import base64
import functions_framework
import os
import datetime
import json
import smtplib
from email.message import EmailMessage

from cloudevents.http import CloudEvent
from google.cloud import pubsub_v1
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GCP Pub/Sub configuration
GCP_PROJECT = os.environ.get("GCP_PROJECT", "arxiv-development")

# This is for exteanal
SUBSCRIPTION_ID = os.environ.get("SUBSCRIPTION_ID", "arxiv-email-queue-sub")

MTA_LIST = {
    "arxiv.org": {
        "server": os.environ.get("INTERNAL_MTA", "smtp-relay.gmail.com").strip(),
        "port": 587,
        "user": None,
        "password": None
    },
    "*": {
        "server": os.environ.get("EXTERNAL_MTA", "mail.arxiv.org").strip(),
        "port": 25,
        "user": None,
        "password": None
    }
}


def send_email_via_smtp(email_data: dict):
    recipient = email_data.get("mail_to", "root@localhost")
    destination = recipient.split('@')[-1]
    mta = MTA_LIST.get(destination)
    if mta is None:
        mta = MTA_LIST.get("*")

    if not mta["server"]:
        logger.info(f"Email for {recipient} is subsumed as no MTA server")
        return

    sender = email_data.get("mail_from", "nobody@arxiv.org")
    subject = email_data.get("subject", "No Subject")
    timestamp = email_data.get("timestamp", datetime.datetime.now().isoformat())
    body = email_data.get("body", "?")
    headers = email_data.get("headers", "")

    try:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg["Date"] = timestamp
        msg.set_content(body, "plain")

        # Add headers
        for header_line in headers.splitlines():
            if ":" in header_line:
                key, value = header_line.split(":", 1)
                msg[key.strip()] = value.strip()

        # Send email to SMTP server
        with smtplib.SMTP(mta["server"], mta["port"]) as server:
            server.ehlo()
            if server.has_extn("STARTTLS"):
                server.starttls()
            server.ehlo()

            if mta["user"] and mta["password"]:
                server.login(mta["user"], mta["password"])

            server.sendmail(sender, recipient, msg.as_string())

        logger.info(f"Email sent to {email_data['mail_to']}")

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise

def callback(message: pubsub_v1.subscriber.message.Message):
    logger.info(f"Received message: {message.message_id}")
    try:
        email_data = json.loads(message.data.decode("utf-8"))
        send_email_via_smtp(email_data)
        message.ack()
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        message.nack()

def main():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(GCP_PROJECT, SUBSCRIPTION_ID)

    logger.info(f"Listening to Pub/Sub subscription: {subscription_path}")
    future = subscriber.subscribe(subscription_path, callback=callback)

    try:
        future.result()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        future.cancel()


@functions_framework.cloud_event
def pubsub_to_email(cloud_event: CloudEvent):
    """This reads from a queue, and try to send a email"""
    data = json.loads(base64.b64decode(cloud_event.data["message"]["data"]).decode())
    send_email_via_smtp(data)


if __name__ == "__main__":
    main()
