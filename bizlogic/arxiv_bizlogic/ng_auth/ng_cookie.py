import random

from arxiv.auth.user_claims import ArxivUserClaims
from pydantic import BaseModel
import jwt
from typing import Optional

# from sqlalchemy.orm import Session
# from arxiv.auth import domain as xa_domain
# from arxiv.auth.legacy.util import compute_capabilities, get_scopes

class NGClaims(BaseModel):
    """
    The shape of NG Cookie

    See arxiv-auth users/arxiv/users/auth/sessions/store.py
    generate_cookie()"""
    user_id: int     # session.user.user_id
    session_id: str  # session.session_id
    nonce: str       # generate_nonce
    expires: str     # 'expires': session.end_time.isoformat()
    start_time: Optional[str] = None


def generate_nonce(length: int = 8) -> str:
    nonce = random.randint(0, 10 ** length - 1)
    return f'{nonce:0{length}d}'

NG_JWT_ALGO = "HS256"

def ng_cookie_decode(token: str, secret: str) -> dict:
    """Decode an auth token to access session information."""
    data = dict(jwt.decode(token, secret, algorithms=[NG_JWT_ALGO]))
    return data


def ng_cookie_encode(user: NGClaims, secret: str) -> str:
    """Encode a auth token"""
    return jwt.encode(vars(user), secret, algorithm=NG_JWT_ALGO)


def create_ng_claims(claims: ArxivUserClaims) -> NGClaims:
    # NG Cookie
    # I'm not sure of the duration of NG cookie. This prob. needs a review.

    return NGClaims(
        user_id=int(claims.user_id if claims.user_id else 0),
        session_id=claims.tapir_session_id,
        nonce=generate_nonce(),
        expires=claims.expires_at.isoformat())


# def user_jwt(user_id: int, secret: str) -> str:
#     """For use in testing to make a jwt."""
#     return ng_cookie_encode(
#         Auth(
#             user_id=user_id, session_id="fakesessionid", nonce="peaceout", expires="0"
#         ),
#         secret,
#     )
#
#
# def tapir_to_domain(session: Session, db_user, db_nick, db_profile):
#     user = xa_domain.User(
#         user_id=str(db_user.user_id),
#         username=db_nick.nickname,
#         email=db_user.email,
#         name=xa_domain.UserFullName(
#             forename=db_user.first_name,
#             surname=db_user.last_name,
#             suffix=db_user.suffix_name
#         ),
#         profile=db_profile.to_domain() if db_profile else None,
#         verified=bool(db_user.flag_email_verified)
#     )
#
#     auths = xa_domain.Authorizations(
#         classic=compute_capabilities(db_user),
#         scopes=get_scopes(db_user),
#         endorsements=endorsements.get_endorsements(session, user)
#     )
#     return user, auths
