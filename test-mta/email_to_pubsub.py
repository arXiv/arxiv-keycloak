from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from google.cloud import pubsub_v1
import json
import os
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# GCP Pub/Sub configuration
GCP_PROJECT = "arxiv-development"
TOPIC_ID = "arxiv-email-queue"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(GCP_PROJECT, TOPIC_ID)

# FastAPI app
app = FastAPI(debug=True, description="Email relay to Pub/Sub")

# Pydantic model for incoming emails
class EmailBase(BaseModel):
    timestamp: str
    subject: str
    headers: str
    mail_from: str
    mail_to: str
    body: str


@app.post("/emails/", response_model=dict)
def create_email(email: EmailBase):
    """
    Publish an email to GCP Pub/Sub.
    """
    try:
        # Convert to JSON
        email_dict = email.dict()
        message_json = json.dumps(email_dict)
        message_bytes = message_json.encode("utf-8")

        # Publish to Pub/Sub
        future = publisher.publish(topic_path, data=message_bytes)
        message_id = future.result()
        logger.debug(f"Published message to {topic_path}: {message_json}")

        return {"message": "Email published to Pub/Sub", "message_id": message_id}
    except Exception as e:
        logger.error(f"Failed to publish email: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish email to Pub/Sub")
