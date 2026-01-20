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
export PUBSUB_EMULATOR_HOST=0.0.0.0:$PORT

gcloud beta emulators pubsub start --host-port=$PUBSUB_EMULATOR_HOST --verbosity=debug &
sleep 10

# Use the emulator directly for gcloud commands
gcloud config configurations create pubsub-emulator-config --quiet || true
gcloud config set auth/disable_credentials true --configuration=pubsub-emulator-config
gcloud config set project "${GCP_PROJECT}" --configuration=pubsub-emulator-config
gcloud config set api_endpoint_overrides/pubsub "http://127.0.0.1:${PORT}/" --configuration=pubsub-emulator-config

gcloud config configurations list

# Create the topic and subscription
gcloud pubsub topics create "${PUBSUB_TOPIC}" --configuration=pubsub-emulator-config
gcloud pubsub subscriptions create "${PUBSUB_SUBSCRIPTION}" --topic="${PUBSUB_TOPIC}" --configuration=pubsub-emulator-config

# Keep the process running
tail -f /dev/null
