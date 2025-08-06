"""
Keycloak audit event processing
"""
import json
from typing import Optional, Any

from arxiv_bizlogic.fastapi_helpers import get_current_user_or_none
from fastapi import APIRouter, Depends, status, HTTPException, Request, Response
from keycloak import KeycloakAdmin, KeycloakError, KeycloakGetError
from sqlalchemy.orm import Session

from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims
from fastapi.responses import JSONResponse

from . import (get_db, verify_bearer_token, ApiToken, get_keycloak_admin, is_authenticated,
               is_authorized)  # , get_client_host
from .biz.keycloak_audit import handle_keycloak_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/keycloak", tags=["keycloak"])


@router.post('/audit', description="")
async def audit_event(
        request: Request,
        body: dict[str, Any],
        token: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token),
        session: Session = Depends(get_db),
        ) -> None:
    """
    Receives Keycloak audit events and updates the state.
    """
    if not token:
        logger.warning("Unauthorized access of Keycloak audit event")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    functions = request.app.extra['KEYCLOAK_DISPATCH_FUNCTIONS']
    handle_keycloak_event(session, body, functions)


@router.get('/user/{user_id:str}', description="")
async def get_kc_user(
        user_id: str,
        current_user: ArxivUserClaims | None = Depends(get_current_user_or_none),
        token: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token),
        kc_admin: KeycloakAdmin  = Depends(get_keycloak_admin),
        ) -> JSONResponse:
    """
    Get the user's data from Keycloak
    """
    if not is_authenticated(token, current_user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if not is_authorized(token, current_user, user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    try:
        data = {
            "user": kc_admin.get_user(user_id, user_profile_metadata=True),
            "realmRoles": kc_admin.get_realm_roles_of_user(user_id),

        }
    except KeycloakGetError as kce:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=json.loads(kce.error_message.encode("utf-8")).get('detail'))
    except KeycloakError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return JSONResponse(data)
