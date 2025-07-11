"""Account management,

"""
import base64
import re
import secrets
from datetime import datetime, timezone
import random
import string
from typing import Optional, List

from arxiv_bizlogic.bizmodels.user_model import UserModel
from arxiv_bizlogic.validation.email_validation import is_valid_email
from arxiv_bizlogic.fastapi_helpers import get_current_user_access_token, get_client_host_name
from fastapi import APIRouter, Depends, status, HTTPException, Request, Response, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from keycloak import KeycloakAdmin
from keycloak.exceptions import (KeycloakGetError, KeycloakError)


from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.db.models import TapirUser, TapirNickname, TapirUsersPassword, OrcidIds, AuthorIds, Demographic
from arxiv.auth.legacy import passwords

from . import (get_current_user_or_none, get_db, get_keycloak_admin, stateless_captcha,
               get_client_host, sha256_base64_encode, get_super_user_id,
               verify_bearer_token, ApiToken, is_super_user, describe_super_user, check_authnz,
               is_authorized, get_authn_or_none, get_arxiv_user_claims)  # , get_client_host
from .biz.account_biz import (AccountInfoModel, get_account_info,
                              AccountRegistrationError, AccountRegistrationModel, validate_password,
                              migrate_to_keycloak,
                              kc_validate_access_token, kc_send_verify_email, register_arxiv_account,
                              update_tapir_account, AccountIdentifierModel, kc_login_with_client_credential)
from .biz.cold_migration import cold_migrate
from .biz.email_history_biz import TapirEmailChangeTokenModel, EmailHistoryBiz, UserEmailHistory, add_admin_email_change_log, \
    EmailChangeEntry
# from . import stateless_captcha
from .captcha import CaptchaTokenReplyModel, get_captcha_token
from .stateless_captcha import InvalidCaptchaToken, InvalidCaptchaValue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])


def reply_account_info(session: Session, id: str) -> AccountInfoModel:
    account = get_account_info(session, id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return account


@router.get('/current', description="")
async def get_current_user_info(
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        session: Session = Depends(get_db)
        ) -> AccountInfoModel:
    """
    Hit the db and get user info
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    return reply_account_info(session, str(current_user.user_id))


@router.get('/profile/{user_id:str}')
async def get_user_profile(user_id: str,
                           current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
                           token: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token),
                           session: Session = Depends(get_db)
                           ) -> AccountInfoModel:
    check_authnz(token, current_user, user_id)

    return reply_account_info(session, user_id)

#
# Profile update and registering user is VERY similar. It is essentially upsert. At some point, I should think
# about refactor these two.
@router.put('/profile/', description="Update the user account profile for both Keycloak and user in db")
async def update_account_profile(
        data: AccountInfoModel,
        authn: Optional[ArxivUserClaims | ApiToken] = Depends(get_authn_or_none),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
) -> AccountInfoModel:
    """
    Update the profile name of a user.
    """
    user_id = data.id
    check_authnz(authn, None, user_id)

    # class AccountInfoModel:
    #    username: str  # aka nickname in Tapir
    #    email: Optional[str] = None
    #    first_name: str
    #    last_name: str
    #    suffix_name: Optional[str] = None
    #    country: Optional[str] = None
    #    affiliation: Optional[str] = None
    #    default_category: Optional[CategoryIdModel] = None
    #    groups: Optional[List[CategoryGroup]] = None
    #    url: Optional[str] = None
    #    joined_date: Optional[int] = None
    #    oidc_id: Optional[str] = None
    #    career_status: Optional[CAREER_STATUS] = None
    #    tracking_cookie: Optional[str] = None
    #    veto_status: Optional[VetoStatusEnum] = None
    #
    #    id
    #    email_verified: Optional[bool] = None
    #    scopes: Optional

    existing_user = UserModel.one_user(session, user_id)
    if existing_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if existing_user.username != data.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username/user id do not match")

    updates = data.to_user_model_data(exclude_defaults=True, exclude_unset=True)
    for field in ["email", "joined_date", "tracking_cookie", "veto_status", "email_verified", "scopes"]:
        if field in updates:
            del updates[field]

    scrubbed = AccountInfoModel.from_user_model_data(updates)
    tapir_user = update_tapir_account(session, scrubbed)
    if not isinstance(tapir_user, TapirUser):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Tapir User")

    return reply_account_info(session, str(tapir_user.user_id))


# See profile update comment.
@router.post('/register/',
             status_code=status.HTTP_201_CREATED,
             responses={
                 status.HTTP_201_CREATED: {"model": AccountInfoModel, "description": "Successfully created account"},
                 status.HTTP_400_BAD_REQUEST: {"model": AccountRegistrationError,
                                               "description": "Invalid registration data"},
                 status.HTTP_404_NOT_FOUND: {"model": AccountRegistrationError, "description": "User not found"},
             }
             )
async def register_account(
        request: Request,
        response: Response,
        registration: AccountRegistrationModel,
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
        token: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token),
) -> AccountInfoModel | AccountRegistrationError:
    """
    Create a new user
    """
    captcha_secret = request.app.extra['CAPTCHA_SECRET']
    host = get_client_host(request)
    if host is None:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="The request requires a client host")

    if not registration.email.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email is required")
    if not registration.username.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username is required")

    # registration = sanitize_model_data(registration)

    if is_super_user(token):
        logger.info("API based user registration %s", describe_super_user(token))
        pass
    else:
        # Check the captcha value against the captcha token.
        try:
            stateless_captcha.check(registration.token, registration.captcha_value, captcha_secret, host)

        except InvalidCaptchaToken:
            logger.warning(f"Registration: captcha token is invalid {registration.token!r} {host!r}")
            detail = AccountRegistrationError(message="Captcha token is invalid. Restart the registration",
                                              field_name="Captcha token")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return detail

        except InvalidCaptchaValue:
            logger.info(f"Registration: wrong captcha value {registration.token!r} {host!r} {registration.captcha_value!r}")
            detail = AccountRegistrationError(message="Captcha answer is incorrect.", field_name="Captcha answer")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return detail

        if not validate_password(registration.password):
            detail = AccountRegistrationError(message="Captcha answer is incorrect.", field_name="Password")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return detail
        pass

    client_secret = request.app.extra['ARXIV_USER_SECRET']

    if registration.keycloak_migration:
        data: Optional[TapirNickname] = session.query(TapirNickname).filter(
            TapirNickname.nickname == registration.username).one_or_none()
        if not data:
            error_response = AccountRegistrationError(message="Username is not found", field_name="username")
            response.status_code = status.HTTP_404_NOT_FOUND
            return error_response

        account = get_account_info(session, str(data.user_id))
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        # Rather than creating user, let the legacy user migration create the account.
        migrate_to_keycloak(kc_admin, account, registration.password, client_secret)
        return account

    maybe_tapir_user = register_arxiv_account(kc_admin, client_secret, session, registration)
    if isinstance(maybe_tapir_user, TapirUser):
        logger.info("User account created successfully")
        result = get_account_info(session, str(maybe_tapir_user.user_id))
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return result
    elif isinstance(maybe_tapir_user, AccountRegistrationError):
        response.status_code = status.HTTP_404_NOT_FOUND
        logger.error("Failed to create user account")
        return maybe_tapir_user
    # notreachd
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="register_arxiv_account returned an unexpected result")


@router.get("/register/")
def get_register(request: Request) -> CaptchaTokenReplyModel:
    return get_captcha_token(request)


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
    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.email == body.email).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    kc_send_verify_email(kc_admin, str(user.user_id), force_verify=True)
    return


class EmailVerifiedStatus(BaseModel):
    user_id: str
    email_verified: bool

@router.get("/email/verified/", description="Is the email verified for this usea?")
def get_email_verified_status_current_user(
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        session: Session = Depends(get_db),
) -> EmailVerifiedStatus:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == current_user.user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return EmailVerifiedStatus(email_verified=bool(user.flag_email_verified), user_id =str(user.user_id))


@router.get("/email/verified/{user_id:str}/", description="Is the email verified for this usea?")
def get_email_verified_status(
        user_id: str,
        authn: Optional[ArxivUserClaims] = Depends(get_authn_or_none),
        session: Session = Depends(get_db),
) -> EmailVerifiedStatus:
    check_authnz(authn, None, user_id)

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return EmailVerifiedStatus(email_verified=bool(user.flag_email_verified), user_id = user_id)


@router.put("/email/verified/", description="Set the email verified status")
def set_email_verified_status(
        body: EmailVerifiedStatus,
        authn: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token),
        remote_host: str = Depends(get_client_host),
        remote_hostname: str = Depends(get_client_host_name),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
) -> EmailVerifiedStatus:
    if authn is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = body.user_id
    check_authnz(authn, None, user_id)

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    nick: TapirNickname | None = session.query(TapirNickname).filter(TapirNickname.user_id == user_id).first()
    if not nick:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        # Update the email verified status. If the user has not migrated to Keycloak yet, no worries.
        kc_user_id = kc_admin.get_user_id(nick.nickname)
        if kc_user_id:
            kc_admin.update_user(user_id=kc_user_id, payload={"emailVerified": body.email_verified})
    except KeycloakGetError as kce:
        # Handle errors here
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(kce)) from kce

    biz: EmailHistoryBiz = EmailHistoryBiz(session, user_id=user_id)

    user.flag_email_verified = 1 if body.email_verified else 0

    if not biz.email_verified(remote_ip=remote_host, remote_host=remote_hostname):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is not verified.")

    session.commit()
    return EmailVerifiedStatus(email_verified=bool(user.flag_email_verified), user_id = user_id)


class EmailUpdateModel(EmailModel):
    user_id: str
    new_email: str
    email_verified: Optional[bool] = None  # This is only useful when the admin wants to set the verify status
    comment: Optional[str] = None


@router.put("/email/", description="Request to change email", responses={
    400: {
        "description": "Old and new email are the same. Or bad new email address",
        "content": {
            "application/json": {
                "example": {"detail": "Old and new email are the same"},
            }
        },
    },
    401: {
        "description": "Not logged in",
        "content": {
            "application/json": {
                "example": {"detail": "Not authorized to change this email"}
            }
        },
    },
    403: {
        "description": "Forbidden - not allowed to change this email",
        "content": {
            "application/json": {
                "example": {"detail": "Not authorized to change this email"}
            }
        },
    },
    404: {
        "description": "Old email does not exist",
        "content": {
            "application/json": {
                "example": {"detail": "Old email does not exist"}
            }
        },
    },
    409: {
        "description": "The email already exists",
        "content": {
            "application/json": {
                "example": {"detail": "The requested email is already used by other user."}
            }
        },
    },
    429: {
        "description": "Too many email change request",
        "content": {
            "application/json": {
                "example": {"detail": "Too many email change request."}
            }
        },
    },
    503: {
        "description": "Error while updating Keycloak",
        "content": {
            "application/json": {
                "example": {"detail": "Could not update Keycloak"}
            }
        },
    },
})
def change_email(
        request: Request,
        body: EmailUpdateModel,
        session: Session = Depends(get_db),
        client_host: str = Depends(get_client_host),
        client_hostname: str = Depends(get_client_host_name),
        authn: Optional[ArxivUserClaims|ApiToken] = Depends(get_authn_or_none),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    user_id = body.user_id
    check_authnz(authn, None, user_id)

    if not is_valid_email(body.new_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email is invalid.")

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.email == body.email).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Old email does not exist")

    other_user: TapirUser | None = session.query(TapirUser).filter(TapirUser.email == body.new_email).one_or_none()
    if other_user:
        if other_user.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="New email already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old and new email are the same")

    current_email = user.email
    kc_user = None
    try:
        kc_user = kc_admin.get_user(str(user_id))
    except KeycloakGetError:
        # The user has not been migrated yet
        logger.warning("Email change before user migration")
        pass

    biz: EmailHistoryBiz = EmailHistoryBiz(session, user_id=user_id)
    if is_super_user(authn):
        # admin change email
        # We can short circuit the rate limit, etc.
        email_verified = True if body.email_verified is None else body.email_verified

        if kc_user:
            # The user has not migrated to KC? Trying to log in should have done the migration
            try:
                kc_admin.update_user(kc_user["id"], payload={"email": body.new_email, "emailVerified": email_verified})
            except KeycloakError as e:
                logger.error("Updating Keycloak user failed.", exc_info=e)
                session.rollback()
                detail = "Account service not available at the moment. Please contact help@arxiv.org: " + str(e)
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
        else:
            # Force the issue, and create the account
            client_secret = request.app.extra['ARXIV_USER_SECRET']
            kc_user = cold_migrate(kc_admin, session, user_id, client_secret, email_verified=email_verified)

        claims = get_arxiv_user_claims(authn)
        tapir_session_id = None
        if claims:
            tapir_session_id = claims.session_id

        biz.set_user_email_by_admin(
            body.new_email,
            admin_id=get_super_user_id(authn),
            session_id=tapir_session_id,
            remote_host=client_host,
            remote_host_name=client_hostname,
            comment=body.comment,
            email_verified=email_verified,
            )
        session.commit()

        if not email_verified and kc_user:
            kc_send_verify_email(kc_admin, kc_user["id"], force_verify=True)
        return

    if biz.is_rate_exceeded():
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many email change request.")

    user.email = body.new_email
    user.flag_email_verified = False

    if kc_user:
        # The user has not migrated to KC? Trying to log in should have done the migration
        try:
            kc_admin.update_user(kc_user["id"], payload={"email": body.new_email, "emailVerified": False})
        except KeycloakError as e:
            logger.error("Updating Keycloak user failed.", exc_info=e)
            session.rollback()
            detail = "Account service not available at the moment. Please contact help@arxiv.org: " + str(e)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    else:
        # Force the issue, and create the account
        client_secret = request.app.extra['ARXIV_USER_SECRET']
        kc_user = cold_migrate(kc_admin, session, user_id, client_secret)

    entry = biz.add_email_change_request(
        TapirEmailChangeTokenModel(
            user_id=user_id,
            email=current_email,
            new_email=body.new_email,
            secret="",  # This is filled by add_email_history
            remote_addr=client_host,
            remote_host=client_hostname,
            used=False,
        )
    )

    session.commit()
    if kc_user:
        kc_send_verify_email(kc_admin, kc_user["id"], force_verify=True)
    return



@router.get("/email/history/{user_id:str}/", description="Get the past email history")
def get_email_history(
        request: Request,
        response: Response,
        user_id: str,

        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),

        authn: Optional[ArxivUserClaims|ApiToken] = Depends(get_authn_or_none),
        session: Session = Depends(get_db),
) -> List[EmailChangeEntry]:
    check_authnz(authn, None, user_id)
    biz: EmailHistoryBiz = EmailHistoryBiz(session, user_id=user_id)
    history = biz.list_email_history()

    if _start is None:
        _start = 0
    if _end is None:
        _end = len(history)

    response.headers['X-Total-Count'] = str(len(history.change_history))
    return history.change_history[_start:_end]


class PasswordUpdateModel(BaseModel):
    user_id: str
    old_password: str
    new_password: str


@router.put('/password/', description="Update user password")
async def change_user_password(
        request: Request,
        data: PasswordUpdateModel,
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        kc_access_token: Optional[str] = Depends( get_current_user_access_token),
        token: ApiToken | ArxivUserClaims | None = Depends(verify_bearer_token),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    """
    Change user password
    """
    logger.debug("User password changed request. Current %s, data %s, Old password %s, new password %s",
                 current_user.user_id if current_user else "No User", data.user_id,
                 sha256_base64_encode(data.old_password), sha256_base64_encode(data.new_password))

    user_id = data.user_id
    check_authnz(token, current_user, user_id)

    if len(data.old_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is invalid")

    if not validate_password(data.new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password is invalid")

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == data.user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    nick: TapirNickname | None = session.query(TapirNickname).filter(
        TapirNickname.user_id == data.user_id).one_or_none()
    if nick is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    pwd: TapirUsersPassword | None = session.query(TapirUsersPassword).filter(
        TapirUsersPassword.user_id == data.user_id).one_or_none()
    if pwd is None:
        pwd = TapirUsersPassword(
            user_id=data.user_id,
            password_storage=2,
            password_enc=passwords.hash_password(data.old_password),
        )
        pass

    # The password is managed by Keycloak - so don't check it against tapir
    # try:
    #     domain_user, domain_auth = authenticate.authenticate(user.email, data.old_password)
    # except AuthenticationFailed:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")

    idp = request.app.extra["idp"]

    # if not kc_check_old_password(kc_admin, idp, nick.nickname, data.old_password, idp._ssl_cert_verify):
    if isinstance(token, ArxivUserClaims):
        if kc_access_token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Stale access. Please log out/login again.")

        current_user = token
        if not await kc_validate_access_token(kc_admin, idp, kc_access_token):
            if current_user.user_id == data.user_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Stale access. Please log out/login again.")
            if not current_user.is_admin:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Stale access. Please log out/login again.")

    kc_user = None
    try:
        kc_user = kc_admin.get_user(data.user_id)
    except KeycloakGetError:
        pass

    tapir_password: TapirUsersPassword | None = session.query(TapirUsersPassword).filter(
        TapirUsersPassword.user_id == user_id).one_or_none()
    if not tapir_password:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Password has never been set")

    um: UserModel | None = UserModel.one_user(session, str(user_id))
    if um is None:
        # This should not happen. The tapir user exists and therefore, this must succeed.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    client_secret = request.app.extra['ARXIV_USER_SECRET']

    if not kc_user:
        try:
            passwords.check_password(data.old_password, tapir_password.password_enc.encode("ascii"))
        except:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Incorrect password")

        tapir_password.password_enc = passwords.hash_password(data.new_password)
        session.commit()
        try:
            account = AccountInfoModel(
                id = str(um.id),
                email_verified=False,
                email = um.email,
                username= um.username,
                first_name = um.first_name,
                last_name=um.last_name,
            )
            migrate_to_keycloak(kc_admin, account, data.new_password, client_secret)
        finally:
            pass
    else:
        kc_cred = kc_login_with_client_credential(kc_admin, um.username, data.old_password, client_secret)
        if kc_cred is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Incorrect password")

        try:
            kc_admin.set_user_password(kc_user["id"], data.new_password, temporary=False)
        except Exception as _exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Changing password failed")

        pwd.password_enc = passwords.hash_password(data.new_password)
        session.commit()

    logger.info("User password changed successfully. Old password %s, new password %s",
                sha256_base64_encode(data.old_password), sha256_base64_encode(data.new_password))


class PasswordResetRequest(BaseModel):
    username_or_email: str


@router.post('/password/reset/', description="Reset user password",
             status_code=status.HTTP_201_CREATED)
async def reset_user_password(
        request: Request,
        body: PasswordResetRequest,
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        token: Optional[ApiToken] = Depends(verify_bearer_token),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    """
    Reset user password
    """
    logger.debug("User password reset request. Current %s",
                 current_user.user_id if current_user else "No User")

    tapir_user: TapirUser | None = None
    nickname: TapirNickname | None = None

    if '@' in body.username_or_email:
        tapir_user = session.query(TapirUser).filter(TapirUser.email == body.username_or_email).one_or_none()
    else:
        nickname = session.query(TapirNickname).filter(TapirNickname.nickname == body.username_or_email).one_or_none()

    if nickname:
        tapir_user = session.query(TapirUser).filter(TapirUser.user_id == nickname.user_id).one_or_none()
    elif tapir_user:
        nickname = session.query(TapirNickname).filter(TapirNickname.user_id == tapir_user.user_id).one_or_none()

    if tapir_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    if nickname is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    user_id = tapir_user.user_id
    email = tapir_user.email
    username = nickname.nickname

    kc_user = None
    try:
        kc_user = kc_admin.get_user(str(user_id))
    except KeycloakGetError as exc:
        pass

    if not kc_user:
        client_secret = request.app.extra['ARXIV_USER_SECRET']
        account = AccountInfoModel(
            id=str(user_id),
            username=username,
            email=email,
            first_name=tapir_user.first_name if tapir_user.first_name else "",
            last_name=tapir_user.last_name if tapir_user.last_name else "",
        )
        password = base64.b85encode(random.randbytes(32)).decode('ascii')
        migrate_to_keycloak(kc_admin, account, password, client_secret)
        kc_user = kc_admin.get_user(str(user_id))

    if not kc_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to migrate a user account")

    try:
        kc_admin.send_update_account(user_id=str(user_id), payload={"requiredActions": ["UPDATE_PASSWORD"]})
    except KeycloakGetError as kce:
        detail = "Password reset request did not succeed due to arXiv server problem. " + str(kce)
        ex_body: str = kce.response_body.decode('utf-8') if kce.response_body and isinstance(kce.response_body, bytes) else (
            str(kce.response_body))
        if ex_body.find("send email") >= 0:
            detail += "\nKeycloak failed to send email. Please contact mailto:help@arXiv.org"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from kce
    except Exception as exc:
        detail = "Password reset request did not succeed: " + str(exc)
        logger.error(detail)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc
    return


@router.get('/identifier/')
async def get_user_profile_with_query(
        user_id: Optional[str] = Query(None, description="User ID"),
        email: Optional[str] = Query(None, description="Email"),
        username: Optional[str] = Query(None, description="Logi name"),
        token: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token),
        session: Session = Depends(get_db)
        ) -> AccountIdentifierModel:

    user: TapirUser
    nick: TapirNickname
    demo: Demographic
    orcid: OrcidIds
    xauth: AuthorIds

    if user_id is None:
        if username or email:
            # If you know an email or username, there is no security concern as both are equivalent
            query = session.query(TapirUser, TapirNickname).join(TapirNickname, TapirUser.user_id == TapirNickname.user_id)
            if username:
                query = query.filter(TapirNickname.nickname == username)
            else:
                query = query.filter(TapirUser.email == email)

            tapir_user = query.one_or_none()
            if tapir_user:
                user, nick = tapir_user
                user_id = str(user.user_id)

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not is_authorized(token, None, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized. If you want to know your user id, use /current")
    user_data = (session.query(TapirUser, TapirNickname, Demographic, OrcidIds, AuthorIds)
             .outerjoin(TapirNickname, TapirUser.user_id == TapirNickname.user_id)
             .outerjoin(Demographic, TapirUser.user_id == Demographic.user_id)
             .outerjoin(OrcidIds, TapirUser.user_id == OrcidIds.user_id)
             .outerjoin(AuthorIds, TapirUser.user_id == AuthorIds.user_id)
             .filter(TapirUser.user_id == user_id).one_or_none())
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Username not found")
    user, nick, demo, orcid, xauth = user_data
    return AccountIdentifierModel(user_id=str(user.user_id), username=nick.nickname, email=user.email,
                                  orcid=orcid.orcid, author_id=xauth.author_id)


#
# ORCID comes from logging into ORCID and get the ORCID back. This is done elsewhere atm.
#
class OrcidUpdateModel(BaseModel):
    user_id: str
    orcid: Optional[str] = None
    orcid_auth: Optional[str] = None
    authenticated: bool

@router.put("/orcid/", description="Update ORCID", responses={
    401: {
        "description": "Not logged in",
        "content": {
            "application/json": {
                "example": {"detail": "Not authenticated"}
            }
        },
    },
    403: {
        "description": "Forbidden - not allowed to change the ORCID data",
        "content": {
            "application/json": {
                "example": {"detail": "Not authorized to set the ORCID data"}
            }
        },
    },
    503: {
        "description": "Error while updating Keycloak",
        "content": {
            "application/json": {
                "example": {"detail": "Could not update Keycloak"}
            }
        },
    },
})
def upsert_orcid(
        request: Request,
        body: OrcidUpdateModel,
        session: Session = Depends(get_db),
        authn: Optional[ArxivUserClaims|ApiToken] = Depends(get_authn_or_none),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    user_id = body.user_id
    check_authnz(authn, None, user_id)

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Old email does not exist")

    orcid_id: OrcidIds | None = session.query(OrcidIds).filter(OrcidIds.user_id == user_id).one_or_none()

    try:
        if body.orcid is not None:
            # Validate ORCID format (ORCID is typically 4 blocks of 4 digits/characters with hyphens)
            if not re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$', body.orcid):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ORCID format")

            current_time = datetime.now(tz=timezone.utc)
            authenticated = 1 if body.authenticated else 0

            if orcid_id:
                # Update existing record
                orcid_id.orcid = body.orcid
                orcid_id.authenticated = authenticated
                orcid_id.updated = current_time
            else:
                # Create new record
                new_orcid = OrcidIds(
                    user_id=user_id,
                    orcid=body.orcid,
                    authenticated=authenticated,
                    updated=current_time
                )
                session.add(new_orcid)

            # Try to update Keycloak as well
            # try:
            #     # Assuming Keycloak needs ORCID info in the user attributes
            #     user_id_str = str(user_id)
            #     keycloak_user = kc_admin.get_user(user_id_str)
            #
            #     # Update the attributes
            #     attributes = keycloak_user.get('attributes', {})
            #     attributes['orcid'] = body.orcid
            #     if body.orcid_auth:
            #         attributes['orcid_auth'] = body.orcid_auth
            #     attributes['orcid_authenticated'] = str(body.authenticated).lower()
            #
            #     kc_admin.update_user(user_id=user_id_str, payload={"attributes": attributes})
            #
            # except Exception as e:
            #     logger.error(f"Failed to update Keycloak: {str(e)}")
            #     # Rollback the database changes
            #     session.rollback()
            #     raise HTTPException(
            #         status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            #         detail="Could not update Keycloak"
            #     )

            # Commit the changes to the database
            session.commit()

            return {"detail": "ORCID updated successfully"}

        elif orcid_id:
            # If orcid is None and there's an existing record, remove it
            session.delete(orcid_id)

            # Try to remove ORCID info from Keycloak as well
            # try:
            #     user_id_str = str(user_id)
            #     keycloak_user = kc_admin.get_user(user_id_str)
            #
            #     # Update the attributes to remove ORCID info
            #     attributes = keycloak_user.get('attributes', {})
            #     if 'orcid' in attributes:
            #         del attributes['orcid']
            #     if 'orcid_auth' in attributes:
            #         del attributes['orcid_auth']
            #     if 'orcid_authenticated' in attributes:
            #         del attributes['orcid_authenticated']
            #
            #     kc_admin.update_user(user_id=user_id_str, payload={"attributes": attributes})
            #
            # except Exception as e:
            #     logger.error(f"Failed to update Keycloak: {str(e)}")
            #     # Rollback the database changes
            #     session.rollback()
            #     raise HTTPException(
            #         status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            #         detail="Could not update Keycloak"
            #     )

            # Commit the changes to the database
            session.commit()

            return {"detail": "ORCID removed successfully"}

        else:
            # No change needed
            return {"detail": "No changes to ORCID"}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to update ORCID: {str(e)}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update ORCID: {str(e)}"
        )



class AuthorIdUpdateModel(BaseModel):
    user_id: str
    author_id: Optional[str] = None


@router.put("/author_id/", description="Update AUTHOR_ID", responses={
    401: {
        "description": "Not logged in",
        "content": {
            "application/json": {
                "example": {"detail": "Not authenticated"}
            }
        },
    },
    403: {
        "description": "Forbidden - not allowed to change the AUTHOR_ID data",
        "content": {
            "application/json": {
                "example": {"detail": "Not authorized to set the AUTHOR_ID data"}
            }
        },
    },
    503: {
        "description": "Error while updating Keycloak",
        "content": {
            "application/json": {
                "example": {"detail": "Could not update Keycloak"}
            }
        },
    },
})
def upsert_author_id(
        request: Request,
        body: AuthorIdUpdateModel,
        session: Session = Depends(get_db),
        authn: Optional[ArxivUserClaims|ApiToken] = Depends(get_authn_or_none),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    user_id = body.user_id
    check_authnz(authn, None, user_id)

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Old email does not exist")

    author_id: AuthorIds | None = session.query(AuthorIds).filter(AuthorIds.user_id == user_id).one_or_none()

    try:
        if body.author_id is not None:
            current_time = datetime.now(tz=timezone.utc)

            if author_id:
                # Update existing record
                author_id.author_id = body.author_id
                author_id.updated = current_time
            else:
                # Create new record
                new_author_id = AuthorIds(
                    user_id=user_id,
                    author_id=body.author_id,
                    updated=current_time
                )
                session.add(new_author_id)

            # Try to update Keycloak as well
            # try:
            #     # Assuming Keycloak needs AUTHOR_ID info in the user attributes
            #     user_id_str = str(user_id)
            #     keycloak_user = kc_admin.get_user(user_id_str)
            #
            #     # Update the attributes
            #     attributes = keycloak_user.get('attributes', {})
            #     attributes['author_id'] = body.author_id
            #     if body.author_id_auth:
            #         attributes['author_id_auth'] = body.author_id_auth
            #     attributes['author_id_authenticated'] = str(body.authenticated).lower()
            #
            #     kc_admin.update_user(user_id=user_id_str, payload={"attributes": attributes})
            #
            # except Exception as e:
            #     logger.error(f"Failed to update Keycloak: {str(e)}")
            #     # Rollback the database changes
            #     session.rollback()
            #     raise HTTPException(
            #         status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            #         detail="Could not update Keycloak"
            #     )

            # Commit the changes to the database
            session.commit()

            return {"detail": "AUTHOR_ID updated successfully"}

        elif author_id:
            # If author_id is None and there's an existing record, remove it
            session.delete(author_id)

            # Try to remove AUTHOR_ID info from Keycloak as well
            # try:
            #     user_id_str = str(user_id)
            #     keycloak_user = kc_admin.get_user(user_id_str)
            #
            #     # Update the attributes to remove AUTHOR_ID info
            #     attributes = keycloak_user.get('attributes', {})
            #     if 'author_id' in attributes:
            #         del attributes['author_id']
            #     if 'author_id_auth' in attributes:
            #         del attributes['author_id_auth']
            #     if 'author_id_authenticated' in attributes:
            #         del attributes['author_id_authenticated']
            #
            #     kc_admin.update_user(user_id=user_id_str, payload={"attributes": attributes})
            #
            # except Exception as e:
            #     logger.error(f"Failed to update Keycloak: {str(e)}")
            #     # Rollback the database changes
            #     session.rollback()
            #     raise HTTPException(
            #         status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            #         detail="Could not update Keycloak"
            #     )

            # Commit the changes to the database
            session.commit()

            return {"detail": "AUTHOR_ID removed successfully"}

        else:
            # No change needed
            return {"detail": "No changes to AUTHOR_ID"}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to update AUTHOR_ID: {str(e)}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update AUTHOR_ID: {str(e)}"
        )


#
class UserStatusModel(BaseModel):
    user_id: str
    deleted: Optional[bool]
    banned: Optional[bool]
    # maybe add more


@router.put("/status/", description="Update User flags", responses={
    401: {
        "description": "Not logged in",
        "content": {
            "application/json": {
                "example": {"detail": "Not authenticated"}
            }
        },
    },
    403: {
        "description": "Forbidden - not allowed to change the ORCID data",
        "content": {
            "application/json": {
                "example": {"detail": "Not authorized to set the ORCID data"}
            }
        },
    },
    503: {
        "description": "Error while updating Keycloak",
        "content": {
            "application/json": {
                "example": {"detail": "Could not update Keycloak"}
            }
        },
    },
})
def update_user_status(
        body: UserStatusModel,
        session: Session = Depends(get_db),
        authn: Optional[ArxivUserClaims|ApiToken] = Depends(get_authn_or_none),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    user_id = body.user_id
    check_authnz(authn, None, user_id)

    user: UserModel | None = UserModel.one_user(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} does not exist")

    tapir_user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if not tapir_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} does not exist")

    if body.deleted is not None:
        if tapir_user.flag_deleted != body.deleted:
            tapir_user.flag_deleted = body.deleted

    if body.banned is not None:
        if tapir_user.flag_banned != body.banned:
            tapir_user.flag_banned = body.banned

    if session.is_modified(tapir_user):
        # The source of truth shall be updated
        session.commit()

        user_enabled = not (tapir_user.flag_banned or tapir_user.flag_deleted)
        kc_user = None
        try:
            # Get the Keycloak user
            kc_user = kc_admin.get_user(user_id)
        except Exception as e:
            logger.error(f"Failed to update Keycloak: {str(e)}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to update Keycloak: {str(e)}")

        if kc_user:
            # if kc user does not exist, no worries. User migration will take care of it
            try:
                # Enable or disable the user in Keycloak
                kc_admin.update_user(user_id, {"enabled": user_enabled})
                logger.info(f"Disabled user {user_id} in Keycloak")

            except Exception as e:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                    detail=f"Failed to update Keycloak: {str(e)}")

    return
