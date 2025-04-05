"""
Keycloak audit event processing
"""
from typing import Optional, Any

from fastapi import APIRouter, Depends, status, HTTPException, Request, Response
from sqlalchemy.orm import Session

from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims

from . import (get_db, verify_bearer_token, ApiToken)  # , get_client_host
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
        raise HTTPException(status_code=401, detail="Unauthorized")

    functions = request.app.extra['KEYCLOAK_DISPATCH_FUNCTIONS']
    handle_keycloak_event(session, body, functions)
