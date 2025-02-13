"""Account management,

"""
from typing import Optional, List

import httpx
from arxiv.auth.domain import UserFullName, UserProfile, OTHER
from fastapi import APIRouter, Depends, status, HTTPException, Request
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

from . import get_current_user_or_none, get_db, get_keycloak_admin, get_client_host
from . import stateless_captcha
from .captcha import CaptchaTokenReplyModel, get_captcha_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])


# arxiv-submit/lib/arXiv/Controller/Admin/User.pm

CAREER_STATUS = ["Unknown", "Staff", "Professor", "Post Doc", "Grad Student", "Other"]

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
    email: str
    first_name: str
    last_name: str
    suffix_name: Optional[str]
    country: Optional[str]
    affiliation: Optional[str]
    default_category: Optional[CategoryIdModel]
    groups: Optional[List[str]]
    url: Optional[str]
    joined_date: Optional[int]
    oidc_id: Optional[str]
    groups: Optional[List[str]]
    career_status: str


class AccountInfoModel(AccountInfoBaseModel):
    id: str
    email_verified: bool
    scopes: Optional[List[str]]


class AccountRegistrationModel(AccountInfoBaseModel):
    password: str
    origin_ip: Optional[str]
    origin_host: Optional[str]
    token: str
    captcha_value: str
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
            email_verified = tapir_user.flag_email_verified,
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
            career_status = CAREER_STATUS[max(0, min(5, demographic.type))],
        )
        return account
    return None


def reply_account_info(session: Session, id: str) -> AccountInfoModel:
    account = get_account_info(session, id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return account


@router.get('/info/current')
async def info(current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
               session: Session = Depends(get_db)
          ) -> AccountInfoModel:
    """
    Hit the db and get user info
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return reply_account_info(session, current_user.user_id)

@router.get('/info/id:str')
async def info(id: str,
               current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
               session: Session = Depends(get_db)
          ) -> AccountInfoModel:
    """
    Hit the db and get user info
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    ok = current_user.is_admin or current_user.is_admin or current_user.user_id == id
    if not ok:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return reply_account_info(session, id)


@router.post('/register/')
async def register(
        request: Request,
        registration: AccountRegistrationModel,
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
        ) -> AccountInfoModel:
    """
    Create a new user
    """
    client_secret = request.app.extra['ARXIV_USER_SECRET']

    if registration.keycloak_migration:
        data: Optional[TapirNickname] = session.query(TapirNickname).filter(TapirNickname.nickname == registration.username).one_or_none()
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
        _migrate_to_keycloak(kc_admin, account, registration.password, client_secret)

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    logger.info("User account created successfully")
    return account



@router.get("/register/")
def get_register(request: Request) -> CaptchaTokenReplyModel:
    return get_captcha_token(request)


def _set_user_password(kc_admin: KeycloakAdmin, account: AccountInfoModel, password: str):
    try:
        kc_admin.set_user_password(account.id, password, temporary=False)
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
    email: str

@router.post("/email/verify/")
def email_verify_requset(
        request: Request,
        body: EmailModel,
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
        ):
    user = session.query(TapirUser).filter(TapirUser.email == body.email).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    _send_verify_email(kc_admin, user.user_id, force_verify=True)
    return

