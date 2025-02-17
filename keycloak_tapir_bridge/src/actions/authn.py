"""
Authenticatino events

ex:
{
  "id" : "cfcfd312-cb01-44a6-8753-82a10028df49",
  "time" : 1739811509474,
  "type" : "LOGIN",
  "realmId" : "e30400df-2670-437f-8d65-3b6654e072c4",
  "realmName" : "arxiv",
  "clientId" : "arxiv-user",
  "userId" : "2280",
  "sessionId" : "ff64f168-c6f9-445c-9190-7ba76f64aecb",
  "ipAddress" : "0:0:0:0:0:0:0:1",
  "details" : {
    "auth_method" : "openid-connect",
    "auth_type" : "code",
    "response_type" : "code",
    "redirect_uri" : "http://localhost.arxiv.org:5100/aaa/callback",
    "consent" : "no_consent_required",
    "code_id" : "ff64f168-c6f9-445c-9190-7ba76f64aecb",
    "response_mode" : "query",
    "username" : "user0000"
  }
}


"""
import logging
from functools import reduce
from typing import Any

from sqlalchemy.orm import Session
# from sqlalchemy import and_

from arxiv.db.models import TapirUser
from arxiv.auth.legacy import accounts
from arxiv.auth import domain


def dispatch_authn_do_login(data: dict, _representation: Any, session: Session, logger: logging.Logger) -> None:
    user_id = data.get("userId")
    details = data.get("details", {})
    username = details.get("username", "")
    logger.debug(f"LOGIN: Entering {__name__} - user: {username} / {user_id}")
    # Need to update the tapir session



def dispatch_authn_do_logout(data: dict, _representation: Any, session: Session, logger: logging.Logger) -> None:
    user_id = data.get("userId")
    details = data.get("details", {})
    username = details.get("username", "")
    logger.debug(f"LOGOUT: Entering {__name__} - user: {username} / {user_id}")
    # Need to update the tapir session
