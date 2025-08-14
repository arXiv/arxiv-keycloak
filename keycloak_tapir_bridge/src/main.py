"""
keycloak_tapir_bridge subscribes to the audit events from keycloak and updates the tapir db accordingly.
"""
import argparse
import importlib
import signal
import sys
import threading
from typing import Dict, Callable
import inspect
from typing import Any
import asyncio
# from datetime import datetime, timedelta
# from pathlib import Path
from time import sleep, gmtime, strftime as time_strftime
from functools import partial

import httpx
from sqlalchemy import Engine

import json
import os
import logging.handlers
import logging
import logging_json

from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1 import SubscriberClient

from arxiv.auth.legacy.exceptions import NoSuchUser
from concurrent.futures import Future

_event_loop = asyncio.new_event_loop()

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


class JsonFormatter(logging_json.JSONFormatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        return time_strftime("%Y-%m-%dT%H:%M:%S", ct) + ".%03d" % record.msecs + time_strftime("%z", ct)

    pass

RUNNING = True

# logging.basicConfig(level=logging.INFO, format='(%(levelname)s): (%(asctime)s) %(message)s')

LOG_FORMAT_KWARGS = {
    "fields": {
        "timestamp": "asctime",
        "level": "levelname",
    },
    "message_field_name": "message",
    # time.strftime has no %f code "datefmt": "%Y-%m-%dT%H:%M:%S.%fZ%z",
}

def signal_handler(_signal: int, _frame: Any):
    """Graceful shutdown request"""
    global RUNNING
    RUNNING = False # Just a very negative int


# Attach the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

logger = logging.getLogger(__name__)


async def post_keycloak_event_to_aaa(api_url: str, api_token: str, audit_event: dict):
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    url = f"{api_url}"
    logger.debug(f"post_to_keycloak_audit_to_aaa %s", url)
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=audit_event, headers=headers)
        return response.status_code


async def dispatch_audit(data: dict, functions: dict[str, Callable]):
    event_type = data.get("type", "").lower()
    if event_type in ["login", "logout"]:
        resource_type = "authn"
        op = event_type
    else:
        resource_type = data.get("resourceType", "no_resource").lower()
        op = data.get("operationType", "").lower()
    dispatch_name = f"dispatch_{resource_type}_do_{op}"
    dispatch = functions.get(dispatch_name)
    representation = json.loads(data.get("representation", "{}"))
    from arxiv.db import Session
    if dispatch is not None:
        try:
            logger.debug("dispatch %s", dispatch_name)
            with Session() as session:
                dispatch(data, representation, session, logger)
        except NoSuchUser:
            logger.warning("No such user: %s", repr(data))
            pass
        except Exception as _exc:
            raise
    else:
        logger.info("dispatch %s does not exist: %s", dispatch_name, repr(data))



def callback_exception_handler(future):
    try:
        future.result()
    except Exception as e:
        logger.error("Callback thread crashed: %s", str(e), exc_info=True)


def handle_keycloak_event(
    message: Message,
    loop: asyncio.AbstractEventLoop,
    subscription_id: str,
    dispatch_functions: Dict[str, Callable],
    api_url: str,
    api_token: str,
):
    log_extra = {"service": "keycloak-tapir", "subscription": subscription_id}

    try:
        json_str = message.data.decode('utf-8')
    except UnicodeDecodeError:
        logger.error(f"bad data {str(message.message_id)}", extra=log_extra)
        message.nack()
        return

    try:
        data = json.loads(json_str)
    except Exception as exc:
        logger.warning("%s bad(%s): %s", str(exc), message.message_id, json_str, extra=log_extra)
        message.ack()
        return

    async def process_event(msg, functions, url, token, kc_data):
        logger.debug(repr(kc_data))
        try:
            if token and url:
                # This is the way to do
                response_code = await post_keycloak_event_to_aaa(url, token, kc_data)
                if response_code == 200:
                    msg.ack()
                    logger.info("POST[%s](%s): ack %s", url, response_code, kc_data.get('id', '<no-id>'))
                else:
                    msg.nack()
                    logger.info("POST[%s](%s): nack %s", url, response_code, kc_data.get('id', '<no-id>'))
                    sleep(1)
            else:
                logger.warning("Forgot setting AAA URL and secret?")
                # This is deprecated in favor of using the API
                if kc_data.get("realmName") != "arxiv":
                    logger.info("Not for arxiv - ack %s", kc_data.get('id', '<no-id>'))
                    msg.ack()
                    return
                await dispatch_audit(kc_data, functions)
                logger.info("SELF: ack %s", kc_data.get('id', '<no-id>'))
                msg.ack()

        except httpx.ReadTimeout as exc:
            logger.warning("[%s] Communication timeout (%s): %s", str(exc), msg.message_id, repr(kc_data), extra=log_extra)
            msg.nack()
            sleep(1)

        except Exception as gexc:
            logger.warning("[%s] bad(%s): %s", str(gexc), msg.message_id, repr(kc_data), extra=log_extra, exc_info=True)
            msg.nack()
            sleep(1)

    future: Future = asyncio.run_coroutine_threadsafe(
        process_event(message, dispatch_functions, api_url, api_token, data),
        loop
    )
    future.add_done_callback(callback_exception_handler)


def subscribe_keycloak_events(
        project_id: str, subscription_id: str, request_timeout: int, db: Engine,
        dispatch_functions: Dict[str, Callable], api_url, api_token: str
) -> None:
    """
    Create a subscriber client and pull messages from the keycloak events

    Args:
        project_id (str): Google Cloud project ID
        subscription_id (str): ID of the Pub/Sub subscription
        request_timeout: request timeout
        db: SQLAlchemy database engine
    """

    if 'PUBSUB_EMULATOR_HOST' in os.environ:
        subscriber_client = SubscriberClient()
        logger.info("Running against pubsub emulator")
    else:
        from google.auth import default
        creds, project = default()
        subscriber_client = SubscriberClient(credentials=creds)
        logger.info("AUTH: Project, SA: %s, %s", project, creds.signer_email)
        pass

    callback = partial(
        handle_keycloak_event,
        loop=_event_loop,
        subscription_id=subscription_id,
        dispatch_functions=dispatch_functions,
        api_url=api_url,
        api_token=api_token,
    )

    subscription_path = subscriber_client.subscription_path(project_id, subscription_id)
    streaming_pull_future = subscriber_client.subscribe(subscription_path, callback=callback)
    streaming_pull_future.add_done_callback(callback_exception_handler)

    log_extra = {"app": "kc-to-tapir"}
    logger.info("Starting on target %s, path %s", subscriber_client.target, subscription_path, extra=log_extra)
    with subscriber_client:
        try:
            while RUNNING:
                sleep(0.2)
            streaming_pull_future.cancel()  # Trigger the shutdown
            streaming_pull_future.result(timeout=30)  # Block until the shutdown is complete
        except TimeoutError:
            logger.info("Timeout")
            streaming_pull_future.cancel()
        except Exception as e:
            logger.error("Subscribe failed: %s", str(e), exc_info=True, extra=log_extra)
            streaming_pull_future.cancel()
    logger.info("Exiting", extra=log_extra)


def get_dispatch_functions(directory: str) -> Dict[str, Callable]:
    # Dictionary to store dispatch functions
    dispatch_functions = {}

    # Get the list of Python files in the actions directory
    for filename in os.listdir(directory):
        if filename.endswith(".py") and not filename.startswith("__"):
            # Get the module name
            module_name = filename[:-3]

            # Import the module dynamically
            module = importlib.import_module(f"actions.{module_name}")

            # Inspect the module to find functions starting with "dispatch_"
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if name.startswith("dispatch_"):
                    dispatch_functions[name] = func

    return dispatch_functions



if __name__ == "__main__":
    # projects/arxiv-production/subscriptions/webnode-pdf-compilation
    ad = argparse.ArgumentParser(epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ad.add_argument('--project',
                    help='GCP project name. Default is arxiv-production',
                    dest="project", default="arxiv-production")
    ad.add_argument('--subscription',
                    help='Subscription name. Default is the one in production',
                    dest="subscription",
                    default="keycloak-arxiv-events-sub")
    ad.add_argument('--json-log-dir',
                    help='JSON logging directory. The default is correct on the sync-node',
                    default='/var/log/e-prints')
    ad.add_argument('--timeout', help='Web node request timeout',
                    default=10, type=int)
    ad.add_argument('--debug', help='Set logging to debug.',
                    action='store_true')
    ad.add_argument('--api-url', help='API URL', default=os.environ.get('AAA_API_URL')),
    ad.add_argument('--api-token', help='API Token', default=os.environ.get('AAA_API_TOKEN')),
    args = ad.parse_args()

    project_id = args.project

    logger.setLevel(logging.DEBUG)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Logging init
    if args.json_log_dir and os.path.exists(args.json_log_dir):
        json_logHandler = logging.handlers.RotatingFileHandler(os.path.join(args.json_log_dir, "kc-to-tapir.log"),
                                                               maxBytes=4 * 1024 * 1024,
                                                               backupCount=10)
    else:
        json_logHandler = logging.StreamHandler(stream=sys.stdout)

    json_formatter = JsonFormatter(**LOG_FORMAT_KWARGS)
    json_formatter.converter = gmtime

    json_logHandler.setFormatter(json_formatter)
    json_logHandler.setLevel(logging.DEBUG if args.debug else logging.INFO)
    logger.addHandler(json_logHandler)

    # DB init
    from arxiv.config import settings
    from arxiv.db import init as arxiv_db_init, _classic_engine
    arxiv_db_init(settings=settings)

    dispatch_functions = get_dispatch_functions(os.path.join(os.path.dirname(os.path.abspath(__file__)), "actions"))

    threading.Thread(target=start_loop, args=(_event_loop,), daemon=True).start()

    listeners = [
        threading.Thread(target=subscribe_keycloak_events,
                         args=(project_id, args.subscription, args.timeout, _classic_engine,
                               dispatch_functions, args.api_url, args.api_token)),
    ]

    for listener in listeners:
        listener.start()

    for listener in listeners:
        listener.join()

