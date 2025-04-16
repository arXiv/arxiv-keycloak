"""Account management,

"""
import base64
import random
import string
from typing import Optional

from arxiv_bizlogic.bizmodels.user_model import UserModel
from arxiv_bizlogic.validation.email_validation import is_valid_email
from arxiv_bizlogic.fastapi_helpers import  get_current_user_access_token
from fastapi import APIRouter, Depends, status, HTTPException, Request, Response, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from keycloak import KeycloakAdmin
from keycloak.exceptions import (KeycloakGetError, KeycloakError)


from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.db.models import TapirUser, TapirNickname, TapirUsersPassword
from arxiv.auth.legacy import passwords

from . import (get_current_user_or_none, get_db, get_keycloak_admin, stateless_captcha,
               get_client_host, sha256_base64_encode,
               verify_bearer_token, ApiToken, is_super_user, describe_super_user, check_authnz,
               is_authorized, is_authenticated)  # , get_client_host
from .biz.account_biz import (AccountInfoModel, get_account_info,
                              AccountRegistrationError, AccountRegistrationModel, validate_password,
                              migrate_to_keycloak,
                              kc_validate_access_token, kc_send_verify_email, register_arxiv_account,
                              update_tapir_account, AccountIdentifierModel, kc_login_with_client_credential)
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
    return reply_account_info(session, current_user.user_id)


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
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        token: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
) -> AccountInfoModel:
    """
    Update the profile name of a user.
    """
    user_id = data.id
    check_authnz(token, current_user, user_id)

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
    if existing_user.username != data.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username/user id do not match")

    updates = data.to_user_model_data(exclude_defaults=True, exclude_unset=True)
    for field in ["email", "joined_date", "tracking_cookie", "veto_status", "email_verified", "scopes"]:
        if field in updates:
            del updates[field]

    scrubbed = AccountInfoModel.model_validate(updates)
    tapir_user = update_tapir_account(session, scrubbed)
    if not isinstance(tapir_user, TapirUser):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Tapir User")

    return reply_account_info(session, tapir_user.user_id)


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

    if not registration.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email is required")
    if not registration.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username is required")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return EmailVerifiedStatus(email_verified= user.is_verified, user_id = user.user_id)


@router.get("/email/verified/{user_id:str}/", description="Is the email verified for this usea?")
def get_email_verified_status(
        user_id: str,
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        token: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token),
        session: Session = Depends(get_db),
) -> EmailVerifiedStatus:
    check_authnz(token, current_user, user_id)

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return EmailVerifiedStatus(email_verified= user.is_verified, user_id = user_id)


@router.put("/email/verified/", description="Set the email verified status")
def set_email_verified_status(
        body: EmailVerifiedStatus,
        token: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token),
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
) -> EmailVerifiedStatus:
    user_id = body.user_id
    check_authnz(token, current_user, user_id)

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    try:
        user = kc_admin.get_user_id(current_user.username)
        kc_admin.update_user(user_id=user, payload={"emailVerified": body.email_verified})

    except KeycloakGetError as kce:
        # Handle errors here
        raise HTTPException(status_code=kce.response_code, detail=str(kce))

    user.is_verified = body.email_verified
    session.commit()
    return EmailVerifiedStatus(email_verified= user.is_verified, user_id = user_id)


class EmailUpdateModel(EmailModel):
    user_id: str
    new_email: str


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
        token: Optional[ApiToken] = Depends(verify_bearer_token),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    user_id = body.user_id
    check_authnz(token, current_user, user_id)

    if not is_valid_email(body.new_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email is invalid.")

    if not is_authenticated(token, current_user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    if not is_authorized(token, current_user, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to change this email")

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.email == body.email).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Old email does not exist")

    other_user: TapirUser | None = session.query(TapirUser).filter(TapirUser.email == body.new_email).one_or_none()
    if other_user:
        if other_user.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="New email already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old and new email are the same")

    user.email = body.new_email
    user.flag_email_verified = False

    kc_user = None
    try:
        kc_user = kc_admin.get_user(str(user_id))
    except KeycloakGetError:
        # The user has not been migrated yet
        logger.warning("Email change before user migration")
        pass

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
        #
        # I cannot come up with anything better, so here it goes.
        # 1. Save the current password data
        # 2. Smash the existing password with temporary password
        # 3. Using the temp password, migrate the user
        # 4. Once the migration is complete, restore the original password to Tapir password
        # 5. Purge the credentials from keycloak so the next login hits legacy auth provider and uses old password
        um: UserModel | None = UserModel.one_user(session, str(user_id))  # Use UserModel to get username
        if um is None:
            # This should not happen. The tapir user exists and therefore, this must succeed.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

        tapir_password: TapirUsersPassword = session.query(TapirUsersPassword).filter(TapirUsersPassword.user_id == user_id).one_or_none()
        current_password_enc = tapir_password.password_enc
        try:
            temp_password = ''.join(random.choices(string.ascii_letters, k=48))
            tapir_password.password_enc = passwords.hash_password(temp_password)
            session.commit()

            account = AccountInfoModel(
                id = str(um.id),
                email_verified=False,
                email = um.email,
                username= um.username,
                first_name = um.first_name,
                last_name=um.last_name,
            )
            client_secret = request.app.extra['ARXIV_USER_SECRET']
            migrate_to_keycloak(kc_admin, account, temp_password, client_secret)
        finally:
            tapir_password.password_enc = current_password_enc
            session.commit()

        credentials = kc_admin.get_credentials(str(user_id))
        for credential in credentials:
            credential_id = credential["id"]
            kc_admin.delete_credential(user_id=str(user_id), credential_id=credential_id)
        kc_user = kc_admin.get_user(str(user_id))

    session.commit()
    if kc_user:
        kc_send_verify_email(kc_admin, kc_user["id"], force_verify=True)
    return


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
        token: Optional[ApiToken] = Depends(verify_bearer_token),
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

    if not is_authenticated(token, current_user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    if not is_authorized(token, current_user, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

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
    if not isinstance(token, ApiToken):
        if kc_access_token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Stale access. Please log out/login again.")

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
        token = kc_login_with_client_credential(kc_admin, um.username, data.old_password, client_secret)
        if token is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Incorrect password")

        try:
            kc_admin.set_user_password(kc_user["id"], data.new_password, temporary=False)
        except Exception as exc:
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
        kc_admin.send_update_account(user_id=user_id, payload={"requiredActions": ["UPDATE_PASSWORD"]})
    except KeycloakGetError as kce:
        detail = "Password reset request did not succeed due to arXiv server problem. " + str(kce)
        body = kce.response_body.decode('utf-8') if kce.response_body and isinstance(kce.response_body, bytes) else str(
            kce.response_body)
        if "send email" in body:
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
    tapir = None

    if username or email:
        # If you know a email or username, there is no security concern as both are equivalent
        query = session.query(TapirUser, TapirNickname).join(TapirNickname, TapirUser.user_id == TapirNickname.user_id)
        if username:
            query = query.filter(TapirNickname.nickname == username)
        else:
            query = query.filter(TapirUser.email == email)

        tapir = query.one_or_none()

    if user_id:
        if not is_authorized(token, None, user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized. If you want to know your user id, use /current")
        tapir = session.query(TapirUser, TapirNickname).join(TapirNickname, TapirUser.user_id == TapirNickname.user_id).filter(TapirUser.user_id == user_id).one_or_none()

    if not tapir:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Username not found")

    user: TapirUser
    nick: TapirNickname
    user, nick = tapir
    return AccountIdentifierModel(user_id=str(user.user_id), username=nick.nickname, email=user.email)
