import json
import re
from fastapi import status
from fastapi.exceptions import HTTPException
from typing import Optional, Any, Dict, Callable
import logging
from arxiv.auth.legacy.exceptions import NoSuchUser
import importlib
import os
import inspect
from sqlalchemy.orm import Session

user_id_pattern = re.compile("^users/([^/]+)/")

def get_user_id_from_audit_message(data: dict) -> Optional[str]:
    matched = user_id_pattern.match(data.get("resourcePath", ""))
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


def get_keycloak_dispatch_functions() -> Dict[str, Callable[..., None]]:
    # Dictionary to store dispatch functions
    logger = logging.getLogger(__name__)
    dispatch_functions: Dict[str, Callable[..., None]] = {}
    directory = os.path.dirname(__file__)

    # Get the list of Python files in the actions directory
    for filename in os.listdir(os.path.join(directory, "actions")):
        if filename.endswith(".py") and not filename.startswith("__"):
            # Get the module name
            module_name = filename[:-3]

            # Import the module dynamically
            try:
                module = importlib.import_module(f"arxiv_oauth2.biz.keycloak_audit.actions.{module_name}")

                # Inspect the module to find functions starting with "dispatch_"
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if name.startswith("dispatch_"):
                        dispatch_functions[name] = func
            except Exception as exc:
                logger.warning("importing of dispatch failed: %s", filename, exc_info=exc)
                pass

    return dispatch_functions


def handle_keycloak_event(session: Session, data: dict[str, Any], dispatch_functions: Dict[str, Callable]) -> None:
    """Keycloak event handler
    the event looks like
    {
        "id" : "1e2abec5-bf62-42b1-a000-8773cf177fab",
        "time" : 1727796557187,
        "realmId" : "e9b31419-5843-4014-9bd1-f05a2df3b96b",
        "realmName" : "arxiv",
        "authDetails" : {
            "realmId" : "e34fe449-a841-4c0c-887d-a123a565d315",
            "realmName" : "master",
            "clientId" : "350cacca-500f-41a5-a1a2-ab57a0df45b4",
            "userId" : "84e2038c-3726-463d-a131-0d09c08c0829",
            "ipAddress" : "172.17.0.1"
        },
        "resourceType" : "REALM_ROLE_MAPPING",
        "operationType" : "DELETE",
        "resourcePath" : "users/28396986-0c90-42be-b39b-73f4714debaf/role-mappings/realm",
        "representation" : "[{\"id\":\"e6350ae5-2083-46ae-bed8-ba72e3c9dfcf\",\"name\":\"Test Role\",\"composite\":false}]",
        "resourceTypeAsString" : "REALM_ROLE_MAPPING"
    }

    Some events may not be interesting to Tapir
    """
    logger = logging.getLogger(__name__)

    # If this is not for arxiv realm, I don't care so eat it up and move on
    realm_name = data.get("realmName")
    if realm_name != "arxiv":
        logger.info("Not for arxiv - ack %s", data.get('id', '<no-id>'))
        return

    #
    event_type = data.get("type", "").lower()
    if event_type in ["login", "logout"]:
        resource_type = "authn"
        op = event_type
    else:
        resource_type = data.get("resourceType", "no_resource").lower()
        op = data.get("operationType", "").lower()
    dispatch_name = f"dispatch_{resource_type}_do_{op}"
    dispatch = dispatch_functions.get(dispatch_name)
    representation = json.loads(data.get("representation", "{}"))
    if dispatch is not None:
        try:
            logger.debug("dispatch %s", dispatch_name)
            dispatch(data, representation, session, logger)
        except NoSuchUser:
            logger.warning("No such user: %s", repr(data))
            pass
        except Exception as exc:
            logger.warning("Error: %s", repr(data), exc_info=exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=repr(exc))
    else:
        logger.info("dispatch %s does not exist: %s", dispatch_name, repr(data))

    logger.info("ack %s", data.get('id', '<no-id>'))
    return
