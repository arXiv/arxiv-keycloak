# mypy: ignore-errors
import base64
import re
from datetime import datetime, timezone
import random
import string
from typing import Optional

from arxiv_bizlogic.bizmodels.user_model import UserModel
from arxiv_bizlogic.validation.email_validation import is_valid_email
from arxiv_bizlogic.fastapi_helpers import  get_current_user_access_token
from fastapi import APIRouter, Depends, status, HTTPException, Request, Response, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session


from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.db.models import TapirUser, TapirNickname, TapirUsersPassword, OrcidIds, AuthorIds

from . import (get_current_user_or_none, get_db, get_keycloak_admin, stateless_captcha,
               get_client_host, sha256_base64_encode,
               verify_bearer_token, ApiToken, is_super_user, describe_super_user, check_authnz,
               is_authorized, get_authn_or_none)  # , get_client_host

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orcid", tags=["account"])

# Initialize ORCID service with your configuration
orcid_service = ORCID(instance="production-public-brandon")


@router.get("/verify_with_orcid/{user_id:str}")
async def verify_with_orcid(
        request: Request,
        response: Response,
        user_id: str,
        session: Session = Depends(get_db),
        current_user: ArxivUserClaims | ApiToken | None = Depends(get_authn_or_none)
):
    """
    Initiates OAuth with ORCID server.
    Corresponds to `verify_with_orcid` in the Perl code.
    """
    # Check if user already has a verified ORCID
    orcid_auth = session.query(OrcidIds).filter(and_(OrcidIds.user_id == user_id, OrcidIds.authenticated == 1)).first()

    if not orcid_auth:
        # Generate CSRF state and store it in session
        csrf_state = secrets.token_urlsafe(32)
        request.session["csrf_state"] = csrf_state

        # Redirect to ORCID authorization page
        authorize_url = orcid_service.authorize_uri(state=csrf_state)
        return RedirectResponse(url=authorize_url)
    else:
        # User already has verified ORCID
        response = RedirectResponse(url="/user")
        response.headers["X-Flash-Message"] = "Your ORCID iD is already verified!"
        return response


@app.get("/process_orcid_response")
async def process_orcid_response(
        request: Request,
        code: Optional[str] = None,
        state: Optional[str] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Processes the response from ORCID after authorization.
    Corresponds to `process_orcid_response` in the Perl code.
    """
    # Check if user already has a verified ORCID
    orcid_auth = db.query("SELECT * FROM orcid_ids WHERE user_id = :user_id AND authenticated = 1",
                          {"user_id": current_user.user_id}).first()

    if not orcid_auth:
        # Verify CSRF state
        stored_state = request.session.get("csrf_state")

        if not orcid_service.state_matches(stored_state, state):
            # Log the error
            print(
                f"Bad state, unsafe (from process_orcid_response) Received: {state}; Stored: {stored_state}; user_id: {current_user.user_id}")

            # Handle different error cases
            if len(stored_state or "") == 0 and len(state or "") > 0:
                return {"error": "Bad state, unsafe",
                        "message": "Please try again after logging in to arXiv; possible session-timeout detected."}
            elif len(stored_state or "") > 0 and len(state or "") == 0:
                return {"error": "Bad state, unsafe"}
            else:
                return {"error": "Bad state, unsafe",
                        "message": "(from process_orcid_response)"}

        # Exchange code for ORCID
        orcid = orcid_service.get_orcid(code=code)

        if orcid:
            # Update or create ORCID entry in database
            db.execute(
                """
                INSERT INTO orcid_ids (user_id, orcid, authenticated)
                VALUES (:user_id, :orcid, 1) ON CONFLICT (user_id) DO
                UPDATE
                    SET orcid = :orcid, authenticated = 1
                """,
                {"user_id": current_user.user_id, "orcid": orcid}
            )
            db.commit()

            # Redirect to user page with success message
            response = RedirectResponse(url="/user")
            response.headers[
                "X-Flash-Message"] = "Your ORCID iD has been successfully associated with your arXiv account."
            return response
        else:
            # Failed to get ORCID
            return {"error": f"Failed: {orcid_service.errstr}",
                    "message": "(from process_orcid_response)"}
    else:
        # User already has verified ORCID
        response = RedirectResponse(url="/user")
        response.headers["X-Flash-Message"] = "Your ORCID iD is already verified!"
        return response

    # Clear CSRF state regardless of outcome
    if "csrf_state" in request.session:
        del request.session["csrf_state"]


@app.get("/confirm_orcid_id")
async def confirm_orcid_id(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Primary page for ORCID iD management, linked from the user's profile.
    Corresponds to `confirm_orcid_id` in the Perl code.
    """
    # Get user's ORCID information
    orcid_info = db.query("SELECT * FROM orcid_ids WHERE user_id = :user_id",
                          {"user_id": current_user.user_id}).first()

    # In a real application, you'd render a template here
    # For this example, we'll return the data that would be passed to the template
    return {
        "user": current_user,
        "orcid_info": orcid_info
    }