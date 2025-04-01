import os
import asyncio
from aiosmtpd.controller import Controller
from email.parser import BytesParser
from email.policy import default
from email.utils import parsedate_to_datetime
from google.cloud import pubsub_v1
import json
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Headers to exclude from relay
excluding_headers = set(["subject", "from", "to", "date"])

# GCP Pub/Sub configuration
GCP_PROJECT = os.environ.get("GCP_PROJECT", "arxiv-development")
TOPIC_ID = os.environ.get("TOPIC_ID", "arxiv-email-queue")
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(GCP_PROJECT, TOPIC_ID)

class EmailHandler:
    async def handle_DATA(self, server, session, envelope):
        mail_from = envelope.mail_from
        mail_to = envelope.rcpt_tos

        # Parse email
        email_message = BytesParser(policy=default).parsebytes(envelope.content)
        subject = email_message.get("subject", "(No Subject)")
        timestamp = parsedate_to_datetime(email_message.get("date")).isoformat() if email_message.get("date") else None
        body = email_message.get_body(preferencelist=('plain',)).get_content()
        headers = {key: value for key, value in email_message.items() if key.lower() not in excluding_headers}

        # Construct payload
        payload = {
            "timestamp": str(timestamp),
            "subject": str(subject),
            "headers": repr(headers),
            "mail_from": str(mail_from),
            "mail_to": str(mail_to),
            "body": str(body)
        }

        logger.debug(f"Publishing to Pub/Sub: {payload!r}")

        try:
            message_json = json.dumps(payload)
            message_bytes = message_json.encode("utf-8")
            future = publisher.publish(topic_path, data=message_bytes)
            message_id = future.result()
            logger.info(f"Published message with ID: {message_id}")
        except Exception as e:
            logger.error(f"Failed to publish to Pub/Sub: {e}")

        return b'250 OK'


if __name__ == "__main__":
    smtp_port = int(os.environ.get("SMTP_PORT", 21508))

    handler = EmailHandler()
    controller = Controller(handler, hostname="0.0.0.0", port=smtp_port)
    controller.start()
    logger.info(f"SMTP server running on port {smtp_port}. Press Ctrl+C to stop.")

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
    except Exception as e:
        logger.exception("Unexpected error during shutdown.")

    controller.stop()
