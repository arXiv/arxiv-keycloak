#!/bin/sh
. ../.env
export PUBSUB_EMULATOR_HOST=0.0.0.0:$PUBSUB_EMULATOR_PORT
export GOOGLE_CLOUD_PROJECT=$PUBSUB_PROJECT
gcloud pubsub topics publish $GCP_EVENT_TOPIC_ID --message "Hello, PubSub Emulator!" --project=$PUBSUB_PROJECT
