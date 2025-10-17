"""Account management,

"""
import base64
import json
import re
from datetime import datetime, timezone
import random
from typing import Optional, List

import keycloak
from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient
from arxiv_bizlogic.bizmodels.user_model import UserModel
from arxiv_bizlogic.sqlalchemy_helper import update_model_fields
from arxiv_bizlogic.validation.email_validation import is_valid_email
from arxiv_bizlogic.fastapi_helpers import get_current_user_access_token, get_client_host_name, get_authn_user, \
    get_tapir_tracking_cookie
from arxiv_bizlogic.audit_event import admin_audit, AdminAudit_ChangeEmail, AdminAudit_ChangePassword, \
    AdminAudit_SetEmailVerified, AdminAudit_SuspendUser, AdminAudit_UnuspendUser, AdminAudit_SetEditUsers, \
    AdminAudit_SetEditSystem, AdminAudit_MakeModerator, AdminAudit_UnmakeModerator, AdminAudit_SetCanLock, \
    AdminAudit_ChangeDemographic
from fastapi import APIRouter, Depends, status, HTTPException, Request, Response, Query

from sqlalchemy.orm import Session
from pydantic import BaseModel
from keycloak import KeycloakAdmin
from keycloak.exceptions import (KeycloakGetError, KeycloakError)


from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.db.models import TapirUser, TapirNickname, TapirUsersPassword, OrcidIds, AuthorIds, Demographic
from arxiv.auth.legacy import passwords
from sqlalchemy.sql.functions import current_user

from . import (get_current_user_or_none, get_db, get_keycloak_admin, stateless_captcha,
               get_client_host, sha256_base64_encode,
               verify_bearer_token, ApiToken, is_super_user, describe_super_user, check_authnz,
               is_authorized, get_authn_or_none, get_arxiv_user_claims)  # , get_client_host
from .biz.account_biz import (AccountInfoModel, get_account_info,
                              AccountRegistrationError, AccountRegistrationModel, validate_password,
                              migrate_to_keycloak,
                              kc_validate_access_token, kc_send_verify_email, register_arxiv_account,
                              update_tapir_account, AccountIdentifierModel, kc_login_with_client_credential,
                              AccountUserNameBaseModel)
from .biz.cold_migration import cold_migrate
from .biz.email_history_biz import EmailHistoryBiz, EmailChangeEntry, EmailChangeRequest
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


@router.get('/{user_id:str}/profile')
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
@router.put('/{user_id:str}/profile', description="Update the user account profile for both Keycloak and user in db")
async def update_account_profile(
        user_id: str,
        data: AccountInfoModel,
        authn: Optional[ArxivUserClaims | ApiToken] = Depends(get_authn_or_none),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
) -> AccountInfoModel:
    """
    Update the profile name of a user.
    """
    assert user_id == data.id
    check_authnz(authn, None, user_id)

    # class AccountInfoModel:
    #    NOPE: username: str  # aka nickname in Tapir
    #    NOPE: email: Optional[str] = None
    #    first_name: str
    #    last_name: str
    #    suffix_name: Optional[str] = None
    #    country: Optional[str] = None
    #    affiliation: Optional[str] = None
    #    default_category: Optional[CategoryIdModel] = None
    #    NOPE: groups: Optional[List[CategoryGroup]] = None
    #    url: Optional[str] = None
    #    joined_date: Optional[int] = None
    #    NOPE: oidc_id: Optional[str] = None
    #    career_status: Optional[CAREER_STATUS] = None
    #    NOPE: tracking_cookie: Optional[str] = None
    #    NOPE: veto_status: Optional[VetoStatusEnum] = None
    #
    #    NOPE: id
    #    NOPE: email_verified: Optional[bool] = None
    #    NOPE: scopes: Optional

    existing_user = UserModel.one_user(session, user_id)
    if existing_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if data.username is not None and existing_user.username != data.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username/user id do not match")

    if data.email is not None and existing_user.email != data.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Setting email is not allowed with profile update. Use 'account/{user_id}/email'")

    if data.email_verified is not None and existing_user.flag_email_verified != data.email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Setting email is not allowed with profile update. Use 'account/{user_id}/email/verified'")

    if data.veto_status is not None and existing_user.veto_status != data.veto_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Setting email is not allowed with profile update. Use Admin API")


    updates = data.to_user_model_data(exclude_defaults=True, exclude_unset=True)
    for field in ["email", "joined_date", "tracking_cookie", "veto_status", "email_verified", "scopes"]:
        if field in updates:
            del updates[field]

    scrubbed = AccountInfoModel.from_user_model_data(updates)
    tapir_user = update_tapir_account(session, AccountInfoModel.model_validate(scrubbed))

    if not isinstance(tapir_user, TapirUser):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Tapir User")

    old_data = existing_user.model_dump()
    session.flush()

    um = UserModel.one_user(session, user_id)
    if um is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    new_data = um.model_dump()

    update_name = False
    for field in ["first_name", "last_name", "suffix_name"]:
        if old_data[field] != new_data[field]:
            update_name = True
            break

    if update_name:
        changes = {"firstName": new_data["first_name"],
                   "lastName": new_data["last_name"]}
        kc_admin.update_user(user_id=str(tapir_user.user_id), payload=changes)
        changes['suffix_name'] = new_data['suffix_name']
        if isinstance(authn, ArxivUserClaims):
            current_user:ArxivUserClaims = authn
            if current_user.is_admin:
                admin_audit(
                    session,
                    AdminAudit_ChangeDemographic(
                        admin_id=str(current_user.user_id),
                        affected_user=str(um.id),
                        session_id=str(current_user.tapir_session_id),
                        remote_ip=remote_ip,
                        remote_hostname=remote_hostname,
                        tracking_cookie=um.tracking_cookie,
                        data={
                            "before": {
                                "first_name": old_data["first_name"],
                                "last_name": old_data["last_name"],
                                "suffix_name": old_data["suffix_name"],
                            },
                            "after": {
                                "first_name": new_data.get("first_name", old_data["first_name"]),
                                "last_name": new_data.get("last_name", old_data["last_name"]),
                                "suffix_name": new_data.get("suffix_name", old_data["suffix_name"]),
                            }
                        }
                    )
                )

    session.commit()
    return reply_account_info(session, str(tapir_user.user_id))


class AccountUserNameUpdateModel(AccountUserNameBaseModel):
    comment: Optional[str] = None

#
# Profile update and registering user is VERY similar. It is essentially upsert. At some point, I should think
# about refactor these two.
@router.put('/{user_id:str}/name', description="Update the user account profile for both Keycloak and user in db")
async def update_user_name(
        request: Request,
        user_id: str,
        data: AccountUserNameUpdateModel,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        remote_ip:Optional[str] = Depends(get_client_host),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
) -> AccountInfoModel:
    """
    Update the profile name of a user.
    """
    check_authnz(current_user, None, user_id)
    existing_user = UserModel.one_user(session, user_id)
    if existing_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    kc_user = None
    try:
        kc_user = kc_admin.get_user(user_id)
    except KeycloakGetError as kce:
        logger.info(f"Failed to get user {user_id} from Keycloak: {kce}")
        pass

    if kc_user is None:
        kc_user = cold_migrate(kc_admin, session, user_id, request.app.extra['ARXIV_USER_SECRET'],
                               email_verified=existing_user.flag_email_verified)

    changed = False
    name_changed = False

    if data.username is not None and existing_user.username != data.username:
        changed = True
        nick: TapirNickname | None = session.query(TapirNickname).filter(TapirNickname.user_id == user_id).one_or_none()
        if nick is None:
            nick =  TapirNickname(nickname=data.username, user_id=user_id, user_seq=0,
                                  flag_valid=1,
                                  role=0,
                                  policy=0,
                                  flag_primary=1)
            session.add(nick)
            session.flush()
            session.refresh(nick)
        else:
            nick.nickname = data.username

        kc_admin.update_user(user_id=user_id, payload={"username": data.username})

    if (data.first_name is not None and existing_user.first_name != data.first_name) or \
            (data.last_name is not None and existing_user.last_name != data.last_name):
        changed = True
        name_changed = True
        kc_admin.update_user(user_id=user_id, payload={"firstName": data.first_name, "lastName": data.last_name})
        tapir_user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
        if tapir_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        update_model_fields(
            session,
            TapirUser,
            data.model_dump(),
            {'first_name', 'last_name'},
            primary_key_field="user_id",
            primary_key_value=user_id
        )


    if data.suffix_name is not None and existing_user.suffix_name != data.suffix_name:
        changed = True
        name_changed = True
        tapir_user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
        if tapir_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        update_model_fields(
            session,
            TapirUser,
            data.model_dump(),
            {'suffix_name'},
            primary_key_field="user_id",
            primary_key_value=user_id
        )

    if name_changed:
        # Log the name change
        admin_audit(
            session,
            AdminAudit_ChangeDemographic(
                admin_id=str(current_user.user_id),
                affected_user=str(user_id),
                session_id=str(current_user.tapir_session_id),
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                data={
                    "before": {
                        "first_name": existing_user.first_name,
                        "last_name": existing_user.last_name,
                        "suffix_name": existing_user.suffix_name,
                    },
                    "after": {
                        "first_name": data.first_name,
                        "last_name": data.last_name,
                        "suffix_name": data.suffix_name,
                    }
                }
            )
        )

    if changed:
        session.commit()

    return reply_account_info(session, str(user_id))



# See profile update comment.
@router.post('/register',
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

    if not registration.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email is required")
    if not registration.username or not registration.username.strip():
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


@router.get("/register")
def get_register(request: Request) -> CaptchaTokenReplyModel:
    return get_captcha_token(request)


class EmailModel(BaseModel):
    email: str


@router.post("/{user_id:str}/email/verify", description="Request to send verify email")
def request_email_verify(
        request: Request,
        user_id: str,
        body: EmailModel,
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.email == body.email).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    kc_send_verify_email(kc_admin, str(user_id), force_verify=True)
    return


class EmailVerifiedStatus(BaseModel):
    email_verified: bool
    user_id: Optional[str] = None

@router.get("/email/verified", description="Is the email verified for this user?")
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


@router.get("/{user_id:str}/email/verified", description="Is the email verified for this user?")
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


@router.put("/{user_id:str}/email/verified", description="Set the email verified status")
def set_email_verified_status(
        user_id: str,
        body: EmailVerifiedStatus,
        authed_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: str = Depends(get_client_host),
        remote_hostname: str = Depends(get_client_host_name),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
) -> EmailVerifiedStatus:
    if body.user_id:
        if not body.user_id == user_id:
            logger.warning(f"User ID {user_id} does not match the expected ID {body.user_id}")
        assert user_id == body.user_id, "user_id == body.user_id"
    check_authnz(authed_user, None, user_id)
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

    email_verified = 1 if body.email_verified else 0

    if authed_user.is_admin:
        if user.flag_email_verified != email_verified:
            logger.info(f"User {user_id} email flag being updated to {email_verified!r}")
            user.flag_email_verified = email_verified
            admin_audit(
                session,
                AdminAudit_SetEmailVerified(
                    str(authed_user.user_id),
                    str(user_id),
                    str(authed_user.tapir_session_id),
                    body.email_verified,
                    remote_ip=remote_ip,
                    remote_hostname=remote_hostname,
                ),
            )
        else:
            logger.info(f"User {user_id} email flag no-change as {email_verified!r}")
    else:
        biz: EmailHistoryBiz = EmailHistoryBiz(session, user_id=user_id)
        if not biz.email_verified(remote_ip=remote_ip, remote_host=remote_hostname,
                                  session_id=str(authed_user.tapir_session_id)):

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is not verified.")
        user.flag_email_verified = email_verified

    if kc_user_id:
        try:
            kc_admin.user_logout(kc_user_id)
        except keycloak.exceptions.KeycloakPostError as exc:
            # if 404, user hasn't migrated to Keycloak yet.
            # Update Tapir entry and move on
            if  exc.response_code != 404:
                logger.error(f"Error logging out user {user_id}: {exc!r}")
                raise

    session.commit()
    return EmailVerifiedStatus(email_verified=bool(user.flag_email_verified), user_id = user_id)


class EmailUpdateModel(EmailModel):
    new_email: str
    email_verified: Optional[bool] = None  # This is only useful when the admin wants to set the verify status
    comment: Optional[str] = None


@router.put("/{user_id:str}/email", description="Request to change email", responses={
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
        user_id: str,
        body: EmailUpdateModel,
        session: Session = Depends(get_db),
        remote_ip: str = Depends(get_client_host),
        remote_hostname: str = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        authn_user: ArxivUserClaims = Depends(get_authn_user),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
) -> UserModel:
    #
    # Case 1 - Admin changes her own
    #    Let her change the email? Most likely yes. She should be able to change anyone's email -> but
    #    leaves audit record.
    #
    # Case 2 - Admin changes someone else's email
    #    Make the change.
    #
    # Case 3 - User changes hre own email
    #    Ask Keycloak to update the email, but not update the tapir email.
    #    This is done with the audit event.
    #

    # All cases, you cannot change email to someone else's email.
    #
    check_authnz(authn_user, None, user_id)

    if not is_valid_email(body.new_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email is invalid.")

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Old email does not exist")

    other_user: TapirUser | None = session.query(TapirUser).filter(TapirUser.email == body.new_email).one_or_none()
    if other_user:
        if str(other_user.user_id) != str(user_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="New email {} is used by other user.".format(body.new_email))
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
    if is_super_user(authn_user):
        # admin change email
        # We can short circuit the rate limit, etc.
        email_verified = True if body.email_verified is None else body.email_verified
        old_email = user.email[:]

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

        claims = get_arxiv_user_claims(authn_user)
        tapir_session_id = None
        if claims:
            tapir_session_id = claims.tapir_session_id

        # add audit record
        admin_audit(
            session,
            AdminAudit_ChangeEmail(
                authn_user.user_id,
                user_id,
                tapir_session_id,
                email=body.new_email,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                comment='' if body.comment is None else body.comment,
            ))
        logger.info("User %s email set by admin %s from %s to %s", user_id, authn_user.user_id, old_email, body.new_email)

        # Audit the email verified
        if not authn_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Authorized user has no user ID. ")

        admin_audit(
            session,
            AdminAudit_SetEmailVerified(
                authn_user.user_id,
                user_id,
                tapir_session_id,
                email_verified,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                comment='' if body.comment is None else body.comment,
            ))
        logger.info("User %s email verified set by admin %s to %s", user_id, authn_user.user_id, repr(email_verified))

        if not email_verified and kc_user:
            kc_send_verify_email(kc_admin, kc_user["id"], force_verify=True)

        session.commit()
        return UserModel.one_user(session, user_id)


    # Case 3 - Normal user change email
    if biz.is_rate_exceeded():
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many email change request.")

    # user.email = body.new_email
    # user.flag_email_verified = False

    if not kc_user:
        # Force the issue, and create the account
        client_secret = request.app.extra['ARXIV_USER_SECRET']
        kc_user = cold_migrate(kc_admin, session, user_id, client_secret)

    # KC has the new email and is set to not verified.
    try:
        kc_admin.update_user(kc_user["id"], payload={"email": body.new_email, "emailVerified": False})

    except KeycloakError as e:
        logger.error("Updating Keycloak user failed.", exc_info=e)
        session.rollback()
        detail = "Account service not available at the moment. Please contact help@arxiv.org: " + str(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    starter = EmailChangeRequest(
        user_id=user_id,
        new_email=body.new_email,
        remote_ip=remote_ip,
        remote_hostname=remote_hostname,
        email=user.email,
        tracking_cookie=tracking_cookie,
        tapir_session_id=authn_user.tapir_session_id,
    )
    _new_token = biz.add_email_change_request(starter)
    session.commit()

    if kc_user:
        # Sends the verify request email
        kc_send_verify_email(kc_admin, kc_user["id"], force_verify=True)

    return UserModel.one_user(session, user_id)


@router.get("/{user_id:str}/email/history", description="Get the past email history")
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
        _end = len(history.change_history)

    response.headers['X-Total-Count'] = str(len(history.change_history))
    return history.change_history[_start:_end]


class PasswordUpdateModel(BaseModel):
    old_password: str
    new_password: str


@router.put('/{user_id:str}/password', description="Update user password")
async def change_user_password(
        request: Request,
        user_id: str,
        data: PasswordUpdateModel,
        authn_user: ArxivUserClaims = Depends(get_authn_user),
        kc_access_token: Optional[str] = Depends( get_current_user_access_token),
        remote_ip: str = Depends(get_client_host),
        remote_hostname: str = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    """
    Change user password
    """
    logger.debug("User password changed request. Current %s, data %s, Old password %s, new password %s",
                 authn_user.user_id if authn_user else "No User", user_id,
                 sha256_base64_encode(data.old_password), sha256_base64_encode(data.new_password))

    check_authnz(authn_user, None, user_id)

    if len(data.old_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is invalid")

    if not validate_password(data.new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password is invalid")

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    nick: TapirNickname | None = session.query(TapirNickname).filter(
        TapirNickname.user_id == user_id).one_or_none()
    if nick is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    pwd: TapirUsersPassword | None = session.query(TapirUsersPassword).filter(
        TapirUsersPassword.user_id == user_id).one_or_none()
    if pwd is None:
        pwd = TapirUsersPassword(
            user_id=user_id,
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
    if kc_access_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Stale access. Please log out/login again.")

    if not await kc_validate_access_token(kc_admin, idp, kc_access_token):
        if authn_user.user_id == user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Stale access. Please log out/login again.")
        if not authn_user.is_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Stale access. Please log out/login again.")

    kc_user = None
    try:
        kc_user = kc_admin.get_user(user_id)
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

    if authn_user.is_admin and authn_user.user_id != user_id:
        if not authn_user.tapir_session_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tapir session is required.")

        tsid = str(authn_user.tapir_session_id)
        admin_audit(
            session,
            AdminAudit_ChangePassword(
                authn_user.user_id,
                user_id,
                tsid,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
            ), # obv. no payload
        )

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


@router.post('/password/reset', description="Reset user password",
             status_code=status.HTTP_201_CREATED)
async def reset_user_password(
        request: Request,
        body: PasswordResetRequest,
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        session: Session = Depends(get_db),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    """
    Make KC to send a password reset request.

    NOTE: Nothing to remember but we may have to rate-limit.
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


@router.get('/identifier')
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
                                  orcid=orcid.orcid if orcid else None,
                                  author_id=xauth.author_id if xauth else None)


#
# ORCID comes from logging into ORCID and get the ORCID back. This is done elsewhere atm.
#
class OrcidUpdateModel(BaseModel):
    user_id: str
    orcid: Optional[str] = None
    orcid_auth: Optional[str] = None
    authenticated: bool

@router.put("/orcid", description="Update ORCID", responses={
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


@router.put("/author_id", description="Update AUTHOR_ID", responses={
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
                author_id.author_id = body.author_id if body.author_id else ""
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
class UserAuthorizationModel(BaseModel):
    deleted: Optional[bool] = None #
    administrator: Optional[bool] = None # Administrator
    approved: Optional[bool] = None # Approved
    suspend: Optional[bool] = None  # Banned
    can_lock: Optional[bool] = None # CanLock
    moderator: Optional[bool] = None # Moderator 
    owner: Optional[bool] = None # Owner (edit_system)
    comment: Optional[str] = None
    # maybe add more


@router.put("/{user_id:str}/authorization",
            description="Update User authorization",
            responses={
    status.HTTP_400_BAD_REQUEST: {
        "description": "Request data is not valid",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid request data"}
            }
        },
    },
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Not logged in",
        "content": {
            "application/json": {
                "example": {"detail": "Not authenticated"}
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        "description": "Forbidden - not allowed to change the ORCID data",
        "content": {
            "application/json": {
                "example": {"detail": "Not authorized to set the ORCID data"}
            }
        },
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "description": "Error while updating Keycloak",
        "content": {
            "application/json": {
                "example": {"detail": "Could not update Keycloak"}
            }
        },
    },
})
def update_user_authorization(
        request: Request,
        user_id: str,
        body: UserAuthorizationModel,
        session: Session = Depends(get_db),
        admin_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: str = Depends(get_client_host),
        remote_hostname: str = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
) -> UserModel:
    check_authnz(admin_user, None, user_id)
    idp: ArxivOidcIdpClient = request.app.extra["idp"]

    user: UserModel | None = UserModel.one_user(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} does not exist")

    tapir_user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if not tapir_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} does not exist")

    # demographic: Demographic | None = session.query(Demographic).filter(Demographic.user_id == user_id).one_or_none()

    valid_request = False
    if body.deleted is not None:
        valid_request = True
        deleted = 1 if body.deleted else 0
        if tapir_user.flag_deleted != deleted:
            tapir_user.flag_deleted = deleted
            # Add audit trail for user deletion/undeletion
            # Note: Using suspend audit events as there are no specific delete audit events
            audit = AdminAudit_SuspendUser(
                admin_user.user_id,
                user_id,
                admin_user.tapir_session_id,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                comment=f"{'Deleted' if body.deleted else 'Undeleted'} user. {body.comment if body.comment else ''}"
            ) if body.deleted else AdminAudit_UnuspendUser(
                admin_user.user_id,
                user_id,
                admin_user.tapir_session_id,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                comment=f"Undeleted user. {body.comment if body.comment else ''}"
            )
            admin_audit(session, audit)


    if body.suspend is not None:
        valid_request = True
        banned = 1 if body.suspend else 0
        if tapir_user.flag_banned != banned:
            tapir_user.flag_banned = banned
            audit = AdminAudit_SuspendUser(
                admin_user.user_id,
                user_id,
                admin_user.tapir_session_id,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                comment=body.comment if body.comment else ''
            ) if not body.suspend else AdminAudit_UnuspendUser(
                admin_user.user_id,
                user_id,
                admin_user.tapir_session_id,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                comment=body.comment if body.comment else '')
            admin_audit(session, audit)


    if body.administrator is not None:
        valid_request = True
        admin_flag = 1 if body.administrator else 0
        if tapir_user.flag_edit_users != admin_flag:
            tapir_user.flag_edit_users = admin_flag
            # Create audit event for administrator role change
            audit = AdminAudit_SetEditUsers(
                str(admin_user.user_id),
                str(user_id),
                str(admin_user.tapir_session_id),
                body.administrator,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                comment=f"{'Granted' if body.administrator else 'Revoked'} administrator role. {body.comment if body.comment else ''}"
            )
            admin_audit(session, audit)


    if body.owner is not None:
        valid_request = True
        owner_flag = 1 if body.owner else 0
        if tapir_user.flag_edit_system != owner_flag:
            tapir_user.flag_edit_system = owner_flag
            # Create audit event for owner role change
            audit = AdminAudit_SetEditSystem(
                str(admin_user.user_id),
                str(user_id),
                str(admin_user.tapir_session_id),
                body.owner,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                comment=f"{'Granted' if body.owner else 'Revoked'} owner role. {body.comment if body.comment else ''}"
            )
            admin_audit(session, audit)


    if body.can_lock is not None:
        valid_request = True
        can_lock_flag = 1 if body.can_lock else 0
        if tapir_user.flag_can_lock != can_lock_flag:
            tapir_user.flag_can_lock = can_lock_flag
            # Create audit event for can_lock role change
            audit = AdminAudit_SetCanLock(
                str(admin_user.user_id),
                str(user_id),
                str(admin_user.tapir_session_id),
                body.can_lock,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                comment=f"{'Granted' if body.can_lock else 'Revoked'} can_lock privilege. {body.comment if body.comment else ''}"
            )
            admin_audit(session, audit)


    if body.approved is not None:
        valid_request = True
        approved_flag = 1 if body.approved else 0
        if tapir_user.flag_approved != approved_flag:
            tapir_user.flag_approved = approved_flag
            # No audit event needed for approved role per user request


    if body.moderator is not None:
        valid_request = True
        moderator_flag = 1 if body.moderator else 0
        # Check if TapirUser has flag_moderator field, if not we might need to handle differently
        if hasattr(tapir_user, 'flag_moderator'):
            if tapir_user.flag_moderator != moderator_flag:
                tapir_user.flag_moderator = moderator_flag
                # Create audit event for moderator role change
                audit = AdminAudit_MakeModerator(
                    str(admin_user.user_id),
                    str(user_id), 
                    str(admin_user.tapir_session_id),
                    category="general",  # Default category for general moderator role
                    remote_ip=remote_ip,
                    remote_hostname=remote_hostname,
                    tracking_cookie=tracking_cookie,
                    comment=f"{'Granted' if body.moderator else 'Revoked'} moderator role. {body.comment if body.comment else ''}"
                ) if body.moderator else AdminAudit_UnmakeModerator(
                    str(admin_user.user_id),
                    str(user_id),
                    str(admin_user.tapir_session_id),
                    category="general",  # Default category for general moderator role
                    remote_ip=remote_ip,
                    remote_hostname=remote_hostname,
                    tracking_cookie=tracking_cookie,
                    comment=f"Revoked moderator role. {body.comment if body.comment else ''}"
                )
                admin_audit(session, audit)


    if session.is_modified(tapir_user):
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
                logger.info(f"{'Enabled' if user_enabled else 'Disabled'} user {user_id} in Keycloak")

                # Handle administrator role changes
                if body.administrator is not None:
                    try:
                        # Get the Administrator role
                        admin_role = kc_admin.get_realm_role("Administrator")
                        
                        if body.administrator:
                            # Add Administrator role
                            kc_admin.assign_realm_roles(user_id, [admin_role])
                            logger.info(f"Granted Administrator role to user {user_id} in Keycloak")
                        else:
                            # Remove Administrator role  
                            kc_admin.delete_realm_roles_of_user(user_id, [admin_role])
                            logger.info(f"Revoked Administrator role from user {user_id} in Keycloak")
                        
                        
                    except Exception as role_e:
                        logger.error(f"Failed to update Administrator role for user {user_id}: {str(role_e)}")
                        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                            detail=f"Failed to update Administrator role: {str(role_e)}")

                # Handle other role changes
                role_mappings = [
                    ('owner', 'Owner', body.owner),
                    ('can_lock', 'CanLock', body.can_lock),
                    ('approved', 'Approved', body.approved),
                    ('moderator', 'Moderator', body.moderator)
                ]
                
                for role_name, keycloak_role, role_value in role_mappings:
                    if role_value is not None:
                        try:
                            # Get the role from Keycloak
                            role = kc_admin.get_realm_role(keycloak_role)
                            
                            if role_value:
                                # Add role
                                kc_admin.assign_realm_roles(user_id, [role])
                                logger.info(f"Granted {keycloak_role} role to user {user_id} in Keycloak")
                            else:
                                # Remove role
                                kc_admin.delete_realm_roles_of_user(user_id, [role])
                                logger.info(f"Revoked {keycloak_role} role from user {user_id} in Keycloak")
                                
                        except Exception as role_e:
                            logger.error(f"Failed to update {keycloak_role} role for user {user_id}: {str(role_e)}")
                            # Don't fail the entire operation for individual role failures
                            # raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            #                     detail=f"Failed to update {keycloak_role} role: {str(role_e)}")

            except Exception as e:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                    detail=f"Failed to update Keycloak: {str(e)}")
                                    
        try:
            kc_admin.user_logout(user_id)
            logger.info(f"Invalidated Keycloak sessions for user {user_id} due to authorization changes")
        except Exception as logout_e:
            logger.warning(f"Failed to invalidate sessions for user {user_id}: {str(logout_e)}")

        session.commit()

    if not valid_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

    return UserModel.one_user(session, user_id)
