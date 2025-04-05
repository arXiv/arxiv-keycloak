import os
from google.cloud import pubsub_v1
import json

def main():
    # Use emulator
    os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:21507"

    project_id = "local-test"
    topic_id = "keycloak-arxiv-events"

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    # Data must be a bytestring

    nop_data = json.dumps({})
    future = publisher.publish(topic_path, nop_data.encode('utf-8'))
    print(f"Published message ID: {future.result()}")

if __name__ == "__main__":
    main()
