from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.auth.transport import requests
from google.oauth2 import id_token
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_security_ = HTTPBearer()

async def verify_gcp_oidc_token(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(_security_)
) -> dict:
    """
    Verify GCP OIDC token from Cloud Scheduler or Cloud Functions.

    Args:
        request: FastAPI request object to access app state
        credentials: The Bearer token from Authorization header

    Returns:
        dict: The decoded and verified token payload

    Raises:
        HTTPException: If token is invalid or verification fails
    """
    token = credentials.credentials

    # Get expected audience from app state
    try:
        expected_audience = request.app.extra['GCP_SERVICE_REQUEST_ENDPOINT']
    except KeyError:
        logger.error("GCP_SERVICE_REQUEST_ENDPOINT not configured in app.extra")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: GCP_SERVICE_REQUEST_ENDPOINT not set"
        )

    try:
        # Verify the token and decode it
        # This validates:
        # - Token signature using Google's public keys
        # - Token expiration
        # - Token issuer (accounts.google.com or https://accounts.google.com)
        decoded_token = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            audience=expected_audience
        )

        #logger.info(f"Token verified for email: {decoded_token.get('email')}")
        #logger.info(f"Token issuer: {decoded_token.get('iss')}")
        #logger.info(f"Token subject: {decoded_token.get('sub')}")

        # Additional validation: check service account email if needed
        email = decoded_token.get('email')
        expected_sa = request.app.extra['GCP_SERVICE_REQUEST_SA']

        # Uncomment to enforce specific service account
        if email != expected_sa:
            raise HTTPException(
                status_code=403,
                detail=f"Token from unauthorized service account: {email}"
            )
        return decoded_token

    except ValueError as e:
        # Token is invalid
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )
