"""Account management,

"""
import re
import traceback
from traceback import TracebackException
from typing import Optional, List

import httpx
# from PIL.EpsImagePlugin import field
from arxiv.auth.domain import UserFullName, UserProfile, OTHER
from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient
from fastapi import APIRouter, Depends, status, HTTPException, Request
# from mypyc.irbuild.expression import transform_bytes_expr
from sqlalchemy import and_
from sqlalchemy.orm import Session
from enum import Enum
from pydantic import BaseModel
from keycloak import KeycloakAdmin, KeycloakError, KeycloakAuthenticationError, KeycloakOpenID

from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.db.models import TapirUser, Demographic, Category, TapirNickname, TapirUsersPassword
from arxiv.db import Session as BaseDbSession
from arxiv.auth import domain
from arxiv.auth.legacy.exceptions import RegistrationFailed
from arxiv.auth.legacy import accounts, passwords

from . import get_current_user_or_none, get_db, get_keycloak_admin, stateless_captcha, \
    get_client_host, sha256_base64_encode, get_current_user_access_token  # , get_client_host
# from . import stateless_captcha
from .captcha import CaptchaTokenReplyModel, get_captcha_token
from .stateless_captcha import InvalidCaptchaToken, InvalidCaptchaValue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])


# arxiv-submit/lib/arXiv/Controller/Admin/User.pm

# CAREER_STATUS = ["Unknown", "Staff", "Professor", "Post Doc", "Grad Student", "Other"]

class CAREER_STATUS(str, Enum):
    Unknown = "Unknown"
    Staff = "Staff"
    Professor = "Professor"
    PostDoc = "Post Doc"
    GradStudent = "Grad Student"
    Other = "Other"

CAREER_STATUS_LIST = [CAREER_STATUS.Unknown, CAREER_STATUS.Staff, CAREER_STATUS.Professor, CAREER_STATUS.PostDoc, CAREER_STATUS.GradStudent]

def get_career_status(index: int) -> CAREER_STATUS:
    """map an integer to a CAREER_STATUS"""
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
    email: Optional[str]
    first_name: str
    last_name: str
    suffix_name: Optional[str]
    country: Optional[str]
    affiliation: Optional[str]
    default_category: Optional[CategoryIdModel]
    groups: Optional[List[CategoryGroup]]
    url: Optional[str]
    joined_date: Optional[int]
    oidc_id: Optional[str]
    groups: Optional[List[str]]
    career_status: Optional[CAREER_STATUS]


class AccountInfoModel(AccountInfoBaseModel):
    id: str
    email_verified: Optional[bool]
    scopes: Optional[List[str]]


class AccountRegistrationModel(AccountInfoBaseModel):
    password: str
    origin_ip: Optional[str]
    origin_host: Optional[str]
    token: str
    captcha_value: str
    keycloak_migration: bool = False


class AccountRegistrationError(BaseModel):
    message: str
    field_name: Optional[str] = None


def to_group_name(group_flag, demographic: Demographic) -> Optional[str]:
    group_name, flag_name = group_flag
    return group_name if hasattr(demographic, flag_name) and getattr(demographic, flag_name) else None


def get_account_info(session: Session, user_id: str) -> Optional[AccountInfoModel]:
    user_data: (TapirUser, TapirNickname, Demographic) = session.query(TapirUser, TapirNickname, Demographic) \
        .join(TapirNickname).join(Demographic) \
        .filter(TapirUser.user_id == user_id) \
        .first()

    if user_data:
        tapir_user: TapirUser
        tapir_nickname: TapirNickname
        demographic: Demographic
        tapir_user, tapir_nickname, demographic = user_data

        groups = [to_group_name(group_flag, demographic) for group_flag in Demographic.GROUP_FLAGS]

        category: Optional[Category] = session.query(Category).filter(
            and_(
                Category.archive == demographic.archive,
                Category.subject_class == demographic.subject_class
            )
        ).one_or_none()

        category_model = CategoryIdModel.model_validate(category) if category else None

        account = AccountInfoModel(
            id = str(tapir_user.user_id),
            username = tapir_nickname.nickname,
            email = tapir_user.email,
            email_verified = True if tapir_user.flag_email_verified else False,
            scopes = None,
            oidc_id = None,
            first_name = tapir_user.first_name,
            last_name = tapir_user.last_name,
            suffix_name = tapir_user.suffix_name,
            country = demographic.country,
            affiliation = demographic.affiliation,
            url = demographic.url,
            default_category = category_model,
            groups = [group for group in groups if group],
            joined_date = tapir_user.joined_date,
            career_status = get_career_status(demographic.type),
        )
        return account
    return None


def reply_account_info(session: Session, id: str) -> AccountInfoModel:
    account = get_account_info(session, id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return account


@router.get('/current', description="")
async def get_current_user_info(current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
               session: Session = Depends(get_db)
          ) -> AccountInfoModel:
    """
    Hit the db and get user info
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return reply_account_info(session, current_user.user_id)


@router.get('/profile/{user_id:str}')
async def get_user_profile(user_id: str,
               current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
               session: Session = Depends(get_db)
          ) -> AccountInfoModel:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    ok = current_user.is_admin or current_user.is_admin or current_user.user_id == user_id
    if not ok:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return reply_account_info(session, user_id)

#
# Profile update and registering user is VERY similar. It is essentially upsert. At some point, I should think
# about refactor these two.
@router.put('/profile/', description="Update the user account profile for both Keycloak and user in db")
async def update_account_profile(
    data: AccountInfoModel,
    current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
    session: Session = Depends(get_db),
    kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
) -> AccountInfoModel:
    """
    Update the profile name of a user.
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_id = data.id
    user = session.get(TapirUser, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    demographic = session.query(Demographic).filter(Demographic.user_id == user_id).one_or_none()

    # Authorization check
    if not (current_user.is_admin or current_user.user_id == user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    user.first_name = data.first_name
    user.last_name = data.last_name
    if data.suffix_name:
        user.suffix_name = data.suffix_name

    # email verified is unchanged when the email is unchanged. If changed, reset
    email_verified = data.email_verified
    if email_verified is None:
        if data.email and user.email != data.email:
            email_verified = False
            user.email_verified = False
            pass
        pass
    else:
        user.email_verified = email_verified

    # At some point, I should get off using kc_admin and use the access token to do the update?
    # If this is done by admin, I still need to use the kc_admin.
    try:
        kc_admin.update_user(data.id, to_kc_user_profile(data, email_verified=email_verified))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    session.add(user)

    if demographic:
        demographic.affiliation = data.affiliation
        demographic.country = data.country
        demographic.url = data.url
        demographic.type = get_career_status_index(data.career_status)
        if data.default_category:
            demographic.archive = data.default_category.archive
            demographic.subject_class = data.default_category.subject_class

        in_group_count = 0
        attr_names = {gr[0]: gr[1] for gr in Demographic.GROUP_FLAGS}

        for group in CategoryGroup:
            if group.value not in attr_names:
                continue
            attr_name = attr_names.get(group.value)
            on_off = 1 if group.value.lower() in data.groups else 0

            if attr_name and hasattr(demographic, attr_name):
                setattr(demographic, attr_name, on_off)
                in_group_count += on_off

        if in_group_count == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        session.add(demographic)

    session.commit()

    return reply_account_info(session, user_id)


# See profile update comment.
@router.post('/register/',
             response_model=AccountInfoModel,
             status_code=status.HTTP_201_CREATED,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": AccountRegistrationError, "description": "Invalid registration data"},
                 status.HTTP_404_NOT_FOUND: {"model": AccountRegistrationError, "description": "User not found"},
             }
             )
async def register_account(
        request: Request,
        registration: AccountRegistrationModel,
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
        ) -> HTTPException | AccountInfoModel:
    """
    Create a new user
    """
    captcha_secret = request.app.extra['CAPTCHA_SECRET']
    host = get_client_host(request)

    # Check the captcha value against the captcha token.
    try:
        stateless_captcha.check(registration.token, registration.captcha_value, captcha_secret, host)

    except InvalidCaptchaToken:
        logger.warning(f"Registration: captcha token is invalid {registration.token!r} {host!r}")
        detail = AccountRegistrationError(message="Captcha token is invalid. Restart the registration")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail.model_dump())

    except InvalidCaptchaValue:
        logger.info(f"Registration: wrong captcha value {registration.token!r} {host!r} {registration.captcha_value!r}")
        detail = AccountRegistrationError(message="Captcha answer is incorrect.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail.model_dump())

    if not validate_password(registration.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is invalid")

    client_secret = request.app.extra['ARXIV_USER_SECRET']

    if registration.keycloak_migration:
        data: Optional[TapirNickname] = session.query(TapirNickname).filter(TapirNickname.nickname == registration.username).one_or_none()
        if not data:
            error_response = AccountRegistrationError(message="Username is not found", field_name="username")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_response.model_dump())
        account = get_account_info(session, str(data.user_id))
        # Rather than creating user, let the legacy user migration create the account.
        _migrate_to_keycloak(kc_admin, account, registration.password, client_secret)

    else:
        full_name = UserFullName(forename=registration.first_name, surname=registration.last_name, suffix=registration.suffix_name)

        user_profile = UserProfile(
            affiliation=registration.affiliation,
            country=registration.country,
            rank=OTHER[0],
            submission_groups=[]
        )

        if not registration.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")

        user = domain.User(
            username=registration.username,
            email=registration.email,
            name=full_name,
            profile=user_profile,
        )

        # Purge the base's db session
        try:
            BaseDbSession.reset()
        except:
            pass

        try:
            user, auth = accounts.register(user, registration.password, registration.origin_ip, registration.origin_host)
        except RegistrationFailed as this_e:
            # PITA - this is the only place I have to use arxiv base's db session
            BaseDbSession.rollback()

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
            error_response = AccountRegistrationError(message=message, field_name=where)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_response.model_dump())
        logger.info("Tapir user account created successfully. Next is Keycloak.")
        account = get_account_info(session, user.user_id)
        # _register_to_keycloak(kc_admin, account)
        _migrate_to_keycloak(kc_admin, account, registration.password, client_secret)

    if not account:
        error_response = AccountRegistrationError(message="The account not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_response.model_dump())

    logger.info("User account created successfully")
    return account


@router.get("/register/")
def get_register(request: Request) -> CaptchaTokenReplyModel:
    return get_captcha_token(request)


def _set_user_password(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str):
    try:
        kc_admin.set_user_password(account.id, password, temporary=False)

    except KeycloakAuthenticationError as e:
        message = "Setting Keycloak user password failed, and kc_admin has the wrong secret"
        logger.error(message, exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message) from e

    except KeycloakError as e:
        logger.error("Setting Keycloak user password failed.", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e


def _migrate_to_keycloak(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str, client_secret: str):
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

    with httpx.Client() as client:
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

    _set_user_password(kc_admin, account, password)
    _send_verify_email(kc_admin, account.id)


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


def _register_to_keycloak(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str):
    payload = to_kc_user_profile(account)

    try:
        kc_admin.create_user(payload=payload)
    except KeycloakError as e:
        logger.error("Creating Keycloak user failed.", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e

    _set_user_password(kc_admin, account, password)


def _send_verify_email(kc_admin: KeycloakAdmin, account_id: str, force_verify: bool = False):
    """
    """
    user = kc_admin.get_user(account_id)
    if force_verify or not user.get("emailVerified", False):
        try:
            kc_admin.send_verify_email(account_id)
        except KeycloakError as e:
            logger.error("Creating Keycloak user failed.", exc_info=e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e

class EmailModel(BaseModel):
    user_id: str
    email: str

@router.post("/email/verify/", description="Request to send verify email")
def email_verify_requset(
        request: Request,
        body: EmailModel,
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
        ):
    user: TapirUser|None = session.query(TapirUser).filter(TapirUser.email == body.email).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    _send_verify_email(kc_admin, user.user_id, force_verify=True)
    return

class EmailUpdateModel(EmailModel):
    new_email: str


@router.put("/email/", description="Request to change email")
def change_email(
        request: Request,
        body: EmailUpdateModel,
        session: Session = Depends(get_db),
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
        ):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    user: TapirUser|None = session.query(TapirUser).filter(TapirUser.email == body.email).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Old email does not exist")

    other_user: TapirUser|None = session.query(TapirUser).filter(TapirUser.email == body.new_email).one_or_none()
    if other_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email already exists")

    if current_user.user_id != user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    user.email = body.new_email
    user.flag_email_verified = False

    kc_user = kc_admin.get_user(body.user_id)
    if kc_user:
        # The user has not migrated to KC? Trying to log in should have done the migration
        try:
            kc_admin.update_user(kc_user["id"], payload={"email": body.new_email, "emailVerified": False})
        except KeycloakError as e:
            logger.error("Updating Keycloak user failed.", exc_info=e)
            session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    session.add(user)
    session.commit()
    if kc_user:
        _send_verify_email(kc_admin, kc_user["id"], force_verify=True)
    return


class ChangePasswordModel(BaseModel):
    user_id: str
    old_password: str
    new_password: str



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


@router.put('/password/', description="Update user password")
async def change_user_password(
    request: Request,
    data: ChangePasswordModel,
    current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
    access_token: Optional[str] = Depends(get_current_user_access_token),
    session: Session = Depends(get_db),
    kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    """
    Change user password
    """
    logger.debug("User password changed request. Current %s, data %s, Old password %s, new password %s",
                 current_user.user_id if current_user else "No User", data.user_id,
                sha256_base64_encode(data.old_password), sha256_base64_encode(data.new_password))

    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if len(data.old_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is invalid")

    if not validate_password(data.new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password is invalid")

    if (current_user.user_id != data.user_id) and (not current_user.is_admin):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not allowed. User ID: %s" % data.user_id)

    user: TapirUser|None = session.query(TapirUser).filter(TapirUser.user_id == data.user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    nick: TapirNickname | None = session.query(TapirNickname).filter(TapirNickname.user_id == data.user_id).one_or_none()
    if nick is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    pwd: TapirUsersPassword | None = session.query(TapirUsersPassword).filter(TapirUsersPassword.user_id == data.user_id).one_or_none()
    if pwd is None:
        pwd = TapirUsersPassword(
            user_id=data.user_id,
            password_storage=2,
            password_enc= passwords.hash_password(data.old_password),
        )
        pass

    # The password is managed by Keycloak - so don't check it against tapir
    # try:
    #     domain_user, domain_auth = authenticate.authenticate(user.email, data.old_password)
    # except AuthenticationFailed:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")

    idp = request.app.extra["idp"]

    # if not kc_check_old_password(kc_admin, idp, nick.nickname, data.old_password, idp._ssl_cert_verify):
    if not await kc_validate_access_token(kc_admin, idp, access_token):
        if current_user.user_id == data.user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stale access. Please log out/login again.")
        if not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stale access. Please log out/login again.")

    kc_user = kc_admin.get_user(data.user_id)
    if not kc_user:
        # The user has not migrated to KC? Trying to log in should have done the migration
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="The user has not been migrated")

    try:
        kc_admin.set_user_password(kc_user["id"], data.new_password, temporary=False)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Changing password failed")

    pwd.password_enc = passwords.hash_password(data.new_password)
    session.add(pwd)
    session.commit()

    logger.info("User password changed successfully. Old password %s, new password %s",
                sha256_base64_encode(data.old_password), sha256_base64_encode(data.new_password))
