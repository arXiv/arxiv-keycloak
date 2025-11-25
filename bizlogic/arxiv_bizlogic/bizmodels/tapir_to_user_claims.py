from typing import  Optional
from logging import getLogger
from arxiv.auth.legacy.cookies import unpack
from arxiv.auth.user_claims import ArxivUserClaims, ArxivUserClaimsModel
from sqlalchemy.orm import Session as DBSession
from arxiv.db.models import TapirUser, TapirSession
from .user_model import UserModel
from .tapir_to_kc_mapping import user_model_to_auth_response, AuthResponse
from ..fastapi_helpers import datetime_to_epoch


def create_user_claims_from_tapir_cookie(session: DBSession,
                                         tapir_cookie: str,
                                         ) -> Optional[ArxivUserClaims]:
    """
    Using the legacy tapir cookie, recreate user claims

    """
    logger = getLogger(__name__)
    # Tuple[str, str, str, datetime, datetime, str]:

    try:
        session_id, user_id, ip, issued_at, expires_at, capabilities = unpack(tapir_cookie)
        tapir_user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
        tapir_session: TapirSession | None = session.query(TapirSession).filter(TapirSession.session_id == session_id).one_or_none()
        if not tapir_user or not tapir_session:
            return None

        user = UserModel.one_user(session, str(user_id))
        auth_response: AuthResponse = user_model_to_auth_response(user, tapir_user)
        data = ArxivUserClaimsModel(
            sub=str(user_id),
            exp=datetime_to_epoch(None, expires_at),
            iat=int(tapir_session.start_time),
            roles=auth_response.roles,
            email_verified=auth_response.emailVerified,
            email=str(auth_response.email),
            first_name=auth_response.firstName,
            last_name=auth_response.lastName,
            username=auth_response.username,
            ts_id=int(session_id),
            sid="keycloak-session-id-is-not-available"
        )
        return ArxivUserClaims(data)

    except ValueError as exc:
        logger.error("create_user_claims_from_tapir_cookie - ValueError: " + str(exc), exc_info=exc)
        return None

    except Exception as exc:
        logger.error("create_user_claims_from_tapir_cookie", exc_info=exc)
        return None
