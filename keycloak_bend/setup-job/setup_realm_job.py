"""
Cloud Run Job wrapper for Keycloak realm setup.

Fetches realm configuration from Secret Manager or GCS and runs the setup.
"""
import json
import logging
import os
import sys
import time
from typing import Optional

import requests
from google.cloud import secretmanager

# Import the existing setup logic
sys.path.insert(0, '/app')
from setup_arxiv_realm import KeycloakSetup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_keycloak(keycloak_url: str, timeout: int = 600, interval: int = 5) -> bool:
    """
    Wait for Keycloak to be ready by polling the master realm endpoint.

    This mimics the behavior of the shell script:
    until curl -s -o /dev/null -w '%{http_code}' $KC_URL/realms/master > /dev/null;
      do sleep 5; done;

    Args:
        keycloak_url: Base URL of Keycloak service
        timeout: Maximum time to wait in seconds (default: 10 minutes)
        interval: Time to wait between attempts in seconds (default: 5)

    Returns:
        True if Keycloak is ready, False if timeout exceeded
    """
    master_realm_url = f"{keycloak_url.rstrip('/')}/realms/master"
    start_time = time.time()
    attempt = 0

    logger.info(f"Waiting for Keycloak to be ready at {keycloak_url}")
    logger.info(f"Polling {master_realm_url} (timeout: {timeout}s, interval: {interval}s)")

    while True:
        attempt += 1
        elapsed = time.time() - start_time

        if elapsed > timeout:
            logger.error(f"Timeout waiting for Keycloak after {elapsed:.1f} seconds ({attempt} attempts)")
            return False

        try:
            # Try to reach the master realm endpoint
            response = requests.get(master_realm_url, timeout=10, verify=True)

            # Any successful HTTP response means Keycloak is up
            # (even 404 would mean the server is responding)
            if response.status_code < 500:
                logger.info(f"Keycloak is ready! (HTTP {response.status_code} after {elapsed:.1f}s, {attempt} attempts)")
                return True
            else:
                logger.debug(f"Attempt {attempt}: HTTP {response.status_code}, retrying in {interval}s...")

        except requests.exceptions.RequestException as e:
            logger.debug(f"Attempt {attempt}: Connection failed ({type(e).__name__}), retrying in {interval}s...")

        # Wait before next attempt
        time.sleep(interval)


def fetch_realm_config_from_secret_manager(secret_path: str) -> dict:
    """
    Fetch realm configuration JSON from Secret Manager.

    Args:
        secret_path: Full secret path in format
                    projects/PROJECT_ID/secrets/SECRET_ID/versions/VERSION

    Returns:
        Realm configuration as dictionary
    """
    logger.info(f"Fetching realm configuration from Secret Manager: {secret_path}")

    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(name=secret_path)
    realm_json = response.payload.data.decode('UTF-8')

    logger.info("Realm configuration fetched successfully")
    return json.loads(realm_json)


def get_realm_config() -> dict:
    """
    Get realm configuration from environment-specified source.

    Supports:
    - HTTP/HTTPS URL: https://github.com/.../realm.json
    - Secret Manager: secret://projects/PROJECT/secrets/NAME/versions/VERSION
    - Local file (for testing): file:///path/to/realm.json

    Returns:
        Realm configuration dictionary
    """
    source = os.environ.get('REALM_CONFIG_SOURCE', '')

    if not source:
        logger.error("REALM_CONFIG_SOURCE environment variable not set")
        sys.exit(1)

    if source.startswith('https://') or source.startswith('http://'):
        # Fetch from HTTP/HTTPS URL (e.g., GitHub raw)
        logger.info(f"Fetching realm configuration from URL: {source}")
        try:
            response = requests.get(source, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch realm config from URL: {e}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse realm config JSON from URL: {e}")
            sys.exit(1)

    elif source.startswith('secret://'):
        # Remove secret:// prefix and fetch from Secret Manager
        secret_path = source.replace('secret://', '')
        return fetch_realm_config_from_secret_manager(secret_path)

    elif source.startswith('file://'):
        # Local file (for testing)
        file_path = source.replace('file://', '')
        logger.info(f"Reading realm configuration from file: {file_path}")
        with open(file_path, 'r') as f:
            return json.load(f)

    else:
        logger.error(f"Unsupported REALM_CONFIG_SOURCE format: {source}")
        logger.error("Supported formats: https://..., secret://projects/..., file://...")
        sys.exit(1)


def main():
    """Main entry point for Cloud Run Job."""
    logger.info("Starting Keycloak realm setup job")

    # Required environment variables
    keycloak_url = os.environ.get('KC_URL')
    admin_password = os.environ.get('KC_ADMIN_PASSWORD')
    arxiv_user_secret = os.environ.get('ARXIV_USER_SECRET')

    # Optional environment variables
    legacy_auth_token = os.environ.get('LEGACY_AUTH_API_TOKEN', '')
    # Support both URI (from shell script) and LEGACY_AUTH_URI (for consistency)
    legacy_auth_uri = os.environ.get('LEGACY_AUTH_URI', '') or os.environ.get('URI', '')
    realm_name = os.environ.get('REALM_NAME', 'arxiv')
    wait_timeout = int(os.environ.get('KEYCLOAK_WAIT_TIMEOUT', '600'))
    wait_interval = int(os.environ.get('KEYCLOAK_WAIT_INTERVAL', '5'))

    # Validate required variables
    if not keycloak_url:
        logger.error("KC_URL environment variable not set")
        sys.exit(1)

    if not admin_password:
        logger.error("KC_ADMIN_PASSWORD environment variable not set")
        sys.exit(1)

    if not arxiv_user_secret:
        logger.error("ARXIV_USER_SECRET environment variable not set")
        sys.exit(1)

    # Wait for Keycloak to be ready
    logger.info("Checking if Keycloak is ready...")
    if not wait_for_keycloak(keycloak_url, timeout=wait_timeout, interval=wait_interval):
        logger.error("Keycloak did not become ready in time. Exiting.")
        sys.exit(1)

    # Fetch realm configuration
    try:
        realm_config = get_realm_config()
    except Exception as e:
        logger.error(f"Failed to fetch realm configuration: {e}")
        sys.exit(1)

    # Initialize and run Keycloak setup
    logger.info(f"Connecting to Keycloak at {keycloak_url}")
    logger.info(f"Configuring realm: {realm_name}")

    try:
        setup = KeycloakSetup(
            realm=realm_config,
            server_url=keycloak_url,
            user_realm_name="master",
            client_id="admin-cli",
            username="admin",
            password=admin_password,
            realm_name=realm_name,
            verify=True,  # Enable SSL verification in production
            client_secret=arxiv_user_secret,
            legacy_auth_token=legacy_auth_token if legacy_auth_token else None,
            legacy_auth_uri=legacy_auth_uri if legacy_auth_uri else None,
        )

        logger.info("Running Keycloak setup...")
        setup.run()

        logger.info("Keycloak realm setup completed successfully!")

    except Exception as e:
        logger.error(f"Keycloak setup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
