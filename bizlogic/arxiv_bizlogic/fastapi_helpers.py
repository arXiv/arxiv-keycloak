"""Contains route information."""
import asyncio
import base64
import datetime
import hashlib
import socket
from dataclasses import dataclass
from logging import getLogger
from typing import Optional

import jwcrypto
import jwcrypto.jwt
import jwt
from arxiv.auth.user_claims import ArxivUserClaims
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from starlette.types import ASGIApp, Receive, Scope, Send

from .database import Database


class ApiToken(BaseModel):
    token: str


HTTPBearer_security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class COOKIE_ENV_NAMES_TYPE:
    classic_cookie_env: str
    auth_session_cookie_env: str
    keycloak_access_token_env: str
    keycloak_refresh_token_env: str
    ng_cookie_env: str

COOKIE_ENV_NAMES = COOKIE_ENV_NAMES_TYPE(
    "CLASSIC_COOKIE_NAME",
    "AUTH_SESSION_COOKIE_NAME",
    "KEYCLOAK_ACCESS_TOKEN_NAME",
    "KEYCLOAK_REFRESH_TOKEN_NAME",
    "ARXIVNG_COOKIE_NAME"
)


def decode_user_claims(token: str, jwt_secret: str) -> ArxivUserClaims | None:
    logger = getLogger(__name__)
    if not token:
        logger.error(f"There is no cookie")
        return None
    if not jwt_secret:
        logger.error("The app is misconfigured or no JWT secret has been set")
        return None

    kc_tokens = {}
    jwt_payload = token

    try:
        claims = ArxivUserClaims.decode_jwt_payload(kc_tokens, jwt_payload, jwt_secret)

    except jwcrypto.jwt.JWTExpired:
        # normal course of token expiring
        return None

    except jwcrypto.jwt.JWTInvalidClaimFormat:
        logger.warning(f"Chowed cookie '{token}'")
        return None

    except jwt.ExpiredSignatureError:
        # normal course of token expiring
        return None

    except jwt.DecodeError:
        logger.warning(f"Chowed cookie '{token}'")
        return None

    except ValueError as exc:
        logger.warning(f"token {token} is malformed")
        return None

    except Exception as exc:
        logger.warning(f"token {token} is wrong?", exc_info=exc)
        return None

    if not claims:
        logger.info(f"unpacking token {token} failed")
        return None
    return claims


def get_current_user_or_none(request: Request) -> ArxivUserClaims | None:
    """gets the user claims from the cookie. This is a foundational function, and do not change the functionality."""
    logger = getLogger(__name__)
    session_cookie_key = request.app.extra[COOKIE_ENV_NAMES.auth_session_cookie_env]
    token = request.cookies.get(session_cookie_key)
    if not token:
        logger.debug(f"There is no cookie '{session_cookie_key}'")
        return None
    secret = request.app.extra['JWT_SECRET']
    if not secret:
        logger.error("The app is misconfigured or no JWT secret has been set")
        return None
    return decode_user_claims(token, secret)


async def get_current_user(request: Request) -> ArxivUserClaims | None:
    """gets the user claims from the cookie, and raises 401 if no user claims.
    """
    user = get_current_user_or_none(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def get_current_user_access_token(request: Request) -> str | None:
    logger = getLogger(__name__)
    kc_cookie_key = request.app.extra[COOKIE_ENV_NAMES.keycloak_access_token_env]
    return request.cookies.get(kc_cookie_key)


def get_db():
    db = Database.get_from_global()
    yield from db.get_session()


def get_client_host(request: Request) -> Optional[str]:
    host = request.headers.get('x-real-ip')
    if not host:
        host = request.client.host
    return host


async def get_hostname(ip_address: str, timeout: float = 1.0) -> str:
    try:
        host_name = await asyncio.wait_for(
            asyncio.to_thread(socket.gethostbyaddr, ip_address),
            timeout=timeout
        )
        return host_name[0]
    except (asyncio.TimeoutError, socket.herror):
        return "Hostname could not be resolved"


async def get_client_host_name(request: Request) -> Optional[str]:
    remote = get_client_host(request)
    if remote:
        # For pytest, the api_client's most is "testclient". So, special case it.
        if remote == "testclient":
            remote = "127.0.0.1"
        return await get_hostname(remote)
    return None


def datetime_to_epoch(timestamp: datetime.datetime | datetime.date | None,
                      default: datetime.date | datetime.datetime,
                      hour=0, minute=0, second=0) -> int:
    if timestamp is None:
        timestamp = default
    if isinstance(timestamp, datetime.date) and not isinstance(timestamp, datetime.datetime):
        # Convert datetime.date to datetime.datetime at midnight UTC
        timestamp = datetime.datetime.combine(timestamp, datetime.time(hour, minute, second))

    # Ensure the datetime is timezone-aware (UTC)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)

    # Use timestamp() method which returns UTC epoch
    return int(timestamp.timestamp())


VERY_OLDE = datetime.datetime(1981, 1, 1)



def sha256_base64_encode(input_string: str) -> str:
    """Hash a string with SHA-256 and return the Base64-encoded result."""
    sha256_hash = hashlib.sha256(input_string.encode()).digest()
    return base64.b64encode(sha256_hash).decode()



def verify_bearer_token(request: Request,
                        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer_security)) -> ArxivUserClaims | ApiToken | None:
    """
    Verifies the provided bearer token. This is a foundational function, and do not change the functionality.

    This function checks whether the provided bearer token is valid by
    comparing it against a predefined shared secret or by decoding it using
    a shared JWT secret. If the token is valid, it either returns an API token
    object or user claims.

    Args:
        request (Request): The incoming FastAPI request.
        credentials (Optional[HTTPAuthorizationCredentials]): The credentials
            extracted from the HTTP Authorization header, provided by
            FastAPI's `HTTPBearer_security`.

    Returns:
        ArxivUserClaims | ApiToken | None: Returns an `ApiToken` object if the
        bearer token matches the shared secret, `ArxivUserClaims` if a valid
        JWT token is decoded, or `None` if the token is invalid or not provided.
    """

    if credentials:
        token = credentials.credentials
        if not token:
            return None
        master_key = request.app.extra.get('API_SHARED_SECRET')
        if master_key and token == master_key:
            return ApiToken(token = token)
        jwt_secret = request.app.extra['JWT_SECRET']
        return decode_user_claims(token, jwt_secret)
    return None


def get_authn_or_none(
    request: Request,
    cookie_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
    credentials: Optional[ArxivUserClaims | ApiToken ] = Depends(verify_bearer_token)) -> ArxivUserClaims | ApiToken | None:
    """
    Determines the authentication credentials for the current request.

    This function checks for user authentication by first verifying the
    bearer token and falling back to user information from cookies if no
    valid bearer token is found. If neither is present, it returns `None`.

    Args:
        request (Request): The incoming FastAPI request.
        cookie_user (Optional[ArxivUserClaims]): User data extracted from
            cookies, provided by `get_current_user_or_none`.
        credentials (Optional[ArxivUserClaims | ApiToken]): Authentication
            credentials (user claims or API token), provided by
            `verify_bearer_token`.

    Returns:
        ArxivUserClaims | ApiToken | None: Returns authenticated `ArxivUserClaims`
        or `ApiToken` if either the bearer token or cookie user is valid.
        Returns `None` if no authentication credentials are present.
    """

    if credentials:
        return credentials
    elif cookie_user:
        return cookie_user

    return None


async def get_authn(
        request: Request,
        cookie_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        credentials: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token)) -> ArxivUserClaims | ApiToken:
    cred = get_authn_or_none(request, cookie_user, credentials)
    if cred is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    return cred


async def get_authn_user(
        request: Request,
        cookie_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
        credentials: Optional[ArxivUserClaims | ApiToken] = Depends(verify_bearer_token)) -> ArxivUserClaims:
    """
    Gets a user claims object from a cookie or bearer token. ApiToken is not allowed.
    Use this if you need to get user_id - IOW, when you mest leave an audit, use this.

    :param request:
    :param cookie_user:
    :param credentials:
    :return: ArxivUserClaims
    """
    cred = get_authn_or_none(request, cookie_user, credentials)
    if cred is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    if not isinstance(cred, ArxivUserClaims):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    return cred


async def is_admin_user(request: Request,
                        user: ArxivUserClaims | ApiToken | None = Depends(get_authn_or_none)
                        ) -> bool:
    if user and isinstance(user, ArxivUserClaims):
        if user.is_admin:
            return True
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def is_any_user(request: Request,
                      user: ArxivUserClaims | ApiToken | None = Depends(get_authn_or_none)
                      ) -> bool:
    if user and isinstance(user, ArxivUserClaims):
        return True
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


class TapirCookieToUserClaimsMiddleware:
    """
    Middleware that checks for tapir cookie and creates ArxivUserClaims JWT token.
    
    If ArxivUserClaims cookie is missing but tapir cookie exists, this middleware
    will create an ArxivUserClaims object from the tapir cookie and inject a JWT
    token as Authorization Bearer header.
    """
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        request = Request(scope, receive)
        
        # Get cookie names from app config
        auth_session_cookie_name = request.app.extra.get(COOKIE_ENV_NAMES.auth_session_cookie_env, "ARXIVNG_SESSION_ID")
        classic_cookie_name = request.app.extra.get(COOKIE_ENV_NAMES.classic_cookie_env, "tapir_session")
        jwt_secret = request.app.extra.get('JWT_SECRET')
        
        # Check if ArxivUserClaims cookie already exists
        arxiv_claims_cookie = request.cookies.get(auth_session_cookie_name)
        
        # Check if Authorization header already exists
        headers = dict(scope.get("headers", []))
        existing_auth = headers.get(b"authorization")
        
        # If no ArxivUserClaims cookie, no existing auth header, but tapir cookie exists, create JWT token
        if not arxiv_claims_cookie and not existing_auth and jwt_secret:
            tapir_cookie = request.cookies.get(classic_cookie_name)
            if tapir_cookie:
                try:
                    # Import here to avoid circular imports
                    from .bizmodels.tapir_to_user_claims import create_user_claims_from_tapir_cookie
                    from .database import Database
                    
                    # Get database session
                    db = Database.get_from_global()
                    session_gen = db.get_session()
                    session = next(session_gen)
                    
                    try:
                        # Create ArxivUserClaims from tapir cookie
                        user_claims: ArxivUserClaims = create_user_claims_from_tapir_cookie(session, tapir_cookie)
                        
                        if user_claims:
                            # Create JWT token from user claims
                            token = user_claims.encode_jwt_token(jwt_secret)
                            
                            # Add Authorization header to the request
                            headers[b"authorization"] = f"Bearer {token}".encode()
                            scope["headers"] = list(headers.items())
                            
                    finally:
                        session.close()
                        
                except Exception as exc:
                    # Log error but don't break the request
                    logger = getLogger(__name__)
                    logger.warning("Failed to create JWT from tapir cookie", exc_info=exc)
        
        await self.app(scope, receive, send)


def get_tapir_tracking_cookie(request: Request) -> str | None:
    """Return the tapir tracking cookie value if it exists, otherwise None."""
    tracking_cookie_key = request.app.extra.get('TRACKING_COOKIE_NAME', "tapir_tracking")
    return request.cookies.get(tracking_cookie_key)
