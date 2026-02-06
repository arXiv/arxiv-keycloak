"""
Parse user's audit event and update USER resource

ex:
{
  "id" : "8b4aaf3b-14ee-4b1d-b532-79d7d178d4b8",
  "time" : 1738005796557,
  "realmId" : "c35229b5-75cf-42d4-aa83-976a0609b73d",
  "realmName" : "arxiv",
  "authDetails" : {
    "realmId" : "dc5d84a5-348f-4956-a7b9-e6a74a35cc66",
    "realmName" : "master",
    "clientId" : "1e15cfc1-4d87-465a-a369-6e70af387895",
    "userId" : "ce43077d-2b2b-4090-996f-d11757b32e83",
    "ipAddress" : "0:0:0:0:0:0:0:1"
  },
  "resourceType" : "USER",
  "operationType" : "UPDATE",
  "resourcePath" : "users/1212",
  "representation" : "{\"id\":\"1212\",\"username\":\"reader\",\"firstName\":\"Random\",\"lastName\":\"Reader\",\"email\":\"no-mail-randomreader@example.com\",\"emailVerified\":false,\"attributes\":{\"tracking_cookie\":[\"xyz\"],\"joined_date\":[\"2013-11-11T15:56:29Z\"],\"joined_ip_num\":[\"dedicated\"],\"share\":[\"FirstName\",\"LastName\",\"Email\"]},\"createdTimestamp\":1738005757855,\"enabled\":true,\"totp\":false,\"disableableCredentialTypes\":[],\"requiredActions\":[],\"notBefore\":0,\"access\":{\"manageGroupMembership\":true,\"view\":true,\"mapRoles\":true,\"impersonate\":true,\"manage\":true}}",
  "resourceTypeAsString" : "USER"
}

"""
import logging
from functools import reduce
from typing import Any

from sqlalchemy.orm import Session
# from sqlalchemy import and_

from arxiv.db.models import TapirUser
from arxiv.auth.legacy import accounts
from arxiv.auth import domain

from ...email_history_biz import EmailHistoryBiz, get_last_tapir_session


def update_username(value: Any, user: domain.User, logger: logging.Logger) -> bool:
    if value == user.username:
        return False
    logger.info('Update username %s --> %s', user.username, value)
    user.username = value
    return True

def update_first_name(value: Any, user: domain.User, logger: logging.Logger) -> bool:
    if user.name is None:
        user.name = domain.UserFullName(forename=value, surname="")
        return True

    if user.name.forename == value:
        return False
    logger.info('Update first name %s --> %s', user.name.forename, value)
    user.name.forename = value
    return True

def update_last_name(value: Any, user: domain.User, logger: logging.Logger) -> bool:
    if user.name is None:
        user.name = domain.UserFullName(forename="", surname=value)
        return True

    if user.name.surname == value:
        return False
    logger.info('Update last name %s --> %s', user.name.surname, value)
    user.name.surname = value
    return True


# Updating email requires a bit more business logic, apparently
# def update_email(session: Session, value: Any, user_id:str, logger: logging.Logger) -> bool:
#     rows_updated = session.query(TapirUser).filter(
#         TapirUser.user_id == user_id,
#         TapirUser.flag_email_verified != value
#     ).update(
#         {TapirUser.flag_email_verified: value},
#         synchronize_session="evaluate"  # Synchronize the in-memory state
#     )
#
#     if user.email == value:
#         return False
#     logger.info('Update email %s --> %s', user.email, value)
#     user.email = value
#     return True


def update_email_verified(session: Session, representation: dict, key: str, user_id: str, logger: logging.Logger) -> bool:
    # There are 3 scenarios to get here.
    # 1. (not here) User responds to the verification email. -> dispatch_user_do_verify_email function
    #
    # 2. Admin sets the email to verified via admin console
    # 3. Go into Keycloak console and set the email to verified.
    #
    # This is for 2, 3
    value = representation.get(key)

    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if user is not None:
        if user.flag_email_verified != value:
            logger.info(f'user {user_id} email verify is set to {value!r}')
            user.flag_email_verified = value
            session.commit()
        else:
            logger.info(f'user {user_id} email verify is {value!r} and unchanged')
            pass
    else:
        logger.warning(f'user {user_id} does not exist in TapirUser table.')


# payload that can be mapped to Tapir
domain_user_updates = [
    ("username", update_username),
    ("firstName", update_first_name),
    ("lastName", update_last_name),
    # Apparently, account.update does not update email. ("email", update_email)
]

direct_user_updates = [
    ("emailVerified", update_email_verified),
    # ("email", update_email)
]


def dispatch_user_do_update(_data: dict, representation: Any, session: Session, logger: logging.Logger) -> None:
    logger.debug(f"Entering {__name__} - r: {representation!r}")
    user_id = representation.get("id")

    changed = reduce(lambda x, y : x or y, [updater(session, representation, key, user_id, logger) for key, updater in direct_user_updates], False)
    if changed:
        session.commit()
        return

    user = accounts.get_user_by_id(user_id)
    changed = reduce(lambda x, y : x or y, [updater(representation.get(key), user, logger) for key, updater in domain_user_updates], False)
    if changed:
        logger.info(f"update user {representation!r}")
        accounts.update(user)


def dispatch_user_do_verify_email(data: dict, representation: Any, session: Session, logger: logging.Logger) -> None:
    # There are 3 scenarios to get here.
    # 1. User responds to the verification email.
    # (not here) 2. Admin sets the email to verified via admin console
    # (not here) 3. Go into Keycloak console and set the email to verified. -> This is a separaete function
    #
    # event example
    # {
    #     "id": "3ebfbf2e-3847-4273-a083-25c9592a4d02",
    #     "time": 1755118023735,
    #     "type": "VERIFY_EMAIL",
    #     "realmId": "e41ca50b-f7f2-40e0-bee9-6c9a972d49de",
    #     "realmName": "arxiv",
    #     "clientId": "arxiv-user",
    #     "userId": "913436",
    #     "ipAddress": "127.0.0.1",
    #     "details": {
    #         "auth_method": "openid-connect",
    #         "token_id": "d413779e-8dc7-4e52-a65a-46682d6f2857",
    #         "action": "verify-email",
    #         "response_type": "code",
    #         "redirect_uri": "http://localhost.arxiv.org:5100/aaa/callback",
    #         "remember_me": "true",
    #         "code_id": "158aff32-51ba-4e01-86f5-dfdaf1044c5c",
    #         "email": "ntai6@cleanwinner.com",
    #         "response_mode": "query",
    #         "username": "ntai"
    #     }
    # }

    logger.debug(f"Entering dispatch_user_do_verify_email")
    user_id = data.get("userId")
    client_id = data.get("clientId")

    if client_id != "arxiv-user":
        logger.debug(f"client id {client_id} is not expected. bailing out")
        return

    biz = EmailHistoryBiz(session, user_id)
    last_session = get_last_tapir_session(session, user_id)
    details = data.get("details", {})
    new_email = details.get("email")
    if new_email is None:
        logger.warning(f"email is not found in details: {details!r}")
        return
    if last_session:
        if biz.email_verified(session_id=str(last_session.session_id),
            remote_ip=data.get("ipAddress"),
            new_email=new_email,
            ):
            logger.info(f"email {new_email} is verified for user {user_id}")
        else:
            logger.info(f"email {new_email} is NOT verified for user {user_id}")
            pass
        pass


    session.commit()
