import json
import smtplib
from email.message import EmailMessage
from google.cloud import pubsub_v1

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GCP Pub/Sub configuration
GCP_PROJECT = "arxiv-development"
SUBSCRIPTION_ID = "arxiv-email-queue-sub"

def send_email_via_smtp(email_data: dict):
    try:
        msg = EmailMessage()
        msg["From"] = email_data["mail_from"]
        msg["To"] = email_data["mail_to"]
        msg["Subject"] = email_data["subject"]
        msg["Date"] = email_data["timestamp"]
        msg.set_content(email_data["body"])

        # Add headers
        headers = email_data.get("headers", "")
        for header_line in headers.splitlines():
            if ":" in header_line:
                key, value = header_line.split(":", 1)
                msg[key.strip()] = value.strip()

        # Send email to localhost SMTP server
        with smtplib.SMTP("localhost", 25) as server:
            server.send_message(msg)

        logger.info(f"Email sent to {email_data['mail_to']}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

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

if __name__ == "__main__":
    main()
