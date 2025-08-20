import datetime
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
SMTP_SERVER = "mail.arxiv.org"
SMTP_PORT = 25
smtp_user = None
smtp_pass = None


def send_email_via_smtp(email_data: dict):
    sender = email_data.get("mail_from", "nobody@arxiv.org")
    recipient = email_data.get("mail_to", "root@localhost")
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

        # Send email to localhost SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()

            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)

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

if __name__ == "__main__":
    main()
