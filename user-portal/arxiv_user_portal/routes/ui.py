"""Provides Flask integration for the external user interface."""
import urllib.parse
from typing import Any, Callable
from datetime import timedelta, datetime
from functools import wraps
from flask import Blueprint, render_template, url_for, request, \
    make_response, redirect, current_app, send_file, Response

from http import HTTPStatus

from arxiv.base import logging

from arxiv.auth.auth.decorators import scoped

from arxiv_user_portal.controllers import registration


logger = logging.getLogger(__name__)
blueprint = Blueprint('ui', __name__, url_prefix='')

def anonymous_only(func: Callable) -> Callable:
    """Redirect logged-in users to their profile."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if hasattr(request, 'auth') and request.auth:
            next_page = request.args.get('next_page',
                                         current_app.config['DEFAULT_LOGIN_REDIRECT_URL'])
            return make_response(redirect(next_page, code=HTTPStatus.SEE_OTHER.value))
        else:
            return func(*args, **kwargs)
    return wrapper


def set_cookies(response: Response, data: dict) -> None:
    """
    Update a :class:`.Response` with cookies in controller data.

    Contollers seeking to update cookies must include a 'cookies' key
    in their response data.
    """
    # Set the session cookie.
    cookies = data.pop('cookies')
    if cookies is None:
        return None
    for cookie_key, (cookie_value, expires) in cookies.items():
        cookie_name = current_app.config[f'{cookie_key.upper()}_NAME']
        max_age = timedelta(seconds=expires)
        logger.debug('Set cookie %s with %s, max_age %s',
                     cookie_name, cookie_value, max_age)
        params = dict(httponly=True,
                      domain= current_app.config['AUTH_SESSION_COOKIE_DOMAIN'])

        if current_app.config['AUTH_SESSION_COOKIE_SECURE']:
            # Setting samesite to lax, to allow reasonable links to
            # authenticated views using GET requests.
            params.update({'secure': True, 'samesite': 'lax'})
        response.set_cookie(cookie_name, cookie_value, max_age=max_age,
                            **params)


# This is unlikely to be useful once the classic submission UI is disabled.
def unset_submission_cookie(response: Response) -> None:
    """
    Unset the legacy Catalyst submission cookie.

    In addition to the authenticated session (which was originally from the
    Tapir auth system), Catalyst also tracks a session used specifically for
    the submission process. The legacy Catalyst controller sets this
    automatically, so we don't need to do anything on login. But on logout,
    if this cookie is not cleared, Catalyst may attempt to use the same
    submission session upon subsequent logins. This can lead to weird
    inconsistencies.
    """
    response.set_cookie('submit_session', '', max_age=0, httponly=True)


def unset_permanent_cookie(response: Response) -> None:
    """
    Users who elect a permanent cookie expect it to be unset when they log out.

    If it is not unset, legacy components will attempt to log them back in.
    """
    permanent_cookie_name = current_app.config['CLASSIC_PERMANENT_COOKIE_NAME']
    domain = current_app.config['AUTH_SESSION_COOKIE_DOMAIN']
    now = datetime.utcnow()
    response.set_cookie(permanent_cookie_name, '', max_age=0, expires=now,
                        httponly=True)
    response.set_cookie(permanent_cookie_name, '', max_age=0, expires=now,
                        httponly=True, domain=domain)
    response.set_cookie(permanent_cookie_name, '', max_age=0, expires=now,
                        httponly=True, domain=domain.lstrip('.'))



@blueprint.after_request
def apply_response_headers(response: Response) -> Response:
    """Apply response headers to all responses."""
    """Prevent UI redress attacks."""
    response.headers['Content-Security-Policy'] = "frame-ancestors 'none'"
    response.headers['X-Frame-Options'] = 'DENY'

    return response

@blueprint.route('/', methods=['GET'])
def landing() -> Response:
    """Interface for creating new accounts."""
    content = render_template("landing.html")
    response = make_response(content)
    return response


@blueprint.route('/old-register', methods=['GET', 'POST'])
@anonymous_only
def old_register() -> Response:
    """Interface for creating new accounts."""
    captcha_secret = current_app.config['CAPTCHA_SECRET']
    ip_address = request.remote_addr
    next_page = request.args.get('next_page', url_for('account'))
    data, code, headers = registration.register(request.method, request.form,
                                                captcha_secret, ip_address,
                                                next_page)

    # Flask puts cookie-setting methods on the response, so we do that here
    # instead of in the controller.
    if code is HTTPStatus.SEE_OTHER.value:
        response = make_response(redirect(headers['Location'], code=code))
        set_cookies(response, data)
        return response
    content = render_template("register.html", **data)
    response = make_response(content, code, headers)
    return response


@blueprint.route('/register', methods=['GET', 'POST'])
@anonymous_only
def register() -> Response:
    """Interface for creating new accounts."""
    response = redirect("/user/register" )
    return response


@blueprint.route('/login', methods=['GET', 'POST'])
@anonymous_only
def login() -> Response:
    """User can log in with username and password, or permanent token."""
    default_next_page = current_app.config['DEFAULT_LOGIN_REDIRECT_URL']
    next_page = request.args.get('next_page', default_next_page)
    response = redirect(f"/aaa/login?next_page={urllib.parse.quote(next_page)}" )
    return response


@blueprint.route('/logout', methods=['GET'])
def logout() -> Response:
    """Log out of arXiv."""
    default_next_page = current_app.config['DEFAULT_LOGOUT_REDIRECT_URL']
    next_page = request.args.get('next_page', default_next_page)
    logger.debug('Request to log out, then redirect to %s', next_page)
    return redirect(f"/aaa/logout?next_page={urllib.parse.quote(next_page)}" )


@blueprint.route('/auth_status')
def auth_status() -> Response:
    """Get if the app is running."""
    return make_response("OK")


@blueprint.route('/protected')
@scoped()
def an_example() -> Response:
    """Example of a protected page.

    see arxiv_auth.auth.decorators in arxiv-auth for more details.
    """
    return make_response("This is an example of a protected page.")


@blueprint.route('/auth/v2/dev')
def dev() -> Response:
    """Dev landing page."""
    return render_template('dev.html')
