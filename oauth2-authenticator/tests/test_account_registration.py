import os
import unittest

from keycloak import KeycloakAdmin

from arxiv_oauth2.biz.account_biz import register_arxiv_account


class TestKeycloakRegistration(unittest.TestCase):
    def setUp(self):
        keycloak_admin_secret = os.environ['KEYCLOAK_ADMIN_SECRET']
        KEYCLOAK_SERVER_URL = os.environ['KEYCLOAK_SERVER_URL']
        realm_name = 'arxiv'

        self.keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_SERVER_URL,
            user_realm_name="master",
            client_id="admin-cli",
            username="admin",
            password=keycloak_admin_secret,
            realm_name=realm_name,
            verify=False,
        )

    def test_account_registration(self):
        client_secret = os.environ['ARXIV_USER_SECRET']

        maybe_tapir_user = register_arxiv_account(kc_admin, client_secret, session, registration)
        if isinstance(maybe_tapir_user, TapirUser):
            result = get_account_info(session, str(maybe_tapir_user.user_id))
        else:
            result = maybe_tapir_user

        if isinstance(result, AccountRegistrationError):
            response.status_code = status.HTTP_404_NOT_FOUND

        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
