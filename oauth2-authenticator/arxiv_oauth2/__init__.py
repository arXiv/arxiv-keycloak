"""Contains route information."""
from typing import Optional

from keycloak import KeycloakAdmin
from arxiv_bizlogic.fastapi_helpers import (
    decode_user_claims, get_current_user, get_db, get_current_user_or_none, get_hostname, get_client_host_name,
    get_client_host, get_current_user_access_token, sha256_base64_encode, datetime_to_epoch, COOKIE_ENV_NAMES
    )
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from arxiv.auth.user_claims import ArxivUserClaims

ALGORITHM = "HS256"
KEYCLOAK_ADMIN = 'KEYCLOAK_ADMIN'

def get_keycloak_admin(request: Request) -> KeycloakAdmin:
    return request.app.extra[KEYCLOAK_ADMIN]

class ApiToken(BaseModel):
    token: str

HTTPBearer_security = HTTPBearer(auto_error=False)

def verify_bearer_token(request: Request,
                        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer_security)) -> ArxivUserClaims | ApiToken | None:
    if credentials:
        token = credentials.credentials
        if not token:
            return None
        if request.app.extra['AAA_API_SECRET_KEY'] and token == request.app.extra['AAA_API_SECRET_KEY']:
            return ApiToken(token = token)
        jwt_secret = request.app.extra['JWT_SECRET']
        return decode_user_claims(token, jwt_secret)
    return None


def is_super_user(token: ArxivUserClaims | ApiToken | None) -> bool:
    return (token is not None) and (isinstance(token, ApiToken) or (isinstance(token, ArxivUserClaims) and token.is_admin))


def is_authenticated(token: ApiToken | ArxivUserClaims | None, current_user: ArxivUserClaims | None) -> bool:
    return token is not None or current_user is not None


def is_authorized(token: ApiToken | ArxivUserClaims | None, current_user: ArxivUserClaims | None, user_id: str) -> bool:
    if token:
        if isinstance(token, ApiToken):
            return True
        elif isinstance(token, ArxivUserClaims):
            current_user = token

    return (current_user is not None) and (current_user.is_admin or (str(current_user.user_id) == str(user_id)))


def check_authnz(token: ApiToken | ArxivUserClaims | None, current_user: ArxivUserClaims | None, user_id: str):
    """
    Sugar to do both authentication and authorization check
    """
    if not is_authenticated(token, current_user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    if not is_authorized(token, current_user, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")



def describe_super_user(token: ArxivUserClaims | ApiToken | None) -> str:
    if token:
        if isinstance(token, ApiToken):
            return "API"
        if isinstance(token, ArxivUserClaims):
            return "Admin user %s" % token.username
    return "Not super"


def get_authn_or_none(
    request: Request,
    cookie_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
    credentials: Optional[ArxivUserClaims | ApiToken ] = Depends(verify_bearer_token)) -> ArxivUserClaims | ApiToken | None:
    if credentials:
        return credentials
    elif cookie_user:
        return cookie_user

    return None
