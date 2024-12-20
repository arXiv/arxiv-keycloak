import json
import logging
import os
from typing import Optional

from keycloak import KeycloakAdmin, KeycloakError
import argparse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class KeycloakSetup:
    realm: dict
    admin: KeycloakAdmin

    def __init__(self, *args, **kwargs):
        self.realm = kwargs.pop('realm')
        self.client_secret = kwargs.pop('client_secret')
        self.admin = KeycloakAdmin(*args, **kwargs)


    def create_realm(self):
        realm_name = realm['realm']
        payload = {
            "realm": realm_name,
            "displayName": realm['displayName'],
            "enabled": True  # Enable the realm
        }
        try:
            self.admin.create_realm(payload=payload)
            logger.info(f"Realm '{realm_name}' created successfully.")
        except KeycloakError as e:
            logger.error(f"Error creating realm '{realm_name}': {e}")


    def restore_realm(self):
        realm_name = self.realm['realm']
        realms = {realm['realm']: realm for realm in self.admin.get_realms()}
        if realm_name not in realms:
            self.create_realm()


    def restore_roles(self):
        existing_roles = {role['name']: role for role in self.admin.get_realm_roles()}

        realm_roles = self.realm['roles']['realm']
        # Define Role Data
        for role in realm_roles:
            role_name = role['name']
            if role_name[0].upper() != role_name[0]:
                continue
            if role_name in existing_roles:
                continue
            role_description = role['description']
            self.admin.create_realm_role(
                payload={
                    "name": role_name,
                    "description": role_description
                }
            )

    def restore_scopes(self):
        existing_scopes = {scope['name']: scope for scope in self.admin.get_client_scopes()}
        realm_scopes = self.realm['clientScopes']

        for scope in realm_scopes:
            if scope['name'] in existing_scopes:
                continue

            try:
                # Create the 'openid' scope
                payload = scope.copy()
                del payload['id']
                scope_id = self.admin.create_client_scope(payload=payload, skip_exists=True)
                logger.info(f"Scope '{payload["name"]}' created successfully. {scope_id}")

            except KeycloakError as exc:
                logger.error(f"Error creating {scope['name']}: {exc}")


    def restore_client(self, client_id: str, client_secret: str):
        target: Optional[dict] = next((client for client in self.realm['clients'] if client['clientId'] == client_id), None)
        if not target:
            logger.error(f"Client '{client_id}' not found.")
            return

        payload = target.copy()
        payload['secret'] = client_secret
        del payload['id']
        del payload['attributes']["client.secret.creation.time"]
        del payload['protocolMappers']

        self.admin.create_client(payload=payload, skip_exists=True)


    def run(self):
        self.restore_realm()
        self.restore_roles()
        self.restore_scopes()
        self.restore_client("arxiv-user", self.client_secret)
        self.restore_auth



if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--realm', type=str, default='arxiv')
    parser.add_argument('--server', type=str, default=os.environ.get("KEYCLOAK_SERVER_URL", 'http://localhost:3033'))
    parser.add_argument('--admin-secret', type=str, default='')
    parser.add_argument('--arxiv-user-secret', type=str, default='')

    args = parser.parse_args()
    keycloak_bend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    with open(os.path.expanduser(os.path.join(keycloak_bend, "realms", "arxiv-realm.json"))) as realm_fd:
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
    )
    admin.run()
