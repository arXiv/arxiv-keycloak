import json
import logging
import os
import base64
import string
from typing import Optional

from keycloak import KeycloakAdmin, KeycloakError
import argparse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



def to_alnums(num: int) -> str:
    chars = string.ascii_letters + string.digits
    if num == 0:
        return chars[0]
    result = ""
    while num > 0:
        num, remainder = divmod(num, len(chars))
        result = result + chars[remainder]
    return result



class KeycloakSetup:
    realm: dict
    admin: KeycloakAdmin

    def __init__(self, *args, **kwargs):
        self.realm = kwargs.pop('realm')
        self.client_secret = kwargs.pop('client_secret')
        self.legacy_auth_token = kwargs.pop('legacy_auth_token', None)
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
                payload_name = payload.get("name", "unknown payload")
                logger.info(f"Scope '{payload_name}' created successfully. {scope_id}")

            except KeycloakError as exc:
                logger.error(f"Error creating {scope['name']}: {exc}")


    def restore_client(self, client_id: str, client_secret: str):
        existing_clients = {cl['clientId']: cl for cl in self.admin.get_clients()}
        if client_id in existing_clients:
            return

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


    def restore_legacy_auth_provider(self):
        provider_type = "org.keycloak.storage.UserStorageProvider"
        provider_name = "arXiv Legacy Auth Provider"
        provider = next((prov for prov in self.realm['components'][provider_type] if prov['name'] == provider_name), None)
        if not provider:
            logger.error(f"Provider '{provider_name}' not found.")
            exit(1)

        existing_providers = {component['name']: component for component in self.admin.get_components({"type": provider_type})}
        if provider_name in existing_providers:
            logger.info(f"Provider '{provider_name}' already exists.")
            return

        provider['providerType'] = provider_type
        del provider["id"]
        del provider["subComponents"]
        token = self.legacy_auth_token if self.legacy_auth_token else to_alnums(int.from_bytes(os.urandom(25), 'little'))
        provider['config']['API_TOKEN'] = [token]
        try:
            self.admin.create_component(provider)
            logger.info(f"Provider '{provider_name}' created successfully.")
        except KeycloakError as e:
            logger.error(f"Error creating {provider_name}: {e}")


    def run(self):
        self.restore_realm()
        self.restore_roles()
        self.restore_scopes()
        self.restore_client("arxiv-user", self.client_secret)
        self.restore_legacy_auth_provider()



if __name__ == '__main__':
    keycloak_bend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser()

    parser.add_argument('--realm', type=str, default='arxiv')
    parser.add_argument('--source', type=path, default=os.path.expanduser(os.path.join(keycloak_bend, "realms", "arxiv-realm-gcp-dev.json")))
    parser.add_argument('--server', type=str, default=os.environ.get("KEYCLOAK_SERVER_URL", 'http://localhost:3033'))
    parser.add_argument('--admin-secret', type=str, default='')
    parser.add_argument('--arxiv-user-secret', type=str, default='')
    parser.add_argument('--legacy-auth-token', type=str, default='', help="bearer token for legacy auth api")

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
        legacy_auth_token=args.legacy_auth_token,
    )
    admin.run()
