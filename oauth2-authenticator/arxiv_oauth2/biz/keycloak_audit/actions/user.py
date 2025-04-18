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
# def update_email(value: Any, user: domain.User, logger: logging.Logger) -> bool:
#     if user.email == value:
#         return False
#     logger.info('Update email %s --> %s', user.email, value)
#     user.email = value
#     return True


def update_email_verified(session: Session, value: Any, user_id:str, logger: logging.Logger) -> bool:
    rows_updated = session.query(TapirUser).filter(
        TapirUser.user_id == user_id,
        TapirUser.flag_email_verified != value
    ).update(
        {TapirUser.flag_email_verified: value},
        synchronize_session="evaluate"  # Synchronize the in-memory state
    )

    if rows_updated > 0:
        logger.info('Update email verified ? --> %s', str(value))

    return rows_updated > 0


# payload that can be mapped to Tapir
domain_user_updates = [
    ("username", update_username),
    ("firstName", update_first_name),
    ("lastName", update_last_name),
    # Apparently, account.update does not update email. ("email", update_email)
]

direct_user_updates = [
    ("emailVerified", update_email_verified)
]


def dispatch_user_do_update(_data: dict, representation: Any, session: Session, logger: logging.Logger) -> None:
    logger.debug(f"Entering {__name__} - r: {representation!r}")
    user_id = representation.get("id")

    changed = reduce(lambda x, y : x or y, [updater(session, representation.get(key), user_id, logger) for key, updater in direct_user_updates], False)
    if changed:
        session.commit()
        return

    user = accounts.get_user_by_id(user_id)
    changed = reduce(lambda x, y : x or y, [updater(representation.get(key), user, logger) for key, updater in domain_user_updates], False)
    if changed:
        logger.info("update user")
        accounts.update(user)
