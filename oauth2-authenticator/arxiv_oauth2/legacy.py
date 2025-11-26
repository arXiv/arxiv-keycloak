from typing import Optional

from arxiv.auth.legacy.cookies import unpack as unpack_legacy_cookie
from fastapi import Request

from . import cookie_params

from pydantic import BaseModel, Field
from datetime import datetime, timezone


class LegacySessionCookie(BaseModel):
    """Represents the unpacked legacy session cookie data."""

    session_id: str = Field(..., description="The session ID associated with the cookie")
    user_id: str = Field(..., description="The user ID of the authenticated account")
    ip_address: str = Field(..., description="The IP address of the client when the session was created")
    issued_at: datetime = Field(..., description="The datetime when the session was created")
    expires_at: datetime = Field(..., description="The datetime when the session expires")
    capabilities: str = Field(..., description="Legacy user privilege level")

    @staticmethod
    def from_tapir_cookie(tapir_cookie: str) -> 'LegacySessionCookie':
        session_id, user_id, ip_address, issued_at, expires_at, capabilities = unpack_legacy_cookie(tapir_cookie)
        return LegacySessionCookie(
            **{
                'session_id': session_id,
                'user_id': user_id,
                'ip_address': ip_address,
                'issued_at': issued_at,
                'expires_at': expires_at,
                'capabilities': capabilities
            }
        )


def get_tapir_cookie_or_none(request: Request) -> Optional[str]:
    cparams = cookie_params(request)

    # Get cookie names from app config
    classic_cookie_name = request.app.extra.get(cparams.classic_cookie_name, "tapir_session")
    tapir_cookie = request.cookies.get(classic_cookie_name)
    if tapir_cookie:
        try:
            session_id, user_id, ip_address, issued_at, expires_at, capabilities = unpack_legacy_cookie(tapir_cookie)
            if expires_at < datetime.now(tz=timezone.utc):
                return tapir_cookie
        except:
            pass
    return None
