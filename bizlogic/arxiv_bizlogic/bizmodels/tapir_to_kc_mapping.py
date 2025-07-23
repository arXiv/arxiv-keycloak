import logging
import os
from typing import Tuple, List, Dict

from arxiv.auth.legacy.exceptions import PasswordAuthenticationFailed
from arxiv.auth.legacy.passwords import check_password
from arxiv.db.models import TapirUser, TapirUsersPassword, TapirNickname, Demographic, TapirPolicyClass
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .user_model import UserModel

UserProfile = Tuple[TapirUser, TapirUsersPassword, TapirNickname, Demographic]
logger = logging.getLogger(__name__)


def authenticate_password(session: Session, user: TapirUser, password: str) -> bool:
    """
    Authenticate using username/email and password.

    Parameters
    ----------
    user : TapirUser
        user model instance
    password : str

    Returns
    -------
    :bool:

    Raises
    ------
    :class:`AuthenticationFailed`
        Raised if the user does not exist or the password is incorrect.
    :class:`RuntimeError`
        Raised when other problems arise.

    """
    logger.debug(f'Authenticate with password, user: {user.user_id}')
    tapir_password: TapirUsersPassword | None = session.query(TapirUsersPassword) \
        .filter(TapirUsersPassword.user_id == user.user_id) \
        .one_or_none()
    if not tapir_password:
        return False
    try:
        if check_password(password, tapir_password.password_enc.encode("utf-8")):
            return True
    except PasswordAuthenticationFailed:
        pass
    return False


def _get_user_by_user_id(session: Session, user_id: int) -> TapirUser | None:
    """Only used by perm token"""
    return session.query(TapirUser) \
        .filter(TapirUser.user_id == int(user_id)) \
        .first()


def _get_user_by_email(session: Session, email: str) -> TapirUser | None:
    return session.query(TapirUser) \
        .filter(TapirUser.email == email) \
        .first()


def _get_user_by_username(session: Session, username: str) -> TapirUser | None:
    """Username is the tapir nickname."""
    if not username or '@' in username:
        raise ValueError("username must not contain a @")
    tapir_nick = session.query(TapirNickname) \
            .filter(TapirNickname.nickname == username) \
            .first()
    if not tapir_nick:
        return None

    return session.query(TapirUser) \
                .filter(TapirUser.user_id == tapir_nick.user_id) \
                .first()

def is_email(username_or_email) -> bool:
    return '@' in username_or_email


def get_tapir_user(session: Session, claim: str) -> TapirUser | None:
    """
    Does the user exist?

    Parameters
    ----------
    session : Session (sqlalchemy.orm.Session)
        Database session (expected to come from FastAPI context)
    claim : str
        Either the email address or username of the authenticating user.

    Returns
    -------
    :class:`.TapirUser`
    """
    return _get_user_by_email(session, claim) if is_email(claim) else _get_user_by_username(session, claim)


class AuthResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    firstName: str
    lastName: str
    enabled: bool
    emailVerified: bool
    attributes: Dict[str, List[str]]
    roles: List[str]
    groups: List[str]
    requiredActions: List[str]


class PasswordData(BaseModel):
    password: str

def user_model_to_auth_response(um: UserModel, tapir_user: TapirUser) -> AuthResponse:
    """Turns the tapir user to the user migration record"""
    # Keycloak's realm "arxiv" should have the roles beforehand.
    # Internal
    # AllowTexProduced
    # EditUsers
    # EditSystem
    # Approved
    # Banned
    # CanLock

    roles = []
    # not used - Only Pole Houle has this role apparently
    if um.flag_internal or um.flag_edit_system:
        roles.append('Owner')

    # admin flag
    if um.flag_allow_tex_produced:
        roles.append('AllowTexProduced')

    # admin flag
    if um.flag_edit_users:
        roles.append('Administrator')

    # not used
    if um.flag_approved:
        roles.append('Approved')

    # ?
    if um.flag_banned:
        roles.append('Banned')

    # user is able to lock submissions from further changes (ARXIVNG-2605)
    if um.flag_can_lock:
        roles.append('CanLock')

    if um.flag_proxy:
        roles.append("Proxy")

    if um.flag_xml:
        roles.append("XML")

    if um.flag_suspect:
        roles.append("Suspect")

    if um.flag_allow_tex_produced:
        roles.append("AllowTexProduced")

    attributes = {}

    # Important to have this. Otherwise, Keycloak does not pick up the email
    attributes["email"] = [um.email]

    # not used
    email_preferences = "email_preferences"
    attributes[email_preferences] = []
    if um.flag_wants_email:
        attributes[email_preferences].append('WantsEmail')
    if um.flag_html_email:
        attributes[email_preferences].append('HtmlEmail')

    # not used
    attributes["share"] = []
    if um.share_first_name:
        attributes["share"].append('FirstName')
    if um.share_last_name:
        attributes["share"].append('LastName')
    if um.share_email:
        attributes["share"].append('Email')

    # seems to exist in DB
    if um.joined_date:
        dt = um.joined_date
        attributes["joined_date"] = [dt.isoformat() + "Z"]

    if um.joined_ip_num:
        attributes["joined_ip_num"] = [str(um.joined_ip_num)]
    if um.joined_remote_host:
        attributes["joined_remote_host"] = [um.joined_remote_host]

    if um.tracking_cookie:
        attributes["tracking_cookie"] = [um.tracking_cookie]

    if um.suffix_name:
        attributes["suffix_name"] = [um.suffix_name]

    if um.email_bouncing:
        attributes["email_bouncing"] = [str(um.email_bouncing)]

    groups = []

    tpc: TapirPolicyClass = tapir_user.tapir_policy_classes
    if tpc.class_id:
        groups.append(tpc.name)
        roles.append(tpc.name)

    username = um.username

    if os.environ.get("NORMALIZE_USERNAME", "true") == "true":
        username = username.lower()

    if um.affiliation:
        attributes["affiliation"] = [um.affiliation]

    if um.url:
        attributes["url"] = [um.url]

    if um.orcid_id:
        attributes["orcid_id"] = [um.orcid_id]

    return AuthResponse(
        id=str(um.id),
        username=username,
        email=um.email,
        firstName=um.first_name,
        lastName=um.last_name,
        enabled=not (um.flag_deleted or um.flag_banned),
        emailVerified=um.flag_email_verified != 0,
        attributes=attributes,
        roles=roles,
        groups=groups,
        requiredActions=[],
    )

