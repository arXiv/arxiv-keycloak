"""
Update arxiv's client secret
"""
import json
import logging
import os
import argparse

from tools.setup_arxiv_realm import KeycloakSetup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def run(admin: KeycloakSetup, client_secret: str):
    # admin.restore_client("arxiv-user", client_secret)
    admin.update_client_secret("arxiv-user-migration", client_secret)


if __name__ == '__main__':
    keycloak_bend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser()

    parser.add_argument('--realm', type=str, default='arxiv')
    parser.add_argument('--source', type=str, default=os.path.expanduser(os.path.join(keycloak_bend, "realms", "foo.json")))
    parser.add_argument('--server', type=str, default=os.environ.get("KEYCLOAK_SERVER_URL", 'http://localhost:3033'))
    parser.add_argument('--admin-secret', type=str, default='')
    parser.add_argument('--arxiv-user-secret', type=str, default='')

    args = parser.parse_args()

    with open(args.source) as realm_fd:
        realm = json.load(realm_fd)

    secret = args.admin_secret
    if not secret:
        with open(os.path.expanduser("~/.arxiv/keycloak-admin-password-dev"), encoding="utf-8") as fd:
            secret = fd.read().strip()

    client_secret = args.arxiv_user_secret
    if not client_secret:
        logger.error("No arxiv-user client secret provided.")
        exit(1)

    admin = KeycloakSetup(
        realm=realm,
        server_url=args.server,
        user_realm_name="master",
        client_id="admin-cli",
        username="admin",
        password=secret,
        realm_name=args.realm,
        verify=False,
        client_secret=client_secret,
        legacy_auth_token="",
        legacy_auth_uri="",
    )
    run(admin, client_secret)
