"""
Account Management DAO to backend UserModel mapping
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

import httpx
from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient
from arxiv.base import logging
from arxiv.db.models import TapirUser
from arxiv_bizlogic.bizmodels.tapir_to_kc_mapping import AuthResponse
from fastapi import HTTPException, status
from keycloak import KeycloakAdmin, KeycloakError, KeycloakAuthenticationError, KeycloakOpenID, KeycloakPostError, \
    KeycloakPutError

from sqlalchemy.orm import Session


from arxiv_bizlogic.user_account_models import (
    CAREER_STATUS, get_career_status, get_career_status_index, CategoryGroup,
    CategoryGroupToCategoryFlags, CategoryIdModel, CategoryModel,
    AccountIdentifierModel, AccountUserNameBaseModel, AccountInfoBaseModel,
    AccountInfoModel, AccountRegistrationModel, AccountRegistrationError,
    um_to_group_name, get_account_info, update_tapir_account, register_tapir_account,
    is_user_account_valid
)

logger = logging.getLogger(__name__)


def register_to_keycloak(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str):
    payload = to_kc_user_profile(account)

    try:
        kc_admin.create_user(payload=payload)
    except KeycloakError as e:
        logger.error("Creating Keycloak user failed.", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e

    kc_set_user_password(kc_admin, account, password)


def kc_login_with_client_credential(kc_admin: KeycloakAdmin, username: str, password: str,
                                    client_secret: str) -> Optional[dict]:
    # Configuration
    keycloak_url = kc_admin.connection.server_url
    realm = kc_admin.connection.realm_name
    client_id = "arxiv-user-migration"
    client_secret = client_secret

    # Token request to simulate login
    token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "password",
        "username": username,
        "password": password,
    }

    parsed_url = urlparse(token_url)
    is_local = parsed_url.hostname.lower() in ("127.0.0.1", "localhost", "localhost.arxiv.org") if parsed_url.hostname is not None else False

    logger.info(f"Logging in local {str(is_local)} {token_url} to Keycloak account {username}")

    with httpx.Client(verify=not is_local) as client:
        response = client.post(token_url, data=payload)
        if response.status_code == 200:
            logger.info(f"Success logging in {username}")
            return response.json()
        logger.warning(f"Failed logging in {username} status_code={response.status_code}")
    return None


def migrate_to_keycloak(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str, client_secret: str):
    # Configuration
    if account.username is None:
        raise ValueError("Account username is None")

    token = kc_login_with_client_credential(kc_admin, account.username, password, client_secret)

    if not token:
        kc_set_user_password(kc_admin, account, password)

    logger.info("Registration successful. Try email verification")
    try:
        kc_send_verify_email(kc_admin, account.id)

    except KeycloakPutError:
        logger.warning("Registration successful, KeycloakPutError - but email verification not working.")
        pass

    except KeycloakError as e:
        logger.warning("Registration successful, KeycloakError error.", exc_info=e)
        pass

    except Exception as e:
        logger.error("Registration success. Some error", exc_info=e)
        pass


def to_kc_user_profile(account: AccountInfoModel, email_verified: bool = False, attributes: dict = {}) -> dict:
    """
    https://www.keycloak.org/docs-api/latest/rest-api/index.html#UserProfileMetadata

Name 	Type 	Format

id        optional String
username  optional String
firstName optional String
lastName  optional String
email     optional String
emailVerified optional Boolean
    """
    return {
        "attributes": attributes,
        "email": account.email,
        "emailVerified": email_verified,
        "firstName": account.first_name,
        "id": str(account.id),
        "lastName": account.last_name,
        "username": account.username,
        #
        "createdTimestamp": account.joined_date,
    }


def kc_send_verify_email(kc_admin: KeycloakAdmin, account_id: str, force_verify: bool = False):
    """
    This may raise KeycloakError.
    """
    user = kc_admin.get_user(account_id)
    if force_verify or not user.get("emailVerified", False):
        kc_admin.send_verify_email(account_id)


def kc_set_user_password(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str):
    try:
        kc_admin.set_user_password(account.id, password, temporary=False)

    except KeycloakAuthenticationError as e:
        message = "Setting Keycloak user password failed, and kc_admin has the wrong secret"
        logger.error(message, exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message) from e

    except KeycloakError as kce:
        logger.error("Setting Keycloak user password failed. " + str(kce), exc_info=kce)
        if kce.response_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=kce.error_message) from kce
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=kce.error_message) from kce


def kc_check_old_password(kc_admin: KeycloakAdmin, idp: ArxivOidcIdpClient,
                          username: str, old_password: str) -> bool:
    """Check if the given old password is correct. However, this requires the direct access (username/password)
    grant and thus avoid.
    """
    keycloak_openid = KeycloakOpenID(
        server_url=kc_admin.connection.server_url,
        client_id=idp.client_id,
        realm_name=idp.realm,
        client_secret_key=idp.client_secret,
        verify=idp._ssl_cert_verify,
    )

    try:
        keycloak_openid.token(username, old_password)
        return True
    except KeycloakAuthenticationError:
        return False


async def kc_validate_access_token(kc_admin: KeycloakAdmin, idp: ArxivOidcIdpClient, access_token: str) -> bool:
    """Validate an access token using Keycloak's introspection endpoint."""
    introspect_url = f"{kc_admin.connection.server_url}/realms/{idp.realm}/protocol/openid-connect/token/introspect"
    data = {
        "token": access_token,
        "client_id": idp.client_id,
        "client_secret": idp.client_secret,
    }

    async with httpx.AsyncClient(verify=idp._ssl_cert_verify) as client:
        response = await client.post(introspect_url, data=data)

    if response.status_code == 200:
        token_info = response.json()
        return token_info.get("active", False)  # 'active' tells whether the token is valid

    return False


def register_arxiv_account(kc_admin: KeycloakAdmin, client_secret: str,
                           session: Session, registration: AccountRegistrationModel) -> AccountRegistrationError | TapirUser :
    result = register_tapir_account(session, registration)

    if isinstance(result, TapirUser):
        logger.info("Tapir user account created successfully. Next is Keycloak.")
        tapir_user = result
        account = get_account_info(session, str(tapir_user.user_id))
        if not account:
            return AccountRegistrationError(message="The account not found.")
        logger.info("Registering to Keycloak id = %s", account.id)
        migrate_to_keycloak(kc_admin, account, registration.password, client_secret)

    return result


def create_kc_account(kc_admin: KeycloakAdmin, user: AuthResponse, exist_ok: bool=True) -> None:
    """
    ** THIS DOES NOT WORK IF THERE IS A TAPIR USER **

    The reason is that, it hits the legacy auth provider and finds the username.
    POST always ends with 409/conflict because of this. IOW, you have to migrate user using legacy auth provider.

    Code is here to let you know that this does not work. OTOH, if there is no tapir user, this would work.

    Create a new KC user account from auth response

    https://www.keycloak.org/docs-api/latest/rest-api/index.html#UserRepresentation

    """
    try:
        kc_admin.create_user({
            "id": user.id,
            "username": user.username,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "email": user.email,
            "emailVerified": user.emailVerified,
            "enabled": True,
            "credentials": [],
            "realmRoles": user.roles,
            "groups": user.groups,
            "attributes": user.attributes  # To have the attributes, make sure the unmanaged user profile is enabled
        }, exist_ok=exist_ok)

    except KeycloakPostError as exc:
        if exc.response_code == status.HTTP_409_CONFLICT:
            if exist_ok:
                return
        raise exc
