"""Contains route information."""
from logging import getLogger
from typing import Optional
from dataclasses import dataclass
import hashlib
import base64
import socket
import asyncio

from fastapi import Request, HTTPException, status

import jwt
import jwcrypto
import jwcrypto.jwt
import datetime
import time

from arxiv.auth.user_claims import ArxivUserClaims

from .database import Database


@dataclass(frozen=True)
class COOKIE_ENV_NAMES_TYPE:
    classic_cookie_env: str
    auth_session_cookie_env: str
    arxiv_keycloak_cookie_env: str

COOKIE_ENV_NAMES = COOKIE_ENV_NAMES_TYPE(
    "CLASSIC_COOKIE_NAME",
    "AUTH_SESSION_COOKIE_NAME",
    "ARXIV_KEYCLOAK_COOKIE_NAME"
)


def decode_user_claims(token: str, jwt_secret: str) -> ArxivUserClaims | None:
    logger = getLogger(__name__)
    if not token:
        logger.error(f"There is no cookie")
        return None
    if not jwt_secret:
        logger.error("The app is misconfigured or no JWT secret has been set")
        return None

    try:
        tokens, jwt_payload = ArxivUserClaims.unpack_token(token)
    except ValueError:
        logger.error("The token is bad.")
        return None

    try:
        claims = ArxivUserClaims.decode_jwt_payload(tokens, jwt_payload, jwt_secret)

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

    except Exception as exc:
        logger.warning(f"token {token} is wrong?", exc_info=exc)
        return None

    if not claims:
        logger.info(f"unpacking token {token} failed")
        return None
    return claims


def get_current_user_or_none(request: Request) -> ArxivUserClaims | None:
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
    user = get_current_user_or_none(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def get_current_user_access_token(request: Request) -> str | None:
    logger = getLogger(__name__)
    kc_cookie_key = request.app.extra[COOKIE_ENV_NAMES.arxiv_keycloak_cookie_env]
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
    return await get_hostname(get_client_host(request))


def datetime_to_epoch(timestamp: datetime.datetime | datetime.date | None,
                      default: datetime.date | datetime.datetime,
                      hour=0, minute=0, second=0) -> int:
    if timestamp is None:
        timestamp = default
    if isinstance(timestamp, datetime.date) and not isinstance(timestamp, datetime.datetime):
        # Convert datetime.date to datetime.datetime at midnight
        timestamp = datetime.datetime.combine(timestamp, datetime.time(hour, minute, second))
    # Use time.mktime() to convert datetime.datetime to epoch time
    return int(time.mktime(timestamp.timetuple()))

VERY_OLDE = datetime.datetime(1981, 1, 1)


async def is_admin_user(request: Request) -> bool:
    # temporary - use user claims in base

    user = await get_current_user(request)
    if user:
        if user.is_admin:
            return True
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def is_any_user(request: Request) -> bool:
    user = await get_current_user(request)
    if user:
        return True
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def sha256_base64_encode(input_string: str) -> str:
    """Hash a string with SHA-256 and return the Base64-encoded result."""
    sha256_hash = hashlib.sha256(input_string.encode()).digest()
    return base64.b64encode(sha256_hash).decode()
