"""
Middleware for interpreting authn/z information on requestsself.

This module provides :class:`ArxivCEAuthMiddleware`, which unpacks encrypted JSON
Web Tokens provided via the ``Authorization`` header. This is intended to
support requests that have been pre-authorized by the web server using the
authenticator service (see :mod:`authenticator`).

The configuration parameter ``JWT_SECRET`` must be set in the WSGI request
environ (e.g. Apache's SetEnv) or in the runtime environment. This must be
the same secret that was used by the authenticator service to mint the token.

To install the middleware, use the pattern described in
:mod:`arxiv.base.middleware`. For example:

.. code-block:: python

   from arxiv.base import Base
   from arxiv.base.middleware import wrap
   from arxiv.users import auth


   def create_web_app() -> Flask:
       app = Flask('foo')
       Base(app)
       auth.Auth(app)
       wrap(app, [auth.middleware.AuthMiddleware])
       return app


For convenience, this is intended to be used with
:mod:`arxiv.users.auth.decorators`.

"""
from typing import Callable, Optional
import logging
import threading
import jwt
import jwcrypto
import jwcrypto.jwt
from werkzeug.wrappers import Request, Response
# from werkzeug.exceptions import InternalServerError
# from werkzeug.wsgi import ClosingIterator
# from werkzeug.middleware.dispatcher import DispatcherMiddleware
# from wsgiref.types import WSGIEnvironment, WSGIApplication
# from werkzeug.utils import redirect
import httpx
import httpcore

from arxiv.base.middleware.base import BaseMiddleware, WSGIRequest, WSGIResponse

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_user_portal.auth_config import AUTH_SESSION_TYPE, ARXIV_CE_SESSION_CONFIG_NAME, AAA_CONFIG_NAME, \
    AUTH_CONFIG_TYPE, CLASSIC_SESSION_CONFIG_NAME

logger = logging.getLogger(__name__)

user_locks = {}
refreshed_token_tag = '_refresh_token_'


def get_user_lock(user_id):
    if user_id not in user_locks:
        user_locks[user_id] = threading.Lock()
    return user_locks[user_id]


def refresh_token(aaa_url: str,
                  cookies: dict,
                  session_cookie: str,
                  classic_cookie: str,
                  refresh_retry: int = 5,
                  request_timeout: int = 2) -> Optional[dict]:
    for iter in range(refresh_retry):
        try:
            with httpx.Client() as client:
                refresh_response = client.post(
                    aaa_url,
                    json={
                        "session": session_cookie,
                        "classic": classic_cookie,
                    },
                    cookies=cookies,
                    timeout=request_timeout,
                )

            if refresh_response.status_code == 200:
                # Extract the new token from the response
                refreshed_tokens = refresh_response.json()
                return refreshed_tokens
            elif refresh_response.status_code >= 500 and refresh_response.status_code <= 599:
                # This needs a retry
                logger.warning("post to %s status %s. iter=%d", aaa_url, refresh_response.status_code,
                               iter)
                continue
            else:
                logger.warning("calling %s failed. status = %s: %s",
                               aaa_url,
                               refresh_response.status_code,
                               str(refresh_response.content))
                break

        except httpcore.ConnectTimeout:
            logger.warning("post to %s timed out. iter=%d", aaa_url, iter)
            continue

        except Exception as exc:
            logger.warning("calling %s failed.", aaa_url, exc_info=exc)
            break

    return None



class ArxivCEAuthMiddleware(BaseMiddleware):
    """
    Middleware to handle auth information on requests.

    Before the request is handled by the application, the ``Authorization``
    header is parsed for an encrypted JWT. If successfully decrypted,
    information about the user and their authorization scope is attached
    to the request.

    This can be accessed in the application via
    ``flask.request.environ['session']``.  If Authorization header was not
    included, then that value will be ``None``.

    If the JWT could not be  decrypted, the value will be an
    :class:`Unauthorized` exception instance. We cannot raise the exception
    here, because the middleware is executed outside of the Flask application.
    It's up to something running inside the application (e.g.
    :func:`arxiv.users.auth.decorators.scoped`) to raise the exception.

    """
    def __call__(self, environ: dict, start: Callable) -> WSGIResponse:
        """Decode and unpack the auth token on the request."""
        request = Request(environ)
        environ['auth'] = None
        environ['claims'] = None
        session_meta: AUTH_SESSION_TYPE = self.config[ARXIV_CE_SESSION_CONFIG_NAME]
        secure_payload = request.cookies.get(session_meta.cookie_name)    # We may not have a token.

        if secure_payload is None:
            logger.debug('No auth token')
            return super().__call__(environ, start)

        kc_tokens = {}
        claims: Optional[ArxivUserClaims] = None
        # classic_meta: AUTH_SESSION_TYPE = self.config[CLASSIC_SESSION_CONFIG_NAME]
        auth_config: AUTH_CONFIG_TYPE = self.config[AAA_CONFIG_NAME]
        # user_id = visible_payload["sub"]

        try:
            claims = ArxivUserClaims.decode_jwt_payload(kc_tokens, secure_payload, session_meta.secret)
            # Attach the encrypted token so that we can use it in subrequests.
            environ['claims'] = claims
            pass

        except jwcrypto.jwt.JWTExpired:
            logger.debug(f"Expired cookie cookie: jwcrypto.jwt.JWTExpired '{token}'")
            pass

        except jwt.ExpiredSignatureError:
            logger.debug(f"Expired cookie cookie: jwt.ExpiredSignatureError '{token}'")
            pass

        except jwcrypto.jwt.JWTInvalidClaimFormat as exc:
            logger.warning(f"Chowed cookie jwcrypto.jwt.JWTInvalidClaimFormat '{token}'")
            # raise InternalServerError() from exc
            need_refresh = True
            pass

        except jwt.DecodeError as exc:
            logger.warning(f"Chowed cookie jwt.DecodeError or bad jwt-secret '{token}'")
            # raise InternalServerError() from exc
            need_refresh = True
            pass

        except Exception as exc:
            logger.warning(f"token {token} is broken?", exc_info=exc)
            # raise InternalServerError() from exc
            need_refresh = True
            pass

        environ['auth'] = claims.domain_session if claims else None
        response, alt_start = self.before(environ, start)
        response: WSGIResponse = self.app(environ, alt_start)
        response = self.after(response)
        return response
