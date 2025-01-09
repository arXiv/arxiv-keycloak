import pytest
import os
import json
from google.cloud import pubsub_v1
from google.auth.credentials import AnonymousCredentials
from . import ROOT_DIR
from dotenv import load_dotenv, dotenv_values


# Replace these with your setup
TOPIC_ID = "your-topic-id"

# Publish the message

@pytest.fixture(scope="module")
def localenv() -> dict:
    load_dotenv(os.path.join(ROOT_DIR, ".env"))
    yield dotenv_values()


def publish_message(localenv: dict, message: dict):
    # Set environment variable for the emulator
    os.environ["PUBSUB_EMULATOR_HOST"] = f"localhost:{localenv['PUBSUB_EMULATOR_PORT']}"  # Replace with your emulator host and port

    project_id = localenv['GCP_PROJECT']
    topic_id = localenv['GCP_EVENT_TOPIC_ID']

    publisher = pubsub_v1.PublisherClient(credentials=AnonymousCredentials())
    topic_path = publisher.topic_path(topic=topic_id, project=project_id)

    try:
        # Publish the message
        future = publisher.publish(topic_path, json.dumps(message).encode("utf-8"))
        print(f"Published message ID: {future.result()}")
    except Exception as e:
        print(f"Failed to publish message: {e}")


def test_post_event(localenv: dict):
    publish_message(localenv, {"action": "test"})
    payload = {
        "id": "1e2abec5-bf62-42b1-a000-8773cf177fab",
        "time": 1727796557187,
        "realmId": "e9b31419-5843-4014-9bd1-f05a2df3b96b",
        "realmName": "arxiv",
        "authDetails": {
            "realmId": "e34fe449-a841-4c0c-887d-a123a565d315",
            "realmName": "master",
            "clientId": "350cacca-500f-41a5-a1a2-ab57a0df45b4",
            "userId": "84e2038c-3726-463d-a131-0d09c08c0829",
            "ipAddress": "172.17.0.1"
        },
        "resourceType": "REALM_ROLE_MAPPING",
        "operationType": "DELETE",
        "resourcePath": "users/28396986-0c90-42be-b39b-73f4714debaf/role-mappings/realm",
        "representation": "[{\"id\":\"e6350ae5-2083-46ae-bed8-ba72e3c9dfcf\",\"name\":\"Test Role\",\"composite\":false}]",
        "resourceTypeAsString": "REALM_ROLE_MAPPING"
    }
    publish_message(localenv, payload)

