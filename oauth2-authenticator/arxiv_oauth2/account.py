"""Account management,

"""
import base64
import random
from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from keycloak import KeycloakAdmin, KeycloakError
from keycloak.exceptions import (KeycloakGetError)

from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.db.models import TapirUser, Demographic, TapirNickname, TapirUsersPassword
from arxiv.auth.legacy import passwords

from . import (get_current_user_or_none, get_db, get_keycloak_admin, stateless_captcha,
               get_client_host, sha256_base64_encode, get_current_user_access_token)  # , get_client_host
from .biz.account_biz import (AccountInfoModel, get_account_info,
                              AccountRegistrationError, AccountRegistrationModel, validate_password,
                              migrate_to_keycloak,
                              kc_validate_access_token, kc_send_verify_email, register_arxiv_account,
                              update_tapir_account)
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    tapir_user = update_tapir_account(session, data)
    if not isinstance(tapir_user, TapirUser):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Tapir User")
    return reply_account_info(session, tapir_user.user_id)


# See profile update comment.
@router.post('/register/',
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
) -> AccountInfoModel | AccountRegistrationError:
    """
    Create a new user
    """
    captcha_secret = request.app.extra['CAPTCHA_SECRET']
    host = get_client_host(request)

    if not registration.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email is required")
    if not registration.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username is required")

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

    client_secret = request.app.extra['ARXIV_USER_SECRET']

    if registration.keycloak_migration:
        data: Optional[TapirNickname] = session.query(TapirNickname).filter(
            TapirNickname.nickname == registration.username).one_or_none()
        if not data:
            error_response = AccountRegistrationError(message="Username is not found", field_name="username")
            response.status_code = status.HTTP_404_NOT_FOUND
            return error_response

        account = get_account_info(session, str(data.user_id))
        # Rather than creating user, let the legacy user migration create the account.
        migrate_to_keycloak(kc_admin, account, registration.password, client_secret)
        result = account
    else:
        maybe_tapir_user = register_arxiv_account(kc_admin, client_secret, session, registration)
        if isinstance(maybe_tapir_user, TapirUser):
            logger.info("User account created successfully")
            result = get_account_info(session, str(maybe_tapir_user.user_id))
        else:
            result = maybe_tapir_user

    if isinstance(result, AccountRegistrationError):
        response.status_code = status.HTTP_404_NOT_FOUND
        logger.error("Failed to create user account")

    return result


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
    kc_send_verify_email(kc_admin, user.user_id, force_verify=True)
    return


class EmailUpdateModel(EmailModel):
    new_email: str


@router.put("/email/", description="Request to change email", responses={
    400: {
        "description": "Old and new email are the same",
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
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.email == body.email).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Old email does not exist")

    other_user: TapirUser | None = session.query(TapirUser).filter(TapirUser.email == body.new_email).one_or_none()
    if other_user:
        if other_user.user_id != user.user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="New email already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old and new email are the same")

    if str(current_user.user_id) != str(user.user_id) and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to change this email")

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
            detail = "Account service not available at the moment. Please contact help@arxiv.org: " + str(e)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    # session.add(user)
    session.commit()
    if kc_user:
        kc_send_verify_email(kc_admin, kc_user["id"], force_verify=True)
    return


class ChangePasswordModel(BaseModel):
    user_id: str
    old_password: str
    new_password: str


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
    if not await kc_validate_access_token(kc_admin, idp, access_token):
        if current_user.user_id == data.user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Stale access. Please log out/login again.")
        if not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Stale access. Please log out/login again.")

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


class PasswordResetRequest(BaseModel):
    username_or_email: str


@router.post('/password/reset/', description="Reset user password",
             status_code=status.HTTP_201_CREATED)
async def reset_user_password(
        request: Request,
        body: PasswordResetRequest,
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
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
    else:
        nickname = session.query(TapirNickname).filter(TapirNickname.user_id == tapir_user.user_id).one_or_none()

    if tapir_user is None or nickname is None:
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")
        return

    user_id = tapir_user.user_id
    email = tapir_user.email
    username = nickname.nickname

    kc_user = None
    try:
        kc_user = kc_admin.get_user(user_id)
    except KeycloakGetError as exc:
        pass

    if not kc_user:
        client_secret = request.app.extra['ARXIV_USER_SECRET']
        account = AccountInfoModel(
            id=str(user_id),
            username=username,
            email=email,
            first_name=tapir_user.first_name,
            last_name=tapir_user.last_name,
        )
        password = base64.b85encode(random.randbytes(32)).decode('ascii')
        migrate_to_keycloak(kc_admin, account, password, client_secret)
        kc_user = kc_admin.get_user(user_id)

    if not kc_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to migrate a user account")

    try:
        kc_admin.send_update_account(user_id=user_id, payload=["UPDATE_PASSWORD"])
    except KeycloakGetError as kce:
        detail = "Password reset request did not succeed due to arXiv server problem. " + str(kce)
        body = kce.response_body.decode('utf-8') if kce.response_body and isinstance(kce.response_body, bytes) else str(
            kce.response_body)
        if "send email" in body:
            detail += "\nKeycloak failed to send email. Please contact mailto:help@arXiv.org"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc
    except Exception as exc:
        detail = "Password reset request did not succeed: " + str(exc)
        logger.error(detail)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc
    return
