"""
Parse the role mapping audit events and set the role flags in Tapir tables.
"""
import logging

from arxiv.db.models import TapirUser # , TapirPolicyClass
from sqlalchemy.orm import Session
from arxiv.auth.legacy.exceptions import NoSuchUser
from typing import Any


role_name_to_field = {
    "AllowTexProduced": "flag_allow_tex_produced",
    "Owner": "flag_edit_system",
    "Administrator": "flag_edit_users",
    "Approved": "flag_approved",
    "Banned": "flag_banned",
    "CanLock": "flag_can_lock"
}

from .. import get_user_id_from_audit_message, update_field_if_changed, find_role_name


def _update_realm_role_mapping(data: dict, representation: Any, value: int, session: Session, logger: logging.Logger) -> None:
    user_id = get_user_id_from_audit_message(data)
    if not user_id:
        logger.warning("Unable to find user ID '%s'", repr(data))
        raise NoSuchUser()

    user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if user is None:
        logger.warning("Unable to find user '%s' in TapirUser", user_id)
        raise NoSuchUser()
    changed = False
    if isinstance(representation, list):
        for role_change in representation:
            role_name = find_role_name(role_change)
            if role_name is None:
                logger.warning("Unable to find role name for role mapping in '%s'", repr(representation))
                return

            if role_name not in role_name_to_field:
                logger.debug("role name %s is not in use", role_name)
                return

            if update_field_if_changed(user, role_name_to_field[role_name], value, logger):
                changed = True
                logger.info("User %s: role %s is set to %s", user_id, role_name, str(value))
            else:
                logger.info("User %s: role %s is unchanged as %s", user_id, role_name, str(value))
                pass
            pass
        pass
    else:
        logger.error("User %s: unexpected payload %s", user_id, repr(representation))
        pass

    if changed:
        session.commit()

def dispatch_realm_role_mapping_do_create(data: dict, representation: Any, session: Session, logger: logging.Logger):
    _update_realm_role_mapping(data, representation, 1, session, logger)


def dispatch_realm_role_mapping_do_delete(data: dict, representation: Any, session: Session, logger: logging.Logger):
    _update_realm_role_mapping(data, representation, 0, session, logger)
