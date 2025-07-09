"""
Account Management DAO to backend UserModel mapping
"""
from __future__ import annotations
import re
import traceback
from datetime import datetime
from enum import Enum
from traceback import TracebackException
from typing import Optional, List, Any, Tuple, Dict
from urllib.parse import urlparse

import httpx
from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient
from arxiv.base import logging
from arxiv.db.models import TapirNickname, TapirUsersPassword, TapirUser, Demographic, Category, OrcidIds, AuthorIds
from arxiv.auth.legacy.exceptions import RegistrationFailed
from arxiv.auth.legacy import passwords
from arxiv_bizlogic.bizmodels.tapir_to_kc_mapping import AuthResponse
from fastapi import HTTPException, status
from keycloak import KeycloakAdmin, KeycloakError, KeycloakAuthenticationError, KeycloakOpenID, KeycloakPostError
from pydantic import BaseModel, EmailStr, field_validator
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

def get_career_status(index: int | None) -> CAREER_STATUS:
    """map an integer to a CAREER_STATUS"""
    if index is None:
        return CAREER_STATUS.Unknown
    csl: List[CAREER_STATUS] = list(CAREER_STATUS)
    if 0 <= index < len(csl):
        return csl[index]
    return CAREER_STATUS.Unknown  # Default fallback


def get_career_status_index(status: CAREER_STATUS) -> int:
    csl = list(CAREER_STATUS)
    if status in csl:
        return csl.index(status)
    return 0


allowed_pattern = re.compile(r"^[A-Za-z0-9_.+#\-=/:;(){}<>\[\]%^]+$")

def validate_password(pwd: str) -> bool:
    if len(pwd) < 8 or (not allowed_pattern.match(pwd)):
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


class AccountIdentifierModel(BaseModel):
    """
    Mapping ot the identifiers that can point to a user
    """
    user_id: Optional[str]
    email: Optional[str]
    username: Optional[str]
    orcid: Optional[str] = None
    author_id: Optional[str] = None


class AccountInfoBaseModel(BaseModel):
    username: str  # aka nickname in Tapir
    email: Optional[EmailStr] = None
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
    career_status: Optional[CAREER_STATUS] = None
    tracking_cookie: Optional[str] = None
    veto_status: Optional[VetoStatusEnum] = None

    @field_validator('first_name', 'last_name', 'suffix_name', 'affiliation', 'oidc_id', 'tracking_cookie')
    @classmethod
    def strip_field_value(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    def to_user_model_data(self, **kwargs) -> dict[str, Any]:
        data = self.model_dump(**kwargs)
        # if "groups" not in data:
        #     data["groups"] = []
        result = data.copy()
        for key, value in data.items():
            match key:
                case "default_category":
                    del result[key]
                    if value:
                        result.update(value)
                    pass

                case "groups":
                    if isinstance(value, list):
                        groups = {group: True for group in value}
                        del result[key]
                        # groups = [CategoryGroup(elem) for elem in value]
                        for group in list(CategoryGroup):
                            result[CategoryGroupToCategoryFlags[group.value]] = group.value in groups
                    else:
                        logger.warning(f"groups is not a list {value!r}")

                case "career_status":
                    del result[key]
                    result["type"] = get_career_status_index(value)

                case "veto_status":
                    del result[key]
                    if value is not None:
                        result[key] = value.value
                    else:
                        result[key] = VetoStatusEnum.ok.value

        if not kwargs.get("exclude_defaults", False):
            for key, value in USER_MODEL_DEFAULTS.items():
                if key not in result:
                    result[key] = value

        if "archive" in result and "subject_class" in result and "original_subject_classes" not in result:
            result["original_subject_classes"] = f'{result["archive"]}.{result["subject_class"]}'

        if "joined_date" in result and isinstance(result["joined_date"], datetime):
            result["joined_date"] = datetime_to_epoch(None, result["joined_date"])
        return result


    @classmethod
    def from_user_model_data(cls, data: Dict[str, Any]) -> "AccountInfoBaseModel":
        values = data.copy()

        if "archive" in values and "subject_class" in values:
            values["default_category"] = CategoryIdModel(
                archive=values.pop("archive"),
                subject_class=values.pop("subject_class")
            )

        groups = []
        for group in CategoryGroup:
            flag = CategoryGroupToCategoryFlags[group.value]
            if values.pop(flag, False):
                groups.append(group)
        values["groups"] = groups or None

        if "type" in values:
            values["career_status"] = get_career_status(values.pop("type"))

        if "veto_status" in values:
            try:
                values["veto_status"] = VetoStatusEnum(values["veto_status"])
            except ValueError:
                logger.warning(f"Invalid veto_status value: {values['veto_status']}")
                values["veto_status"] = VetoStatusEnum.ok

        if isinstance(values.get("joined_date"), int):
            values["joined_date"] = values["joined_date"]
        elif isinstance(values.get("joined_date"), datetime):
            values["joined_date"] = int(values["joined_date"].timestamp())

        return cls(**values)


class AccountInfoModel(AccountInfoBaseModel):
    id: str  # user id
    email_verified: Optional[bool] = None
    scopes: Optional[List[str]] = None
    author_id: Optional[str] = None
    orcid_id: Optional[str] = None
    orcid_authenticated: Optional[bool] = None

    @field_validator('author_id', 'orcid_id')
    @classmethod
    def strip_field_value(cls, value: str | None) -> str | None:
        return value.strip() if value else value

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
    token = kc_login_with_client_credential(kc_admin, account.username, password, client_secret)

    if not token:
        kc_set_user_password(kc_admin, account, password)

    logger.info("Registration successful. Try email verification")
    try:
        kc_send_verify_email(kc_admin, account.id)

    except KeycloakError as e:
        logger.warning("Registration successful, but email verification not working.")


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


def um_to_group_name(group_flag: Tuple[str, str], um: UserModel) -> Optional[str]:
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

        orcid_id: OrcidIds | None = session.query(OrcidIds).filter(OrcidIds.user_id == um.id).one_or_none()
        arxiv_author_id: AuthorIds | None = session.query(AuthorIds).filter(AuthorIds.user_id == um.id).one_or_none()

        account = AccountInfoModel(
            id = str(um.id),
            username = um.username,
            email = um.email,
            oidc_id=None,
            email_verified = True if um.flag_email_verified else False,
            scopes = scopes,
            first_name = um.first_name,
            last_name = um.last_name,
            suffix_name = um.suffix_name,
            country = um.country,
            affiliation = um.affiliation,
            url = um.url,
            default_category = category_model,
            groups = [CategoryGroup(group) for group in groups if group is not None],
            joined_date = datetime_to_epoch(None, um.joined_date),
            career_status = get_career_status(um.type),
            tracking_cookie=um.tracking_cookie,
            veto_status=um.veto_status,
            orcid_id = orcid_id.orcid if orcid_id else None,
            orcid_authenticated = True if orcid_id and orcid_id.authenticated else False,
            author_id = arxiv_author_id.author_id if arxiv_author_id else None,
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
        # If username or email is dupe, this would catch it and may be able to produce a reasonable error mssage.
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

    if tapir_user:
        db_nick = TapirNickname(user_id = tapir_user.user_id,  nickname = um.username, flag_valid = 1, flag_primary = 1)
        session.add(db_nick)

        hashed = passwords.hash_password(registration.password)
        db_pass = TapirUsersPassword(user_id = tapir_user.user_id, password_storage = 2, password_enc = hashed)
        session.add(db_pass)

        session.commit() # The account needs to be committed, so the following account migration works.
        logger.info("Tapir user account created successfully. The user data committed.")
        return tapir_user

    # This should not happen.
    logger.error("Tapir user account is not created.")
    return AccountRegistrationError(message="Tapir user account is not created.", field_name="user_id")


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
        where = "Unknown"
        if match:
            field = match.group(2)
            where = {"nickname": "User name", "email": "Email"}.get(field, field)
            message = f"'{match.group(1)}' for '{where}' belongs to an existing user."
        return AccountRegistrationError(message=message, field_name=where)

    if tapir_user:
        logger.info("Tapir user account updated successfully.")
        return tapir_user

    logger.error("Tapir user account is not updated.")
    return AccountRegistrationError(message="Failed to update user account", field_name="Unknown")


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


def is_user_account_valid(session: Session, user_id: str) -> bool:
    """
    Checks whether a user account is valid by evaluating if the user exists and is not
    marked as banned or deleted.


    :param session: A database session used to query user data.
    :type session: Session
    :param user_id: The unique identifier of the user being checked.
    :type user_id: str
    :return: A boolean indicating whether the user account is valid.
    :rtype: bool
    """
    tu: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if tu:
        return not (tu.flag_banned == 1 or tu.flag_deleted == 1)
    return True
