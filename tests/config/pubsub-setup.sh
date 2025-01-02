#!/bin/bash
set -x

PORT=$1
shift

GCP_PROJECT=$1
shift

PUBSUB_TOPIC=$1
shift

PUBSUB_SUBSCRIPTION=$1
shift

export CLOUDSDK_CORE_ACCOUNT="fake-account"
export CLOUDSDK_CORE_PROJECT="${GCP_PROJECT}"

gcloud beta emulators pubsub start --host-port=0.0.0.0:$PORT &
sleep 10

export PUBSUB_EMULATOR_HOST=localhost:$PORT

# Use the emulator directly for gcloud commands
gcloud config configurations create pubsub-emulator-config --quiet || true
gcloud config set auth/disable_credentials true --configuration=pubsub-emulator-config
gcloud config set project "${GCP_PROJECT}" --configuration=pubsub-emulator-config
gcloud config set api_endpoint_overrides/pubsub "http://localhost:${PORT}/" --configuration=pubsub-emulator-config

# Create the topic and subscription
gcloud pubsub topics create "${PUBSUB_TOPIC}" --configuration=pubsub-emulator-config
gcloud pubsub subscriptions create "${PUBSUB_SUBSCRIPTION}" --topic="${PUBSUB_TOPIC}" --configuration=pubsub-emulator-config

# Keep the process running
tail -f /dev/null
