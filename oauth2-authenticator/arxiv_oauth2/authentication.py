"""Provides integration for the external user interface."""
import dataclasses
import json
import urllib.parse
from dataclasses import asdict
from typing import Optional, Literal, Any, Dict

import jwt
from arxiv_bizlogic.bizmodels.user_model import UserModel
from arxiv_bizlogic.fastapi_helpers import get_client_host
# from arxiv_bizlogic.ng_auth import ng_cookie
from arxiv_bizlogic.ng_auth.ng_cookie import create_ng_claims, ng_cookie_encode  # NGClaims, generate_nonce,
from fastapi import APIRouter, Depends, status, Request, HTTPException, Response
from fastapi.responses import RedirectResponse, JSONResponse
from keycloak import KeycloakAdmin, KeycloakError
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from arxiv.auth.auth.exceptions import UnknownSession
from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient
from arxiv.auth.legacy.sessions import invalidate as legacy_invalidate
from starlette.datastructures import URL

# from arxiv.auth.legacy import accounts, exceptions
# from arxiv.auth import domain

from . import get_current_user_or_none, get_db, COOKIE_ENV_NAMES
# from .account import AccountRegistrationModel

from .sessions import create_tapir_session

@dataclasses.dataclass
class CookieParams:
    auth_session_cookie_name: str    # ArxivUserClaims
    classic_cookie_name: str         # classic cookie name
    arxiv_keycloak_cookie_name: str  # Keycloak access token
    ng_cookie_name: str              # arxivng cookie name
    domain: Optional[str]            # domain
    secure: bool                     # secure
    samesite: Literal["lax", "none"] # same site
    jwt_secret: str                  # JWT secret
    max_age: int


def cookie_params(request: Request) -> CookieParams:
    """
    ,
    request.app.extra[COOKIE_ENV_NAMES.classic_cookie_env],
    request.app.extra[COOKIE_ENV_NAMES.arxiv_keycloak_cookie_env],  # This is the Keycloak access token
    request.app.extra.get('DOMAIN'),
    request.app.extra.get('SECURE', True),
    request.app.extra.get('SAMESITE', "Lax"))

    """

    return CookieParams(
        auth_session_cookie_name=request.app.extra[COOKIE_ENV_NAMES.auth_session_cookie_env],
        classic_cookie_name=request.app.extra[COOKIE_ENV_NAMES.classic_cookie_env],
        arxiv_keycloak_cookie_name=request.app.extra[COOKIE_ENV_NAMES.arxiv_keycloak_cookie_env],
        ng_cookie_name=request.app.extra[COOKIE_ENV_NAMES.ng_cookie_env],
        domain=request.app.extra.get('DOMAIN'),
        secure=request.app.extra.get('SECURE', True),
        samesite=request.app.extra.get('SAMESITE', "Lax"),
        jwt_secret=request.app.extra.get('JWT_SECRET', "jwt secret is not set"),
        max_age=int(request.app.extra['COOKIE_MAX_AGE']),
    )


logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])

@router.get('/login')
async def login(request: Request,
          current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none)
          ) -> RedirectResponse:
    """User can log in with username and password, or permanent token."""
    # redirect to IdP
    idp: ArxivOidcIdpClient = request.app.extra["idp"]
    url = idp.login_url
    next_page = request.query_params.get('next_page', request.query_params.get('next', '/'))
    if next_page:
        url = url + "&state=" + urllib.parse.quote(next_page)
    if current_user:
        pass
    logger.info(f"Login URL: {url}")
    return RedirectResponse(url)


@router.get('/callback')
async def oauth2_callback(request: Request,
                          _db = Depends(get_db)
                          ) -> Response:
    """User can log in with username and password, or permanent token."""
    code = request.query_params.get('code')
    logger.debug("callback code: %s", repr(code))
    if code is None:
        logger.warning("error: %s", repr(request.query_params))
        request.session.clear()
        return Response(status_code=status.HTTP_200_OK)

    client_ip = request.headers.get("x-real-ip", request.client.host if request.client else "")

    idp: ArxivOidcIdpClient = request.app.extra["idp"]
    user_claims: Optional[ArxivUserClaims] = idp.from_code_to_user_claims(code, client_ipv4=client_ip)

    # session_cookie_key, classic_cookie_key, keycloak_key, domain, secure, samesite = cookie_params(request)

    if user_claims is None:
        logger.warning("Getting user claim failed. code: %s", repr(code))
        request.session.clear()
        # return Response(status_code=status.HTTP_401_UNAUTHORIZED)
        response = RedirectResponse(request.app.extra['ARXIV_URL_LOGIN'])
        #response.set_cookie(session_cookie_key, '', max_age=0, domain=domain, path="/",
        #                    secure=secure, samesite=samesite)
        #response.set_cookie(classic_cookie_key, '', max_age=0, domain=domain, path="/",
        #                    secure=secure, samesite=samesite)
        return response

    logger.debug("User claims: user id=%s, email=%s", user_claims.user_id, user_claims.email)

    # legacy cookie and session
    tapir_cookie, tapir_session = create_tapir_session(user_claims, client_ip)

    # Legacy cookie
    if tapir_cookie and tapir_session:
        user_claims.set_tapir_session(tapir_cookie, tapir_session)

    # Set up cookies
    next_page = urllib.parse.unquote(request.query_params.get("state", "/"))  # Default to root if not provided
    logger.debug("callback success: next page: %s", next_page)

    return make_cookie_response(request, user_claims, tapir_cookie, next_page)


@router.post('/impersonate/{user_id: str}')
async def impersonate(request: Request,
                      user_id: str,
                      session = Depends(get_db),
                      client_ip = Depends(get_client_host),
                      current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
                      ) -> Response:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    kc_admin: KeycloakAdmin = request.app.extra["KEYCLOAK_ADMIN"]
    # Tapir user
    tapir_user = UserModel.one_user(session, user_id)
    if tapir_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID is not found")

    try:
        kc_user = kc_admin.get_user(user_id, user_profile_metadata=True)
        if not kc_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID is not found")
    except KeycloakError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    access_token = ""
    id_token = ""
    refresh_token = ""
    # https://www.keycloak.org/docs-api/latest/rest-api/index.html#UserRepresentation
    claims: Dict[str, Any] = {
        'sub': user_id,
        'exp': current_user.expires_at,
        'iat': current_user.issued_at,
        'realm_access': kc_user.get("realmRoles", []),
        'email_verified': kc_user.get("emailVerified", False),
        'email': kc_user.get("email", ""),
        "acc": access_token,
        "idt": id_token,
        "refresh": refresh_token,
        "given_name": kc_user.get("firstName", ""),
        "family_name": kc_user.get("lastName", ""),
        "username": tapir_user.username,
        "client_ipv4": client_ip,
    }

    user_claims: ArxivUserClaims = ArxivUserClaims(claims)
    # session_cookie_key, classic_cookie_key, keycloak_key, domain, secure, samesite = cookie_params(request)
    logger.debug("User claims: user id=%s, email=%s", user_claims.user_id, user_claims.email)

    # legacy cookie and session
    tapir_cookie, tapir_session = create_tapir_session(user_claims, client_ip)

    # legacy cookie
    if tapir_cookie and tapir_session:
        user_claims.set_tapir_session(tapir_cookie, tapir_session)

    # Perform impersonation (returns a URL to redirect to)
    impersonation_response = kc_admin.connection.raw_post(f"admin/realms/{kc_admin.connection.user_realm_name}/users/{user_id}/impersonation", {})  # type: ignore
    impersonation_url = impersonation_response.headers.get("redirect")
    response = make_cookie_response(request, user_claims, tapir_cookie, impersonation_url)
    return response


@router.get('/refresh')
async def refresh_token(
        request: Request,
        ) -> Response:
    """Refresh the access token

    current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none)
    is the standard method of getting the cookie/user but since this is a refresh request, it is likely
    the user claims expired, and thus no "current user".

    IOW, this needs to get to the refresh token, turn it into access token and recreate the cookie if
    it succeeds.

    The code here mirrors to get_current_user_or_none, so maybe I should refactor to do the first part of
    checking the cookies and rehydrate it.
    """
    next_page = request.query_params.get('next_page', request.query_params.get('next', ''))
    cparam = cookie_params(request)
    user_claims: Optional[ArxivUserClaims] = None
    tapir_cookie = request.cookies.get(cparam.classic_cookie_name, "")
    login_url = request.url_for("login")  # Assuming you have a route named 'login'
    if next_page:
        login_url = URL(f"{login_url}?next_page={urllib.parse.quote(next_page)}")

    session_cookie_key = request.app.extra[COOKIE_ENV_NAMES.auth_session_cookie_env]
    token = request.cookies.get(session_cookie_key)
    if not token:
        logger.debug(f"There is no cookie '{session_cookie_key}'")
        return RedirectResponse(url=login_url, status_code=status.HTTP_303_SEE_OTHER)

    secret = request.app.extra['JWT_SECRET']
    if not secret:
        logger.error("The app is misconfigured or no JWT secret has been set")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        tokens, jwt_payload = ArxivUserClaims.unpack_token(token)
    except ValueError:
        logger.error("The token is bad.")
        return RedirectResponse(url=login_url, status_code=status.HTTP_303_SEE_OTHER)

    refresh_token = tokens.get('refresh')
    if refresh_token is None:
        logger.warning("Refresh token is not in the tokens")
        return RedirectResponse(url=login_url, status_code=status.HTTP_303_SEE_OTHER)

    idp: ArxivOidcIdpClient = request.app.extra["idp"]
    user_claims = idp.refresh_access_token(refresh_token)
    if user_claims is None:
        return RedirectResponse(url=login_url, status_code=status.HTTP_303_SEE_OTHER)

    response = make_cookie_response(request, user_claims, tapir_cookie, next_page)
    return response


class Tokens(BaseModel):
    """Token refresh request body"""
    classic: Optional[str]
    session: str
    refresh: str

class RefreshedTokens(BaseModel):
    """Token refresh reply"""
    session: str
    classic: Optional[str]
    domain: Optional[str]
    max_age: int
    secure: bool
    samesite: str

reported_env_name = set()

@router.post('/refresh', responses = {
    status.HTTP_200_OK: {
        "model": RefreshedTokens,
        "description": "Tokens successfully refreshed"
    },
    status.HTTP_303_SEE_OTHER: {
        "model": RefreshedTokens,
        "description": "Redirect to login if refresh token is missing"
    },
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Unauthorized if session or refresh token is invalid"
    }
    })
async def refresh_tokens(request: Request, response: Response, body: Tokens) -> Response:
    session = body.session
    if not session:
        logger.debug(f"There is no oidc session cookie.")
    classic_cookie = body.classic

    try:
        tokens, jwt_payload = ArxivUserClaims.unpack_token(session)
    except ValueError:
        logger.error("The token is bad.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The session token is invalid")

    idp: ArxivOidcIdpClient = request.app.extra["idp"]
    refresh_token = tokens.get('refresh')

    if refresh_token is None:
        logger.warning("Refresh token is not in the tokens")
        login_url = request.url_for("login")  # Assuming you have a route named 'login'
        return RedirectResponse(url=login_url, status_code=status.HTTP_303_SEE_OTHER)

    user_claims = idp.refresh_access_token(refresh_token)

    if user_claims is None:
        # The refresh token is invalid, or expired. Purge the session cookie
        for env_name in asdict(COOKIE_ENV_NAMES).values():
            if env_name in request.app.extra:
                response.delete_cookie(request.app.extra[env_name])
                pass
            else:
                # This is an ALARMING bug. app initialization is not done correctly.
                if env_name not in reported_env_name:
                    logger.warning("app.extra has no %s - which is very likely a bug", env_name)
                    reported_env_name.add(env_name)
                    pass
                pass
            pass
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    secret = request.app.extra['JWT_SECRET']

    cparam = cookie_params(request)
    cookie_max_age = int(request.app.extra['COOKIE_MAX_AGE'])

    content = RefreshedTokens(
        session = user_claims.encode_jwt_token(secret),
        classic = classic_cookie,
        domain = cparam.domain,
        max_age = cookie_max_age,
        secure = cparam.secure,
        samesite = cparam.samesite
    )
    default_next_page = request.app.extra['ARXIV_URL_HOME']
    # "post" should not redirect, I think.
    # next_page = request.query_params.get('next_page', request.query_params.get('next', default_next_page))
    response = make_cookie_response(request, user_claims, classic_cookie, '', content=content.model_dump())
    return response


@router.post('/logout')
@router.get('/logout')
async def logout(request: Request,
                 _db=Depends(get_db),
                 current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none)) -> Response:
    """Log out of arXiv."""
    default_next_page = request.app.extra['ARXIV_URL_HOME']
    next_page = request.query_params.get('next_page', request.query_params.get('next', default_next_page))
    cparam = cookie_params(request)

    classic_cookie = request.cookies.get(cparam.classic_cookie_name)

    logged_out = True
    email = "?"
    if current_user is not None:
        email = current_user.email
        logger.debug('Request to log out, then redirect to %s', next_page)
        idp: ArxivOidcIdpClient = request.app.extra["idp"]
        logged_out = idp.logout_user(current_user)

    if logged_out:
        logger.info('%s log out', email)

    if classic_cookie:
        try:
            legacy_invalidate(classic_cookie)
        except UnknownSession:
            # Trying to log out and there is no such session. What a happy coincidence
            logger.error("Tapir session has been gone")
            pass
        except Exception as exc:
            logger.error("Invalidating legacy session failed.", exc_info=exc)
            pass

    response = make_cookie_response(request, None, "", next_page)
    return response


@router.post('/logout-callback')
async def logout_callback(request: Request) -> Response:
    body = await request.body()
    logger.info("logout-callback body: %s", json.dumps(body))
    return Response(status_code=status.HTTP_200_OK)


@router.get('/token-names')
async def get_token_names(request: Request) -> JSONResponse:
    cparam = cookie_params(request)
    return JSONResponse(content={
        "session": cparam.auth_session_cookie_name,
        "classic": cparam.classic_cookie_name,
        "arxiv_keycloak": cparam.arxiv_keycloak_cookie_name,
    })


class WellKnownServices(BaseModel):
    arxiv_base_url: str
    account: str
    login: str
    logout: str
    account_registration: str
    change_password: str
    password_recovery: str
    oidc_url: str


@router.get('/well-known')
async def get_well_known_services(request: Request) -> WellKnownServices:
    well_known: WellKnownServices = request.app.extra["WELL_KNOWN"]
    return well_known


@router.get('/check-db')
async def check_db(db: Session = Depends(get_db)) -> JSONResponse:
    from arxiv.db.models import TapirCountry
    count = db.query(func.count(TapirCountry.digraph)).scalar()
    return JSONResponse(content={"count": count})


def make_cookie_response(request: Request,
                         user_claims: Optional[ArxivUserClaims],
                         tapir_cookie: Optional[str],
                         next_page: Optional[str],
                         content: Optional[Any] = None) -> Response:

    # Create NG cookie
    cparam = cookie_params(request)
    keycloak_key = cparam.arxiv_keycloak_cookie_name
    session_cookie_key = cparam.auth_session_cookie_name
    classic_cookie_key = cparam.classic_cookie_name
    ng_cookie_key = cparam.ng_cookie_name
    secure = cparam.secure
    domain = cparam.domain
    samesite = cparam.samesite
    cookie_max_age = cparam.max_age

    response: Response
    if next_page:
        if user_claims and user_claims.access_token:
            # Construct the updated URL with access token as query param
            parsed_url = urllib.parse.urlparse(next_page)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            #
            # ** Drop setting the access token in favor of using cookie. **
            #
            # query_params['access_token'] = user_claims.access_token
            # Maybe too pedantic?
            # query_params['token_type'] = "bearer"
            # query_params['refresh_token'] = user_claims.refresh_token
            updated_query = urllib.parse.urlencode(query_params, doseq=True)
            url = urllib.parse.urlunparse(parsed_url._replace(query=updated_query))
        else:
            url = next_page
        response = RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
    elif content:
        response = JSONResponse(content=content, status_code=status.HTTP_200_OK)
    else:
        response = Response(status_code=status.HTTP_200_OK)

    if user_claims:
        secret = cparam.jwt_secret
        token = user_claims.encode_jwt_token(secret)
        logger.debug('%s=%s',session_cookie_key, token)
        response.set_cookie(session_cookie_key, token, max_age=cookie_max_age,
                            domain=domain, path="/", secure=secure, samesite=samesite)
        response.set_cookie(keycloak_key, user_claims.access_token,  max_age=cookie_max_age,
                            domain=domain, path="/", secure=secure, samesite=samesite)
        try:
            response.set_cookie(ng_cookie_key, ng_cookie_encode(create_ng_claims(user_claims), secret),
                max_age=cookie_max_age, domain=domain, path="/", secure=secure, samesite=samesite)
        except:
            pass

    else:
        for key in [session_cookie_key, keycloak_key, ng_cookie_key]:
            response.set_cookie(key, "", max_age=0,
                                domain=domain, path="/", secure=secure, samesite=samesite, expires=1)

    if tapir_cookie:
        logger.debug('%s=%s',classic_cookie_key, tapir_cookie)
        response.set_cookie(classic_cookie_key, tapir_cookie, max_age=cookie_max_age,
                            domain=domain, path="/", secure=secure, samesite=samesite)
    else:
        logger.debug('%s=<EMPTY>',classic_cookie_key)
        response.set_cookie(classic_cookie_key, '', max_age=0,
                            domain=domain, path="/", secure=secure, samesite=samesite,
                            expires=1)
    return response

