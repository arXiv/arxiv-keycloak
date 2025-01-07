#!/bin/bash
TOOLS_DIR=$(dirname "$(realpath "$0")")
BEND_DIR=$(dirname "$SCRIPT_DIR")

pip install python-keycloak requests

until curl -s -o /dev/null -w '%{http_code}' $KC_URL/realms/master > /dev/null;
  do
    sleep 5;
  done;
set -x

# http://legacy-auth-provider is from docker-compose.yaml
python $TOOLS_DIR/setup_arxiv_realm.py --server $KC_URL --admin-secret $KC_ADMIN_PASSWORD --arxiv-user-secret "$ARXIV_USER_SECRET" --legacy-auth-token "$LEGACY_AUTH_API_TOKEN" --legacy-auth-uri "$URI"
