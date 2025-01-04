#!/bin/bash
TOOLS_DIR=$(dirname "$(realpath "$0")")
BEND_DIR=$(dirname "$SCRIPT_DIR")

pip install python-keycloak requests

until curl -s -o /dev/null -w '%{http_code}' http://keycloak:${KC_PORT}/auth/realms/master > /dev/null;
  do
    sleep 5;
  done;

echo python $TOOLS_DIR/setup_arxiv_realm.py --server $KEYCLOAK_SERVER_URL --admin-secret $KC_ADMIN_PASSWORD --arxiv-user-secret "$ARXIV_USER_SECRET" --legacy-auth-token "${LEGACY_AUTH_TOKEN}"

python $TOOLS_DIR/setup_arxiv_realm.py --server $KEYCLOAK_SERVER_URL --admin-secret $KC_ADMIN_PASSWORD --arxiv-user-secret "$ARXIV_USER_SECRET" --legacy-auth-token "${LEGACY_AUTH_TOKEN}"
