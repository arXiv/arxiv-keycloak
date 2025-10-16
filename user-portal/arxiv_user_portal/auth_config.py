import logging
import os
from dataclasses import dataclass
from typing import Tuple
import httpx

# from arxiv.auth.user_claims import ArxivUserClaims
# from arxiv.db import Session

ARXIV_CE_SESSION_CONFIG_NAME = "arxiv-ce-session"
CLASSIC_SESSION_CONFIG_NAME = "classic-session"
AAA_CONFIG_NAME = "aaa-config"

@dataclass
class AUTH_SESSION_TYPE:
    cookie_name: str
    cookie_domain: str
    cookie_secure: bool
    secret: str
    hash: str
    duration: int
    tracking_cookie: str
    permanent_cookie: str
    token_recovery_time: int


CLASSIC_SESSION = AUTH_SESSION_TYPE(
    cookie_name=os.environ.get('CLASSIC_COOKIE_NAME', 'tapir_session'),
    cookie_domain=os.environ.get('AUTH_SESSION_COOKIE_DOMAIN', '.arxiv.org'),
    cookie_secure=bool(int(os.environ.get('AUTH_SESSION_COOKIE_SECURE', '1'))),
    secret=os.environ.get('JWT_SECRET', 'jwt-secret'),
    hash=os.environ.get('CLASSIC_SESSION_HASH', 'foosecret'),
    duration=int(os.environ.get('SESSION_DURATION', '36000')),
    tracking_cookie=os.environ.get('CLASSIC_TRACKING_COOKIE', 'browser'),
    permanent_cookie=os.environ.get('CLASSIC_PERMANENT_COOKIE_NAME', 'tapir_permanent'),
    token_recovery_time=int(os.environ.get('CLASSIC_TOKEN_RECOVERY_TIMEOUT', '86400')),
)

ARXIV_CE_SESSION = AUTH_SESSION_TYPE(
    cookie_name=os.environ.get('ARXIV_CE_SESSION_COOKIE_NAME', 'ARXIVNG_SESSION_ID'),
    cookie_domain=os.environ.get('AUTH_SESSION_COOKIE_DOMAIN', '.arxiv.org'),
    cookie_secure=bool(int(os.environ.get('AUTH_SESSION_COOKIE_SECURE', '1'))),
    secret=os.environ.get('JWT_SECRET', 'jwt-secret'),
    hash="",
    duration=0,
    tracking_cookie="",
    permanent_cookie="",
    token_recovery_time=0,
)


@dataclass
class AUTH_CONFIG_TYPE:
    login_url: str
    logout_url: str
    refresh_url: str
    retry_count: int
    request_timeout: int


AAA_CONFIG = AUTH_CONFIG_TYPE(
    login_url=os.environ.get('AAA_LOGIN_REDIRECT_URL', '/aaa/login'),
    logout_url=os.environ.get('AAA_LOGOUT_REDIRECT_URL', '/aaa/logout'),
    refresh_url=os.environ.get('AAA_TOKEN_REFRESH_URL', '/aaa/refresh'),
    retry_count=int(os.environ.get('KC_RETRY', '5')),
    request_timeout=int(os.environ.get('KC_TIMEOUT', '2')),
)

def get_session_meta(url: str, logger: logging.Logger) -> Tuple[AUTH_SESSION_TYPE, AUTH_SESSION_TYPE, AUTH_CONFIG_TYPE]:
    try:
        with httpx.Client() as client:
            response = client.get(url, timeout=3)
            token_names = response.json()
            CLASSIC_SESSION.cookie_name = token_names.get('classic', CLASSIC_SESSION.cookie_name)
            ARXIV_CE_SESSION.cookie_name = token_names.get('session', ARXIV_CE_SESSION.cookie_name)
    except Exception as e:
        logger.warning("cookie name is not available : %s", e)

    return CLASSIC_SESSION, ARXIV_CE_SESSION, AAA_CONFIG
