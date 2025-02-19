"""
Controllers for registration and user profile management.

WORK IN PROGRESS: not in use.

Users are able to create a new arXiv account, and login using their username
and password. Each user can create a personalized profile with contact and
affiliation information, and links to external identities such as GitHub and
ORCID.
"""

from typing import Dict, Tuple, Any, Optional
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import BadRequest, InternalServerError

from arxiv import status
from arxiv_auth import domain
from arxiv.base import logging

from arxiv_auth.auth.sessions import SessionStore

from wtforms import StringField, PasswordField, SelectField, \
    BooleanField, Form, HiddenField
from wtforms.validators import DataRequired, Email, Length, URL, optional, \
    ValidationError
from flask import url_for, Markup
import pycountry

from arxiv import taxonomy
from .util import MultiCheckboxField, OptGroupSelectField

from .. import stateless_captcha

from arxiv_auth import legacy
from arxiv_auth.legacy import accounts
from arxiv_auth.legacy.exceptions import RegistrationFailed, \
    SessionCreationFailed, SessionDeletionFailed

logger = logging.getLogger(__name__)

ResponseData = Tuple[dict, int, dict]


def register(method: str, params: MultiDict, captcha_secret: str, ip: str,
             next_page: str) -> ResponseData:
    """Handle requests for the registration view."""
    data: Dict[str, Any]
    if method == 'GET':
        captcha_token = stateless_captcha.new(captcha_secret, ip)
        _params = MultiDict({'captcha_token': captcha_token})  # type: ignore
        form = RegistrationForm(_params, next_page=next_page)
        form.configure_captcha(captcha_secret, ip)
        data = {'form': form, 'next_page': next_page}
    elif method == 'POST':
        logger.debug('Registration form submitted')
        form = RegistrationForm(params, next_page=next_page)
        data = {'form': form, 'next_page': next_page}
        form.configure_captcha(captcha_secret, ip)

        if not form.validate():
            logger.debug('Registration form not valid')
            return data, status.HTTP_400_BAD_REQUEST, {}

        logger.debug('Registration form is valid')
        password = form.password.data

        # Perform the actual registration.
        try:
            user, auth = accounts.register(form.to_domain(), password, ip, ip)
        except RegistrationFailed as e:
            msg = 'Registration failed'
            raise InternalServerError(msg) from e  # type: ignore

        # Log the user in.
        session, cookie = _login(user, auth, ip)
        c_session, c_cookie = _login_classic(user, auth, ip)
        data.update({
            'cookies': {
                'session_cookie': (cookie, session.expires),
                'classic_cookie': (c_cookie, c_session.expires)
            },
            'user_id': user.user_id
        })
        return data, status.HTTP_303_SEE_OTHER, {'Location': next_page}
    return data, status.HTTP_200_OK, {}



def validate_captcha_value(self, field: StringField) -> None:
    """Check the captcha value against the captcha token."""
    stateless_captcha.check(self.captcha_token.data, field.data,
                            self.captcha_secret, self.ip)

