#!/bin/sh

DUMP_DIR=$1
shift

MAX_RETRIES=3
RETRY_DELAY=5
COUNTER=0

while [ $COUNTER -lt $MAX_RETRIES ]; do
  echo "Attempting to load dump directory: $DUMP_DIR"
  myloader \
    -h "$MYSQL_HOST" \
    -P "$MYSQL_TCP_PORT" \
    -u root \
    -p "$MYSQL_ROOT_PASSWORD" \
    -B "$MYSQL_DATABASE" \
    -d "$DUMP_DIR" \
    -o \
    --threads 8 \
    --compress-protocol \
    --overwrite-tables && break

  echo "Failed to load dump, retrying in $RETRY_DELAY seconds..."
  COUNTER=$((COUNTER + 1))
  sleep $RETRY_DELAY
done

if [ $COUNTER -eq $MAX_RETRIES ]; then
  echo "Failed to load dump after $MAX_RETRIES attempts."
  exit 1
else
  echo "Dump loaded successfully."
fi
