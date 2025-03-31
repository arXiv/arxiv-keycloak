import os
import asyncio
import requests
from aiosmtpd.controller import Controller
from email.parser import BytesParser
from email.policy import default
from email.utils import parsedate_to_datetime
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

excluding_headers = set(["subject", "from", "to", "date"])

class EmailHandler:
    def __init__(self, rest_api: str):
        self.api = rest_api
        pass

    async def handle_DATA(self, server, session, envelope):
        mail_from = envelope.mail_from
        mail_to = envelope.rcpt_tos

        email_message = BytesParser(policy=default).parsebytes(envelope.content)
        subject = email_message.get("subject", "(No Subject)")
        timestamp = parsedate_to_datetime(email_message.get("date")).isoformat() if email_message.get("date") else None
        body = email_message.get_body(preferencelist=('plain',)).get_content()
        headers = {key: value for key, value in email_message.items() if key.lower() not in excluding_headers}
        payload = {
                    "timestamp": str(timestamp),
                    "subject": str(subject),
                    "headers": repr(headers),
                    "mail_from": str(mail_from),
                    "mail_to": str(mail_to),
                    "body": str(body)
                }
        logger.debug(f"Payload: {payload!r}")
        try:
            response = requests.post(self.api, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email to REST API: {e}")

        return b'250 OK'


if __name__ == "__main__":
    smtp_port = int(os.environ.get("SMTP_PORT", 21508))
    MAIL_API_PORT = int(os.environ.get("MAIL_API_PORT", 21512))

    handler = EmailHandler(os.environ.get("MAILSTORE_API", f"http://localhost:{MAIL_API_PORT}/emails"))
    controller = Controller(handler, hostname="0.0.0.0", port=smtp_port)
    controller.start()
    logger.info("SMTP server running. Press Ctrl+C to stop.")
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("Exiting")
    except Exception as e:
        logger.info("Exiting", exc_info=True)
    controller.stop()
