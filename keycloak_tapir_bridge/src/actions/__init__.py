import re
from typing import Optional, Any
import logging

user_id_pattern = re.compile("^users/([^/]+)/")

def get_user_id_from_audit_message(data: dict) -> Optional[str]:
    matched = user_id_pattern.match(data.get("resourcePath"))
    if not matched:
        return None
    return matched.group(1)


def update_field_if_changed(obj: Any, field: str, update_with: int, logger: logging.Logger) -> bool:
    if getattr(obj, field) == update_with:
        logger.debug("Field %s is unchanged %s", field, repr(update_with))
        return False
    setattr(obj, field, update_with)
    logger.info("Field %s is changed to %s", field, repr(update_with))
    return True


def find_role_name(representation: Any) -> Optional[str]:
    if isinstance(representation, list):
        for element in representation:
            role_name = find_role_name(element)
            if role_name is not None:
                return role_name
        return None
    elif isinstance(representation, dict):
        return representation.get("name")
    else:
        return None