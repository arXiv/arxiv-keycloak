"""
Account Management DAO to backend UserModel mapping
"""
from __future__ import annotations
import re
import traceback
from datetime import datetime
from enum import Enum
from traceback import TracebackException
from typing import Optional, List, Any
from urllib.parse import urlparse

import httpx
from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient
from arxiv.base import logging
from arxiv.db.models import TapirNickname, TapirUsersPassword, TapirUser, Demographic, Category
from arxiv.auth.legacy.exceptions import RegistrationFailed
from arxiv.auth.legacy import passwords
from fastapi import HTTPException, status
from keycloak import KeycloakAdmin, KeycloakError, KeycloakAuthenticationError, KeycloakOpenID
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session

from .. import datetime_to_epoch
# from ..account import AccountRegistrationModel, AccountRegistrationError, AccountInfoModel

from arxiv_bizlogic.bizmodels.user_model import UserModel, USER_MODEL_DEFAULTS, VetoStatusEnum

logger = logging.getLogger(__name__)



# CAREER_STATUS = ["Unknown", "Staff", "Professor", "Post Doc", "Grad Student", "Other"]

class CAREER_STATUS(str, Enum):
    Unknown = "Unknown"
    Staff = "Staff"
    Professor = "Professor"
    PostDoc = "Post Doc"
    GradStudent = "Grad Student"
    Other = "Other"

CAREER_STATUS_LIST = [CAREER_STATUS.Unknown, CAREER_STATUS.Staff, CAREER_STATUS.Professor, CAREER_STATUS.PostDoc, CAREER_STATUS.GradStudent]

def get_career_status(index: int | None) -> CAREER_STATUS:
    """map an integer to a CAREER_STATUS"""
    if index is None:
        return CAREER_STATUS.Unknown

    if 0 <= index < len(CAREER_STATUS_LIST):
        return CAREER_STATUS_LIST[index]
    return CAREER_STATUS.Unknown  # Default fallback


def get_career_status_index(status: CAREER_STATUS) -> int:
    if status in CAREER_STATUS_LIST:
        return CAREER_STATUS_LIST.index(status)
    return 0


allowed_pattern = re.compile(r"^[A-Za-z0-9_.+#\-=/:;(){}\[\]%^]+$")

def validate_password(pwd: str) -> bool:
    if len(pwd) < 8 or (not "_" in pwd) or not allowed_pattern.match(pwd):
        return False
    return True


class CategoryGroup(str, Enum):
    PHYSICS = "grp_physics"  # Physics
    MATH = "grp_math"        # Mathematics
    CS = "grp_cs"            # Computer Science
    Q_BIO = "grp_q-bio"      # Quantitative Biology
    Q_FIN = "grp_q-fin"      # Quantitative Finance
    STAT = "grp_q-stat"      # Statistics
    ECON = "grp_q-econ"      # Economics
    EESS = "grp_eess"        # Electrical Engineering and Systems Science
    NLIN = "grp_nlin"        # Natual Linguistics
    TEST = "grp_test"        # Test

CategoryGroupToCategoryFlags = {
    "grp_physics": "flag_group_physics",
    "grp_math": "flag_group_math",
    "grp_cs": "flag_group_cs",
    "grp_q-bio": "flag_group_q_bio",
    "grp_q-fin": "flag_group_q_fin",
    "grp_q-stat": "flag_group_stat",
    "grp_q-econ": "flag_group_econ",
    "grp_eess": "flag_group_eess",
    "grp_nlin": "flag_group_nlin",
    "grp_test": "flag_group_test",
}


class CategoryIdModel(BaseModel):
    class Config:
        from_attributes = True
    archive: str
    subject_class: str


class CategoryModel(CategoryIdModel):
    class Config:
        from_attributes = True
    definitive: bool
    active: bool
    category_name: str
    endorse_all: str # Mapped[Literal["y", "n", "d"]] = mapped_column(Enum("y", "n", "d"), nullable=False, server_default=text("'d'"))
    endorse_email: str # Mapped[Literal["y", "n", "d"]] = mapped_column(Enum("y", "n", "d"), nullable=False, server_default=text("'d'"))
    papers_to_endorse: bool # Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    endorsement_domain: Optional[str] # Mapped[Optional[str]] = mapped_column(ForeignKey("arXiv_endorsement_domains.endorsement_domain"), index=True)


class AccountInfoBaseModel(BaseModel):
    username: str  # aka nickname in Tapir
    email: Optional[str] = None
    first_name: str
    last_name: str
    suffix_name: Optional[str] = None
    country: Optional[str] = None
    affiliation: Optional[str] = None
    default_category: Optional[CategoryIdModel] = None
    groups: Optional[List[CategoryGroup]] = None
    url: Optional[str] = None
    joined_date: Optional[int] = None
    oidc_id: Optional[str] = None
    groups: Optional[List[str]] = None
    career_status: Optional[CAREER_STATUS] = None
    tracking_cookie: Optional[str] = None
    veto_status: Optional[VetoStatusEnum] = None

    def to_user_model_data(self, **kwargs) -> dict[str, Any]:
        data = self.model_dump(**kwargs)
        result = data.copy()
        for key, value in data.items():
            match key:
                case "default_category":
                    del result[key]
                    if value:
                        result.update(value)
                    pass

                case "groups":
                    del result[key]
                    if value:
                        value: List[str]
                        # groups = [CategoryGroup(elem) for elem in value]
                        for group in list(CategoryGroup):
                            result[CategoryGroupToCategoryFlags[group.value]] = group.value in value

        if not kwargs.get("exclude_defaults", False):
            for key, value in USER_MODEL_DEFAULTS.items():
                if key not in result:
                    result[key] = value

        if "archive" in result and "subject_class" in result and "original_subject_classes" not in result:
            result["original_subject_classes"] = f'{result["archive"]}.{result["subject_class"]}'

        if "joined_date" in result and isinstance(result["joined_date"], datetime):
            result["joined_date"] = datetime_to_epoch(None, result["joined_date"])

        return result


class AccountInfoModel(AccountInfoBaseModel):
    id: str
    email_verified: Optional[bool] = None
    scopes: Optional[List[str]] = None

    def to_user_model_data(self, **kwargs) -> dict[str, Any]:
        return super().to_user_model_data(**kwargs)


class AccountRegistrationModel(AccountInfoBaseModel):
    password: str
    origin_ip: Optional[str] = None
    origin_host: Optional[str] = None
    token: str
    captcha_value: str
    keycloak_migration: bool = False

    def to_user_model_data(self, **kwargs) -> dict[str, Any]:
        return super().to_user_model_data(**kwargs)


class AccountRegistrationError(BaseModel):
    message: str
    field_name: Optional[str] = None


def register_to_keycloak(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str):
    payload = to_kc_user_profile(account)

    try:
        kc_admin.create_user(payload=payload)
    except KeycloakError as e:
        logger.error("Creating Keycloak user failed.", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e

    kc_set_user_password(kc_admin, account, password)


def migrate_to_keycloak(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str, client_secret: str):
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
        "username": account.username,
        "password": password,
    }

    parsed_url = urlparse(token_url)
    is_local = parsed_url.hostname.lower() in ("127.0.0.1", "localhost", "localhost.arxiv.org")

    with httpx.Client(verify=not is_local) as client:
        response = client.post(token_url, data=payload)
        if response.status_code == 200:
            logger.info("Migration successful")
        else:
            logger.warning(
                "Migration failed. status: %d. Migration is likely to fail", response.status_code,
                extra={
                    "status_code": response.status_code,
                    "client_id": client_id,
                    "username": account.username,
                })

    kc_set_user_password(kc_admin, account, password)
    kc_send_verify_email(kc_admin, account.id)



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
    """
    user = kc_admin.get_user(account_id)
    if force_verify or not user.get("emailVerified", False):
        try:
            kc_admin.send_verify_email(account_id)
        except KeycloakError as e:
            logger.error("Creating Keycloak user failed.", exc_info=e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e


def kc_set_user_password(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str):
    try:
        kc_admin.set_user_password(account.id, password, temporary=False)

    except KeycloakAuthenticationError as e:
        message = "Setting Keycloak user password failed, and kc_admin has the wrong secret"
        logger.error(message, exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message) from e

    except KeycloakError as e:
        logger.error("Setting Keycloak user password failed.", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e


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


def um_to_group_name(group_flag, um: UserModel) -> Optional[str]:
    group_name, flag_name = group_flag
    return group_name if hasattr(um, flag_name) and getattr(um, flag_name) else None



def get_account_info(session: Session, user_id: str) -> Optional[AccountInfoModel]:
    um = UserModel.one_user(session, user_id)
    if um:
        if um.flag_deleted or um.flag_banned:
            return None

        groups = [um_to_group_name(group_flag, um) for group_flag in Demographic.GROUP_FLAGS]

        category: Optional[Category] = session.query(Category).filter(
            and_(
                Category.archive == um.archive,
                Category.subject_class == um.subject_class
            )
        ).one_or_none()

        category_model = CategoryIdModel.model_validate(category) if category else None

        scopes = None
        for flag, value in [
            ("admin", um.flag_edit_users),
            ("root", um.flag_edit_system),
            ("mod", um.flag_is_mod),
            ("tex", um.flag_allow_tex_produced),
            ("can-lock", um.flag_can_lock),
            ]:
            if value:
                if scopes is None:
                    scopes = [flag]
                else:
                    scopes.append(flag)

        account = AccountInfoModel(
            id = str(um.id),
            username = um.username,
            email = um.email,
            email_verified = True if um.flag_email_verified else False,
            scopes = scopes,
            oidc_id = None,
            first_name = um.first_name,
            last_name = um.last_name,
            suffix_name = um.suffix_name,
            country = um.country,
            affiliation = um.affiliation,
            url = um.url,
            default_category = category_model,
            groups = [group for group in groups if group],
            joined_date = um.joined_date,
            career_status = get_career_status(um.type),
            tracking_cookie=um.tracking_cookie,
            veto_status=um.veto_status,
        )
        return account
    return None


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


def register_tapir_account(session: Session, registration: AccountRegistrationModel) -> AccountRegistrationError | TapirUser :
    data = registration.to_user_model_data()
    um = UserModel.to_model(data)

    try:
        tapir_user = UserModel.create_user(session, um)

    except IntegrityError as this_e:
        # If user name or email is dupe, this would catch it and may be able to produce a reasonable error mssage.
        session.rollback()

        tb_exception = traceback.TracebackException.from_exception(this_e)
        messages = []
        cause = tb_exception.__cause__
        if isinstance(cause, TracebackException):
            messages.append(str(cause.exc_type))
            messages.append(str(cause))
        flattened_error = "\n".join(messages)
        message = flattened_error
        match = re.search(r"Duplicate entry '([^']+)' for key '([^']+)'", flattened_error, flags=re.MULTILINE)
        where = None
        if match:
            field = match.group(2)
            where = {"nickname": "User name", "email": "Email"}.get(field, field)
            message = f"'{match.group(1)}' for '{where}' belongs to an existing user."
        return AccountRegistrationError(message=message, field_name=where)

    db_nick = TapirNickname(user_id = tapir_user.user_id,  nickname = um.username, flag_valid = 1, flag_primary = 1)
    session.add(db_nick)

    hashed = passwords.hash_password(registration.password)
    db_pass = TapirUsersPassword(user_id = tapir_user.user_id, password_storage = 2, password_enc = hashed)
    session.add(db_pass)
    session.commit() # The account needs to be commit, so the following account migration works.
    logger.info("Tapir user account created successfully. The user data committed.")
    return tapir_user


def update_tapir_account(session: Session, profile: AccountInfoModel) -> AccountRegistrationError | TapirUser :
    """
    updates TapirUser and arXiv_demographics tables but not username or password
    """
    updates = profile.to_user_model_data(exclude_defaults=True, exclude_unset=True)
    um0 = UserModel.one_user(session, profile.id)
    if um0 is None:
        return AccountRegistrationError(message="The account not found.")
    user = um0.model_dump()
    user.update(updates)
    um1 = UserModel.to_model(user)

    try:
        tapir_user = UserModel.update_user(session, um1)

    except RegistrationFailed as this_e:
        session.rollback()

        tb_exception = traceback.TracebackException.from_exception(this_e)
        messages = []
        cause = tb_exception.__cause__
        if isinstance(cause, TracebackException):
            messages.append(str(cause.exc_type))
            messages.append(str(cause))
        flattened_error = "\n".join(messages)
        message = flattened_error
        match = re.search(r"Duplicate entry '([^']+)' for key '([^']+)'", flattened_error, flags=re.MULTILINE)
        where = None
        if match:
            field = match.group(2)
            where = {"nickname": "User name", "email": "Email"}.get(field, field)
            message = f"'{match.group(1)}' for '{where}' belongs to an existing user."
        return AccountRegistrationError(message=message, field_name=where)

    logger.info("Tapir user account updated successfully.")
    return tapir_user
