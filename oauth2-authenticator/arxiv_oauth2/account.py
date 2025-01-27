"""Account management,

"""
from typing import Optional, List

import httpx
from arxiv.auth.domain import UserFullName, UserProfile, OTHER
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session
from pydantic import BaseModel
from keycloak import KeycloakAdmin, KeycloakError

from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.db.models import TapirUser, Demographic, Category, TapirNickname
from arxiv.auth import domain
from arxiv.auth.legacy.exceptions import RegistrationFailed
from arxiv.auth.legacy import accounts

from . import get_current_user_or_none, get_db, get_keycloak_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])

class AccountInfoBaseModel(BaseModel):
    username: str  # aka nickname in Tapir
    email: str
    first_name: str
    last_name: str
    suffix_name: Optional[str]
    country: Optional[str]
    affiliation: Optional[str]
    groups: Optional[List[str]]
    url: Optional[str]
    joined_date: Optional[int]
    oidc_id: Optional[str]

class AccountInfoModel(AccountInfoBaseModel):
    id: str

class AccountRegistrationModel(AccountInfoBaseModel):
    password: str
    origin_ip: str
    origin_host: str
    keycloak_migration: bool = False


def to_group_name(group_flag, demographic: Demographic) -> Optional[str]:
    group_name, flag_name = group_flag
    return group_name if hasattr(demographic, flag_name) and getattr(demographic, flag_name) else None


def get_account_info(session: Session, user_id: str) -> Optional[AccountInfoModel]:
    user_data: (TapirUser, TapirNickname, Demographic) = session.query(TapirUser, TapirNickname, Demographic) \
        .join(TapirNickname).join(Demographic) \
        .filter(TapirUser.user_id == user_id) \
        .first()

    if user_data:
        tapir_user, tapir_nickname, demographic = user_data

        groups = [to_group_name(group_flag, demographic) for group_flag in Demographic.GROUP_FLAGS]

        category: Optional[Category] = session.query(Category).filter(
            and_(
                Category.archive == demographic.archive,
                Category.subject_class == demographic.subject_class
            )
        ).one_or_none()
        account = AccountInfoModel(
            id = str(tapir_user.user_id),
            username = tapir_nickname.nickname,
            email = tapir_user.email,
            oidc_id = None,
            first_name = tapir_user.first_name,
            last_name = tapir_user.last_name,
            suffix_name = tapir_user.suffix_name,
            country = demographic.country,
            affiliation = demographic.affiliation,
            url = demographic.url,
            category = category.category_name if category else None,
            groups = [group for group in groups if group],
            joined_date = tapir_user.joined_date,
        )
        return account
    return None


@router.get('/current/info')
async def info(current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
               session: Session = Depends(get_db)
          ) -> AccountInfoModel:
    """
    Hit the db and get user info
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    account = get_account_info(session, current_user.user_id)
    if account:
        return account
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post('/register')
async def register(
        registration: AccountRegistrationModel,
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
        ) -> AccountInfoModel:
    """
    Create a new user
    """

    if registration.keycloak_migration:
        data: Optional[TapirNickname] = session.query(TapirNickname).filter(TapirNickname.nickname == registration.username).one_or_none()
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        account = get_account_info(session, str(data.user_id))
        # Rather than creating user, let the legacy user migration create the account.
        _migrate_to_keycloak(kc_admin, account, registration.password)

    else:
        full_name = UserFullName(forename=registration.first_name, surname=registration.last_name, suffix=registration.suffix_name)

        user_profile = UserProfile(
            affiliation=registration.affiliation,
            country=registration.country,
            rank=OTHER[0],
            submission_groups=[]
        )

        user = domain.User(
            username=registration.username,
            email=registration.email,
            name=full_name,
            profile=user_profile,
        )
        try:
            user, auth = accounts.register(user, registration.password, registration.origin_ip, registration.origin_host)
        except RegistrationFailed as e:
            msg = 'Registration failed'
            raise RegistrationFailed(msg) from e
        logger.info("Tapir user account created successfully. Next is Keycloak.")
        account = get_account_info(session, user.user_id)
        # _register_to_keycloak(kc_admin, account)
        _migrate_to_keycloak(kc_admin, account, registration.password)

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    logger.info("User account created successfully")
    return account


def _set_user_password(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str):
    try:
        kc_admin.set_user_password(account.id, password, temporary=False)
    except KeycloakError as e:
        logger.error("Setting Keycloak user password failed.", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e


def _migrate_to_keycloak(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str):
    # Configuration
    keycloak_url = kc_admin.connection.server_url
    realm = kc_admin.connection.realm_name
    client_id = "arxiv-user-migration"

    # Token request to simulate login
    token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
    payload = {
        "client_id": client_id,
        "client_secret": kc_admin.connection.password,
        "grant_type": "password",
        "username": account.username,
        "password": password,
    }

    with httpx.Client() as client:
        response = client.post(token_url, data=payload)
        if response.status_code == 200:
            logger.info("Migration successful")
        else:
            logger.warning("Migration failed")

    _set_user_password(kc_admin, account, password)
    _send_verify_email(kc_admin, account)


def _register_to_keycloak(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str):
    payload = {
        "attributes": {},
        "email": account.email,
        "emailVerified": False,
        "firstName": account.first_name,
        "id": str(account.id),
        "lastName": account.last_name,
        "username": account.username,
        #
        "createdTimestamp": account.joined_date,
    }

    try:
        kc_admin.create_user(payload=payload)
    except KeycloakError as e:
        logger.error("Creating Keycloak user failed.", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e

    _set_user_password(kc_admin, account, password)


def _send_verify_email(kc_admin: KeycloakAdmin, account: AccountInfoModel, force_verify: bool = False):
    """
    """
    user = kc_admin.get_user(account.id)
    if force_verify or not user.get("emailVerified", False):
        try:
            kc_admin.send_verify_email(account.id)
        except KeycloakError as e:
            logger.error("Creating Keycloak user failed.", exc_info=e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e
