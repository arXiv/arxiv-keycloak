#!/bin/sh
# extract-ui.sh - Monitor and extract React UIs from Docker images

DEST_DIR="/output"
STATE_DIR="/tmp/ui-extractor-state"
CHECK_INTERVAL=${CHECK_INTERVAL:-3600}
GCP_KEY_FILE="/gcp-key.json"

mkdir -p "$STATE_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Initialize GCP authentication and Docker CLI
initialize() {
    log "=== Initializing UI Extractor Service ==="


    # Install gcloud CLI if not present
    if ! command -v gcloud >/dev/null 2>&1; then
        log "Installing gcloud CLI..."
        apk add --no-cache python3 py3-pip curl bash

        # Install gcloud SDK
        curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-458.0.0-linux-x86_64.tar.gz
        tar -xzf google-cloud-sdk-458.0.0-linux-x86_64.tar.gz
        ./google-cloud-sdk/install.sh --quiet --usage-reporting=false --path-update=true
        rm google-cloud-sdk-458.0.0-linux-x86_64.tar.gz

        # Add to PATH
        export PATH=$PATH:/google-cloud-sdk/bin
        log "gcloud CLI installed"
    fi

    # Authenticate with GCP
    if [ -f "$GCP_KEY_FILE" ]; then
        log "Authenticating with GCP..."
        /google-cloud-sdk/bin/gcloud auth activate-service-account --key-file="$GCP_KEY_FILE" --quiet
        /google-cloud-sdk/bin/gcloud auth configure-docker gcr.io --quiet
        log "GCP authentication complete"
    else
        log "WARNING: GCP key file not found at $GCP_KEY_FILE"
    fi


    log "Initialization complete"
}

get_image_digest() {
    local image=$1
    docker inspect --format='{{.Id}}' "$image" 2>/dev/null || echo "none"
}

extract_ui() {
    local IMAGE=$1
    local CONTAINER_NAME=$2
    local SOURCE_PATH=$3
    local DEST_SUBDIR=$4
    local STATE_FILE="$STATE_DIR/${CONTAINER_NAME}.digest"

    log "Checking $CONTAINER_NAME..."

    # Pull latest image
    log "Pulling $IMAGE..."
    if ! docker pull "$IMAGE" >/dev/null 2>&1; then
        log "ERROR: Failed to pull $IMAGE"
        return 1
    fi

    # Get current digest
    CURRENT_DIGEST=$(get_image_digest "$IMAGE")
    PREVIOUS_DIGEST=$(cat "$STATE_FILE" 2>/dev/null || echo "none")

    if [ "$CURRENT_DIGEST" = "$PREVIOUS_DIGEST" ] && [ -d "$DEST_DIR/$DEST_SUBDIR" ]; then
        log "$CONTAINER_NAME: No update needed (digest: ${CURRENT_DIGEST:0:12}...)"
        return 0
    fi

    log "$CONTAINER_NAME: New version detected, extracting..."

    # Create temporary container
    TEMP_NAME="${CONTAINER_NAME}-extract-$$"
    if ! docker create --name "$TEMP_NAME" "$IMAGE" >/dev/null 2>&1; then
        log "ERROR: Failed to create container"
        return 1
    fi

    # Extract files
    DEST_PATH="$DEST_DIR/$DEST_SUBDIR"

    # Remove old files
    if [ -d "$DEST_PATH" ]; then
        rm -rf "$DEST_PATH"
    fi

    # Copy files
    if docker cp "$TEMP_NAME:$SOURCE_PATH" "$DEST_PATH" >/dev/null 2>&1; then
        log "$CONTAINER_NAME: Successfully extracted to $DEST_PATH"
        echo "$CURRENT_DIGEST" > "$STATE_FILE"

        # Set world-readable permissions so nginx can read them
        chmod -R 755 "$DEST_PATH" 2>/dev/null
        log "$CONTAINER_NAME: Permissions set to 755"
    else
        log "ERROR: Failed to extract files from $SOURCE_PATH"
    fi

    # Cleanup
    docker rm "$TEMP_NAME" >/dev/null 2>&1

    log "$CONTAINER_NAME: Extraction complete"
}

# Initialize on first run
initialize

# Main loop
log "Monitoring images for updates every ${CHECK_INTERVAL}s"

while true; do
    log "--- Starting extraction cycle ---"

    # Extract Admin Console UI
    extract_ui \
        "$ADMIN_CONSOLE_IMAGE" \
        "admin-console" \
        "/usr/share/nginx/html/admin-console" \
        "admin-console"

    # Extract Account Portal UI
    extract_ui \
        "$ACCOUNT_PORTAL_IMAGE" \
        "account-portal" \
        "/usr/share/nginx/html/user-account" \
        "user-account"

    log "--- Extraction cycle complete, sleeping ${CHECK_INTERVAL}s ---"
    sleep "$CHECK_INTERVAL"
done
