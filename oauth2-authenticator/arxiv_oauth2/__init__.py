"""Contains route information."""

from keycloak import KeycloakAdmin
from arxiv_bizlogic.fastapi_helpers import *
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

ALGORITHM = "HS256"
KEYCLOAK_ADMIN = 'KEYCLOAK_ADMIN'

def get_keycloak_admin(request: Request) -> KeycloakAdmin:
    return request.app.extra[KEYCLOAK_ADMIN]

class ApiToken(BaseModel):
    token: str

HTTPBearer_security = HTTPBearer()

def verify_bearer_token(request: Request,
                        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer_security)) -> ArxivUserClaims | ApiToken | None:
    token = credentials.credentials
    if not token:
        return None
    if request.app.extra['AAA_API_SECRET_KEY'] and token == request.app.extra['AAA_API_SECRET_KEY']:
        return ApiToken(token = token)
    jwt_secret = request.app.extra['JWT_SECRET']
    return decode_user_claims(token, jwt_secret)


def is_super_user(token: ArxivUserClaims | ApiToken | None) -> bool:
    return token and (isinstance(token, ApiToken) or (isinstance(token, ArxivUserClaims) and token.is_admin))

def describe_super_user(token: ArxivUserClaims | ApiToken | None) -> str:
    if token:
        if isinstance(token, ApiToken):
            return "API"
        if isinstance(token, ArxivUserClaims):
            return "Admin user %s" % token.username
    return "Not super"
