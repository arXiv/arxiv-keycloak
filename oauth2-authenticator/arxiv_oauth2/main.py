import os
from typing import Callable, List

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
# from sqlalchemy.orm import sessionmaker
from keycloak import KeycloakAdmin # , KeycloakError
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.middleware import is_valid_uuid4
from uuid import uuid4

from arxiv.auth.legacy.util import missing_configs
from arxiv.base.globals import get_application_config
from arxiv.base.logging import getLogger
from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient
from arxiv.db.models import State

from .authentication import router as authn_router, WellKnownServices
from .account import router as account_router
from .captcha import router as captcha_router
from .keycloak import router as keycloak_router

from .app_logging import setup_logger
from .mysql_retry import MySQLRetryMiddleware
from . import get_db, COOKIE_ENV_NAMES, get_keycloak_admin
from .biz.keycloak_audit import get_keycloak_dispatch_functions
from arxiv_bizlogic.fastapi_helpers import TapirCookieToUserClaimsMiddleware

#
# Since this is not a flask app, the config needs to be in the os.environ
# Fill in these if it's missing. This is required for setting up Tapir session.
# On Apache, these are found.
# Since this is running in docker, there is no way to get that value so needs to be set
# as environment.
# These look a little redundant (which probably true) but making sure they are present in the
# os.environ wi
#
CONFIG_DEFAULTS = {
    'SESSION_DURATION': os.environ.get('SESSION_DURATION', '120'),
    COOKIE_ENV_NAMES.classic_cookie_env: os.environ.get(COOKIE_ENV_NAMES.classic_cookie_env, "tapir_session"),
    'CLASSIC_SESSION_HASH': os.environ.get('CLASSIC_SESSION_HASH', 'not-very-safe-hash-value')
}

#
# LOGOUT_REDIRECT_URL

# You should set BASE_SERVER first.
# That's the entry point of whole thing
# Setting has the notion of AUTH_SERVER, and it may be relevant.
# For the actual deployment, since this is running in a docker with plain HTTP,
# it's up to the web server's setting.

SERVER_ROOT_PATH = os.environ.get('SERVER_ROOT_PATH', "/aaa")
#
KEYCLOAK_SERVER_URL = os.environ.get('KEYCLOAK_SERVER_URL', 'https://oidc.arxiv.org')

# This is the public URL that OAuth2 calls back when the authentication succeeds.
CALLBACK_URL = os.environ.get("OAUTH2_CALLBACK_URL", "https://dev3.arxiv.org/aaa/callback")

# For arxiv-user, the client needs to know the secret.
# This is in keycloak's setting. Do not ever ues this value. This is for development only.
# You should generate one, and use it in keycloak. it can generate a good one on UI.
ARXIV_USER_SECRET = os.environ.get('ARXIV_USER_SECRET', '<arxiv-user-secret-is-not-set>')

# session cookie names
# NOTE: You also need the classic session cookie name "tapir_session" but it's set
# slightly differently since it needs to be passed to arxiv-base
AUTH_SESSION_COOKIE_NAME = os.environ.get(COOKIE_ENV_NAMES.auth_session_cookie_env, "arxiv_oidc_session")

# arXiv's Keycloak access token names
ARXIV_KEYCLOAK_COOKIE_NAME = os.environ.get(COOKIE_ENV_NAMES.arxiv_keycloak_cookie_env, "arxiv_keycloak_token")

# OIDC server SSL verify - this should be always true except when you are running locally and with self-signed cert
OIDC_SERVER_SSL_VERIFY = os.environ.get('OIDC_SERVER_SSL_VERIFY', os.environ.get('SECURE', 'true')) != "false"

# More cors origins
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "")

_idp_ = ArxivOidcIdpClient(CALLBACK_URL,
                           scope=["openid"],
                           server_url=KEYCLOAK_SERVER_URL,
                           client_secret=ARXIV_USER_SECRET,
                           logger=getLogger(__name__),
                           ssl_verify=OIDC_SERVER_SSL_VERIFY,
                           )


origins = [
    "http://localhost",
    "http://localhost:5000",
    "http://localhost:5000/",
    "http://localhost:5000/admin-console",
    "http://localhost:5000/admin-console/",
    "https://arxiv.org",
    "https://arxiv.org/",
    "https://dev.arxiv.org",
    "https://dev.arxiv.org/",
    "https://dev3.arxiv.org",
    "https://dev3.arxiv.org/",
    "https://dev9.arxiv.org",
    "https://dev9.arxiv.org/",
    "https://dev9.dev.arxiv.org",
    "https://dev9.dev.arxiv.org/",
    "https://web40.arxiv.org",
    "https://web40.arxiv.org/",
    "https://web41.arxiv.org",
    "https://web41.arxiv.org/",
    ]

def create_app(*args, **kwargs) -> FastAPI:
    setup_logger()
    from arxiv.config import Settings

    settings = Settings(
        CLASSIC_DB_URI = os.environ.get('CLASSIC_DB_URI', "arXiv"),
        LATEXML_DB_URI = None
    )
    from arxiv_bizlogic.database import Database
    database = Database(settings)
    database.set_to_global()


    # Doubly check we agree with get_application_config
    for key in missing_configs(get_application_config()):
        os.environ[key] = CONFIG_DEFAULTS[key]
        os.putenv(key, CONFIG_DEFAULTS[key])
    CLASSIC_COOKIE_NAME = os.environ.get(COOKIE_ENV_NAMES.classic_cookie_env, "tapir_session")
    ARXIVNG_COOKIE_NAME = os.environ.get(COOKIE_ENV_NAMES.ng_cookie_env, "ARXIVNG_SESSION_ID")
    SESSION_DURATION = int(os.environ.get("SESSION_DURATION", 120))
    logger = getLogger(__name__)


    # DOMAIN is okay to be None
    DOMAIN = os.environ.get("DOMAIN")
    if DOMAIN:
        if DOMAIN[0] != ".":
            DOMAIN = "." + DOMAIN
            logger.warning("DOMAIN does not have the leading dot. %s", DOMAIN)
    secure = True
    SECURE = os.environ.get("SECURE", "").lower()
    if SECURE in ["false", "no"]:
        secure = False

    logger.info(f"DOMAIN: {DOMAIN!r}")
    logger.info(f"SECURE: {secure!r}")
    logger.info(f"SERVER_ROOT_PATH: {SERVER_ROOT_PATH}")
    logger.info(f"KEYCLOAK_SERVER_URL {KEYCLOAK_SERVER_URL}")
    logger.info(f"CALLBACK_URL: {CALLBACK_URL}")
    logger.info(f"AUTH_SESSION_COOKIE_NAME: {AUTH_SESSION_COOKIE_NAME}")
    logger.info(f"CLASSIC_COOKIE_NAME: {CLASSIC_COOKIE_NAME}")
    logger.info(f"NG_COOKIE_NAME: {ARXIVNG_COOKIE_NAME}")
    logger.info(f"SESSION_DURATION: {SESSION_DURATION}")

    if not secure:
        logger.warning("SECURE is off. This cannot be good even in dev. This is for local development, like running under debugger.")

    jwt_secret = get_application_config().get('JWT_SECRET', settings.SECRET_KEY)
    if not jwt_secret or (jwt_secret == "qwert2345"):
        logger.error("JWT_SECRET nedds to be set correctly.")
        raise ValueError("JWT_SECRET is not set correctly.")

    # engine, _ = configure_db(settings)
    from arxiv.db import init as arxiv_db_init, _classic_engine
    arxiv_db_init(settings=settings)

    #
    realm_name = os.environ.get('ARXIV_REALM_NAME', "arxiv")
    keycloak_admin_secret = os.environ.get('KEYCLOAK_ADMIN_SECRET', "<NOT-SET>")
    if keycloak_admin_secret == "<NOT-SET>":
        logger.warning("KEYCLOAK_ADMIN_SECRET is not set correctly. kc_admin operations will fail.")
    keycloak_admin = KeycloakAdmin(
        server_url=KEYCLOAK_SERVER_URL,
        user_realm_name="master",
        client_id="admin-cli",
        username="admin",
        password=keycloak_admin_secret,
        realm_name=realm_name,
        verify=False,
    )

    URLs: dict = {f"ARXIV_URL_{name.upper()}": value for name, value, site in settings.URLS}

    #
    #
    well_known = WellKnownServices(
        arxiv_base_url=settings.BASE_SERVER,
        account="/user-account/",
        login=URLs['ARXIV_URL_LOGIN'],
        logout=URLs['ARXIV_URL_LOGOUT'],
        account_registration="/user-account/register",
        change_password="/user-account/change-password",
        password_recovery="/user-account/password-recover",
        oidc_url=KEYCLOAK_SERVER_URL,
    )

    app = FastAPI(
        root_path=SERVER_ROOT_PATH,
        idp=_idp_,
        arxiv_db_engine=_classic_engine,
        arxiv_settings=settings,
        SECURE=secure,
        DOMAIN=DOMAIN,
        JWT_SECRET=jwt_secret,
        KEYCLOAK_SERVER_URL=KEYCLOAK_SERVER_URL,
        COOKIE_MAX_AGE=int(os.environ.get('COOKIE_MAX_AGE', '99073266')),
        AUTH_SESSION_COOKIE_NAME=AUTH_SESSION_COOKIE_NAME,
        ARXIV_KEYCLOAK_COOKIE_NAME=ARXIV_KEYCLOAK_COOKIE_NAME,
        CLASSIC_COOKIE_NAME=CLASSIC_COOKIE_NAME,
        ARXIVNG_COOKIE_NAME=ARXIVNG_COOKIE_NAME,
        SESSION_DURATION=SESSION_DURATION,
        KEYCLOAK_ADMIN=keycloak_admin,
        ARXIV_USER_SECRET=ARXIV_USER_SECRET,
        CAPTCHA_SECRET=os.environ.get("CAPTCHA_SECRET", "foocaptcha"),
        WELL_KNOWN=well_known,
        AAA_API_SECRET_KEY=os.environ.get("AAA_API_SECRET_KEY", ""),
        KEYCLOAK_DISPATCH_FUNCTIONS=get_keycloak_dispatch_functions(),
        **URLs
    )

    if CORS_ORIGINS:
        for cors_origin in CORS_ORIGINS.split(","):
            origins.append(cors_origin.strip())

    flattened_origins = ",".join(origins)
    logger.info(f"cors origins: {flattened_origins}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        CorrelationIdMiddleware,
        header_name='X-Request-ID',
        update_request_header=True,
        generator=lambda: uuid4().hex,
        validator=is_valid_uuid4,
        transformer=lambda a: a,
        )

    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    app.add_middleware(MySQLRetryMiddleware, engine=_classic_engine,  retry_attempts=3)

    app.add_middleware(TapirCookieToUserClaimsMiddleware)

    app.include_router(authn_router)
    # app.include_router(authz_router)
    app.include_router(account_router)
    app.include_router(captcha_router)
    app.include_router(keycloak_router)

    @app.middleware("http")
    async def apply_response_headers(request: Request, call_next: Callable) -> Response:
        """Apply response headers to all responses.
           Prevent UI redress attacks.
        """
        response: Response = await call_next(request)
        response.headers['Content-Security-Policy'] = "frame-ancestors 'none'"
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @app.get("/")
    async def root(request: Request):
        return "Hello"

    @app.get("/status", response_model=dict)
    async def health_check(session: Session = Depends(get_db),
                           kc_admin: KeycloakAdmin = Depends(get_keycloak_admin)) -> dict | HTTPException:
        result = {}

        try:
            keycloak_admin.connection.get_token()
            token = keycloak_admin.connection.token
            result.update({"keycloak": "good" if isinstance(token, dict) and token.get('access_token', None) else "bad"})
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Keycloak: " + str(exc))

        try:
            states: List[State] = session.query(State).all()
            result.update({state.name: str(state.value) for state in states if state.name})
            return result

        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="mysql: " + str(exc))


    return app
