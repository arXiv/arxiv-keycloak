#!/bin/sh
# extract-react-app.sh - Monitor and extract React UIs from Docker images

DEST_DIR="/output"
STATE_DIR="/tmp/ui-extractor-state"
CHECK_INTERVAL=${CHECK_INTERVAL:-3600}

mkdir -p "$STATE_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
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
    if ! docker pull "$IMAGE" 2>&1 | tee -a /tmp/docker-pull.log; then
        log "ERROR: Failed to pull $IMAGE"
        cat /tmp/docker-pull.log
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

        # Set proper permissions: directories 755, files 644
        find "$DEST_PATH" -type d -exec chmod 755 {} \; 2>/dev/null
        find "$DEST_PATH" -type f -exec chmod 644 {} \; 2>/dev/null
        log "$CONTAINER_NAME: Permissions set (dirs=755, files=644)"
    else
        log "ERROR: Failed to extract files from $SOURCE_PATH"
    fi

    # Cleanup
    docker rm "$TEMP_NAME" >/dev/null 2>&1

    log "$CONTAINER_NAME: Extraction complete"
}

# Main loop
log "=== UI Extractor Service Started ==="
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
        "/usr/share/nginx/html" \
        "user-account"

    log "--- Extraction cycle complete, sleeping ${CHECK_INTERVAL}s ---"
    sleep "$CHECK_INTERVAL"
done
