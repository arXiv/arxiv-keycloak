"""Contains route information."""
from logging import getLogger
from typing import Optional
from dataclasses import dataclass
import hashlib
import base64

from fastapi import Request, HTTPException, status

import jwt
import jwcrypto
import jwcrypto.jwt
import datetime
import time

from arxiv.auth.user_claims import ArxivUserClaims
from keycloak import KeycloakAdmin
from sqlalchemy.orm import sessionmaker

ALGORITHM = "HS256"


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

    try:
        tokens, jwt_payload = ArxivUserClaims.unpack_token(token)
    except ValueError:
        logger.error("The token is bad.")
        return None

    try:
        claims = ArxivUserClaims.decode_jwt_payload(tokens, jwt_payload, secret)

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


async def get_current_user(request: Request) -> ArxivUserClaims | None:
    user = get_current_user_or_none(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def get_current_user_access_token(request: Request) -> str | None:
    logger = getLogger(__name__)
    kc_cookie_key = request.app.extra[COOKIE_ENV_NAMES.arxiv_keycloak_cookie_env]
    return request.cookies.get(kc_cookie_key)


SessionLocal = sessionmaker(autocommit=False, autoflush=False)
def get_db():
    """Dependency for fastapi routes"""
    from arxiv.db import _classic_engine
    db = SessionLocal(bind=_classic_engine)
    try:
        yield db
        if db.new or db.dirty or db.deleted:
            db.commit()
    except Exception as e:
        logger = getLogger(__name__)
        logger.warning(f'Commit failed, rolling back', exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def transaction():
    logger = getLogger(__name__)
    from arxiv.db import _classic_engine
    with SessionLocal(bind=_classic_engine) as session:
        try:
            yield session
            if session.new or session.dirty or session.deleted:
                session.commit()
        except HTTPException:  # HTTP exception is a normal business
            session.rollback()
            raise
        except Exception as e:
            logger = getLogger(__name__)
            logger.warning(f'Commit failed, rolling back', exc_info=True)
            session.rollback()
            raise


KEYCLOAK_ADMIN = 'KEYCLOAK_ADMIN'

def get_keycloak_admin(request: Request) -> KeycloakAdmin:
    return request.app.extra[KEYCLOAK_ADMIN]


def get_client_host(request: Request) -> Optional[str]:
    host = request.headers.get('x-real-ip')
    if not host:
        host = request.client.host
    return host


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
