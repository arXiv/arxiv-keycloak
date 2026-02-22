from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional

from arxiv_bizlogic.audit_event import admin_audit, AdminAudit_ChangeEmail
from arxiv_bizlogic.fastapi_helpers import datetime_to_epoch
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, union_all, select
from datetime import datetime, timedelta, timezone
import logging
import time

from arxiv.db.models import TapirEmailChangeToken, TapirUser, t_tapir_email_change_tokens_used, TapirNickname, \
    TapirAdminAudit, TapirSession
from pydantic import BaseModel
from arxiv_bizlogic.randomness import generate_random_string


# Assuming this is defined somewhere in the module
EMAIL_CHANGE_RATE_LIMIT = timedelta(days=1)  # For example, 1 day rate limit

# Set up logging
logger = logging.getLogger(__name__)

def generate_email_verify_token() -> str:
    token = generate_random_string(alpha=True, digits=True, specials=False, length=12)
    return token[0:6] + "-" + token[6:12]


class EmailChangedBy(Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class EmailChangeEntry(BaseModel):
    class Config:
        from_attributes = True

    id: str
    user_id: str
    email: str
    start_date: datetime
    end_date: Optional[datetime]
    changed_by: EmailChangedBy  # "USER" or "ADMIN[admin_name admin_id]"
    admin_id: Optional[int] = None
    issued_when: datetime
    used: bool  # Boolean indicating if the token was used


class UserEmailHistory(BaseModel):
    class Config:
        from_attributes = True
    user_id: str
    current: EmailChangeEntry
    joined_date: datetime
    change_history: List[EmailChangeEntry]


class TapirEmailChangeTokenModel(BaseModel):
    """
    Represents a record of email change using the TapirEmailChangeToken model.
    """
    class Config:
        from_attributes = True

    user_id: str
    email: str  # Current email
    new_email: str  # New email to change to
    secret: str  # Token secret
    tapir_session_id: Optional[int] = None
    remote_host: str
    remote_addr: str
    issued_when: datetime
    used: bool  # Boolean indicating if the token was used
    used_when: Optional[datetime] = None  # When the token was used (if used)
    used_from_ip: Optional[str] = None  # IP address from which token was used
    used_from_host: Optional[str] = None  # Hostname from which token was used


@dataclass
class EmailChangeRequest:
    user_id: str
    new_email: str
    remote_ip: str
    remote_hostname: str
    email: Optional[str] = None
    tapir_session_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    tracking_cookie: Optional[str] = None


def get_last_tapir_session(session: Session, user_id: str) -> Optional[TapirSession]:
     return session.query(TapirSession).filter(TapirSession.user_id == user_id).order_by(TapirSession.session_id.desc()).first()



def get_user_email_history(session: Session, user_id: str) -> UserEmailHistory:
    """
    Retrieve the complete email change history for a user using SQLAlchemy models.

    Args:
        session: SQLAlchemy session
        user_id: The user ID to look up

    Returns:
        UserEmailHistory: Complete user email history with typed data
    """

    # Get user basic info with nickname
    user_query = (
        select(TapirUser.email, TapirUser.joined_date, TapirNickname.nickname)
        .select_from(TapirUser)
        .outerjoin(TapirNickname, TapirNickname.user_id == TapirUser.user_id)
        .where(TapirUser.user_id == user_id)
    )

    user_result = session.execute(user_query).first()

    if not user_result:
        raise ValueError(f"User {user_id} not found")

    email, joined_date_int, nickname = user_result
    # identifier = nickname if nickname else email

    # Convert Unix timestamp to datetime
    joined_date = datetime.fromtimestamp(joined_date_int)

    # Build the UNION query for email changes
    # Query 1: Catalyst email changes (consumed tokens)
    query1 = (
        select(
            TapirEmailChangeToken.consumed_when.label('used_when'),
            TapirEmailChangeToken.old_email,
            TapirEmailChangeToken.new_email,
            func.space(128).label('who'),
            func.cast(0, Integer).label('admin_id'),  # type: ignore[arg-type]
            TapirEmailChangeToken.issued_when,
            TapirEmailChangeToken.used,
        )
        .where(
            TapirEmailChangeToken.user_id == user_id,
            TapirEmailChangeToken.used == 1,
            TapirEmailChangeToken.consumed_when.isnot(None)
        )
    )

    # Query 2: Tapir email changes (from used tokens table)
    query2 = (
        select(
            t_tapir_email_change_tokens_used.c.used_when,
            TapirEmailChangeToken.old_email,
            TapirEmailChangeToken.new_email,
            func.space(128).label('who'),
            func.cast(0, Integer).label('admin_id'),  # type: ignore[arg-type]
            TapirEmailChangeToken.issued_when,
            TapirEmailChangeToken.used,
        )
        .select_from(
            t_tapir_email_change_tokens_used.join(
                TapirEmailChangeToken,
                t_tapir_email_change_tokens_used.c.secret == TapirEmailChangeToken.secret
            )
        )
        .where(
            t_tapir_email_change_tokens_used.c.user_id == user_id,
            TapirEmailChangeToken.consumed_when.is_(None)
        )
    )

    # Query 3: Admin email changes
    query3 = (
        select(
            TapirAdminAudit.log_date.label('used_when'),
            func.cast('', String).label('old_email'),  # type: ignore[arg-type]
            TapirAdminAudit.data.label('new_email'),
            TapirNickname.nickname.label('who'),
            TapirAdminAudit.admin_user.label('admin_id'),
            TapirAdminAudit.log_date.label('issued_when'),
            func.cast(True, Boolean).label('used'),  # type: ignore[arg-type]
        )
        .join(
            TapirNickname,
            TapirAdminAudit.admin_user == TapirNickname.user_id,
            isouter=True
        )
        .where(
            TapirAdminAudit.affected_user == user_id,
            TapirAdminAudit.action == 'change-email'
        )
    )

    # Combine all queries with UNION and order by used_when
    union_query: Any = union_all(query1, query2, query3).order_by('used_when')

    email_changes_result = session.execute(union_query).fetchall()

    # Process email changes
    email_history = []
    begin_date = joined_date
    next_admin_change: EmailChangedBy = EmailChangedBy.USER

    for index, change in enumerate(email_changes_result):
        used_when_int, old_email, new_email, who, admin_id, issued_when, used = change

        # Convert Unix timestamp to datetime
        used_when = datetime.fromtimestamp(used_when_int)
        end_date = used_when

        # Determine who made the change
        if admin_id:
            admin_change = EmailChangedBy.ADMIN
        else:
            admin_change = EmailChangedBy.USER

        # Handle admin changes where old_email is empty (stored as "old new" format)
        if old_email == "" and new_email and " " in new_email:
            old_email, new_email = new_email.split(" ", 1)

        # Create email change record for the previous period
        if old_email:  # Only add if we have an old email
            email_change = EmailChangeEntry(
                id=f"user@{user_id}@{index}",
                user_id=user_id,
                email=old_email,
                start_date=begin_date,
                end_date=end_date,
                changed_by=EmailChangedBy(next_admin_change),
                admin_id=admin_id if admin_id else None,
                issued_when=issued_when,
                used=used,
            )
            email_history.append(email_change)

        begin_date = end_date
        next_admin_change = admin_change

    # Add current email period
    current_change = EmailChangeEntry(
        id=f"user@{user_id}@{len(email_changes_result)}",
        user_id=user_id,
        email=email,
        start_date=begin_date,
        end_date=None,  # Current email has no end date
        changed_by=EmailChangedBy(next_admin_change),
        admin_id=None,
        issued_when=begin_date,
        used=True
    )
    email_history.append(current_change)

    return UserEmailHistory(
        user_id=user_id,
        current=current_change,
        joined_date=joined_date,
        change_history=email_history,
    )


class EmailHistoryBiz:
    """
    Class to handle retrieving and managing email change history for a user.
    """
    session: Session
    user_id: str
    email_history: UserEmailHistory | None
    rate_limit: timedelta

    def __init__(self, session: Session, user_id: str, rate_limit: timedelta = EMAIL_CHANGE_RATE_LIMIT):
        self.session = session
        self.user_id = user_id
        self.email_history = None
        self.rate_limit = rate_limit

    def list_email_history(self) -> UserEmailHistory:
        """
        Retrieves the email change history for a user from TapirEmailChangeToken records
        and stores it in self.email_history.

        Returns:
            UserEmailHistory: A list of email change history records for the user
        """
        if self.email_history is None:
            self.email_history = get_user_email_history(self.session, self.user_id)
        return self.email_history


    def is_rate_exceeded(self) -> bool:
        """
        Checks if the rate limit for email changes has been exceeded.
        
        The rate limit is exceeded when the most recent email change request
        was issued within the rate_limit time window from now.
        
        Returns:
            bool: True if the rate limit has been exceeded, False otherwise
        """
        # Ensure we have the latest email history
        history = self.list_email_history()
            
        # If there's no history, the rate limit is not exceeded
        if not history:
            return False
            
        # Get the most recent email change request
        most_recent = history.current
        
        # Check if the most recent request is within the rate limit window
        # ntai: This seems not right to me. This should take a look at the last open request if there is one.
        now = datetime.now()
        time_since_last_request = now - most_recent.issued_when
        
        return time_since_last_request < self.rate_limit


    def add_email_change_request(self, change_request: EmailChangeRequest) -> TapirEmailChangeToken:
        """
        Adds a new email change history entry to the database.
        
        If the email field is empty, retrieves the current email from the TapirUser record.
        If timestamp is provided, it is used as the issued_when value, otherwise current time is used.
        
        Args:
            change_request: The EmailChangeRequest containing the new email change information

        Returns:
            TapirEmailChangeTokenModel: The created entry with all fields populated
        """
        # If email is empty, retrieve it from TapirUsers
        old_email = change_request.email
        if not old_email:
            user: TapirUser | None = self.session.query(TapirUser).filter(TapirUser.user_id == self.user_id).one_or_none()
            if user:
                old_email = user.email
            else:
                raise ValueError(f"User with ID {self.user_id} not found")
        
        tapir_session_id = change_request.tapir_session_id
        if tapir_session_id is None:
            last_session = get_last_tapir_session(self.session, self.user_id)
            if last_session:
                tapir_session_id = last_session.session_id
                change_request.tapir_session_id = tapir_session_id

        # Use provided timestamp or current time
        timestamp = change_request.timestamp if change_request.timestamp else datetime.now(tz=timezone.utc)
        
        # Generate a random secret if not provided
        email_secret = self.generate_email_verify_token(change_request)

        # Create a new token in the database
        new_token = TapirEmailChangeToken(
            user_id=int(self.user_id),
            old_email=old_email,
            new_email=change_request.new_email,
            secret=email_secret,
            remote_host=change_request.remote_ip, # entry.remote_host?
            issued_when=datetime_to_epoch(None, timestamp),
            tracking_cookie=change_request.tracking_cookie,
            used=False,
            session_id=tapir_session_id,
            consumed_when=None,
            consumed_from=None,
        )
        
        self.session.add(new_token)
        return new_token
    
    def email_verified(self, timestamp: datetime | None = None, remote_ip: str = "", remote_host: str = "",
                       session_id: str = "",
                       new_email: str = "") -> bool:
        """
        Marks the latest unused email change token as used.
        
        Updates the 'used' status from False to True on the most recent token that hasn't been used yet.
        Also adds a record to the tapir_email_change_tokens_used table to track when and where
        the verification was completed.
        
        Args:
            remote_ip: The IP address from which the verification was completed
            remote_host: The hostname from which the verification was completed
            session_id: The ID of the session during which the verification occurred
            
        Returns:
            bool: True if a token was successfully marked as used, False if no unused token was found
                 or if the update failed
        """
        # Check if session_id is provided (required for the used tokens table)
        if not session_id:
            logger.error("Session ID is required for email verification")
            return False
            
        # Ensure we have the latest email history
        if self.email_history is None:
            self.list_email_history()
            
        # If there's no history, nothing to verify
        if not self.email_history:
            logger.warning(f"No email history found for user {self.user_id}")
            return False
            
        # Find the most recent unused token directly from TapirEmailChangeToken table
        unused_token = (
            self.session.query(TapirEmailChangeToken)
            .filter(
                TapirEmailChangeToken.user_id == self.user_id,
                TapirEmailChangeToken.new_email == new_email,
                TapirEmailChangeToken.used == 0  # 0 means unused
            )
            .order_by(TapirEmailChangeToken.issued_when.desc())
            .first()
        )
                
        if unused_token is None:
            logger.warning(f"No unused email tokens found for user {self.user_id}")
            return False

        # Use the latest unused token
        email_change_token = unused_token
        
        # Get current timestamp
        if timestamp is None:
            timestamp = datetime.now(tz=timezone.utc)

        epoch_timestamp =datetime_to_epoch(None, timestamp)

        try:
            # 1. Update the token as used
            email_change_token.used = True
            email_change_token.consumed_when = epoch_timestamp
            email_change_token.consumed_from = remote_ip
            email_change_token.remote_host = remote_host
            
            # 2. Insert a record into the tapir_email_change_tokens_used table
            # Using the raw SQL connection to insert directly into the table
            self.session.execute(
                t_tapir_email_change_tokens_used.insert().values(
                    user_id=int(self.user_id),
                    secret=email_change_token.secret,
                    used_when=epoch_timestamp,
                    used_from=remote_ip[:16] if remote_ip else "",  # Limit to 16 chars as per schema
                    remote_host=remote_host[:255] if remote_host else "",  # Limit to 255 chars as per schema
                    session_id=session_id
                )
            )
            
            # 3. Also update the user's email_verified flag
            user: TapirUser | None = self.session.query(TapirUser).filter(TapirUser.user_id == self.user_id).one_or_none()
            if user:
                if not user.flag_email_verified:
                    user.flag_email_verified = True
                    logger.info(f"User {self.user_id} email flag marked as verified")

                if email_change_token.new_email and user.email != email_change_token.new_email:
                    logger.info(f"User {self.user_id} email changes from {user.email} to {email_change_token.new_email}")
                    user.email = email_change_token.new_email

            logger.info(f"Email change token for user {self.user_id} marked as verified")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to mark email token as verified for user {self.user_id}: {str(e)}")
            return False


    def generate_email_verify_token(self, change_request: EmailChangeRequest) -> str:
        """
        Generates a unique email verification token.
        
        This function tries to generate a unique token by calling the global 
        generate_email_verify_token() function. It checks if the token already exists, 
        and if it does, it generates another one. If the token is unique, it adds an 
        entry to the tapir_email_change_tokens_used table.
        
        Returns:
            str: A unique email verification token
        """

        tapir_session_id = change_request.tapir_session_id

        if tapir_session_id is None:
            last_session = get_last_tapir_session(self.session, self.user_id)
            if last_session:
                tapir_session_id = last_session.session_id
        
        for _ in range(10):  # Try up to 10 times to get a unique token
            # Generate a token using the global function
            token = generate_email_verify_token()
            
            # Check if this token already exists in TapirEmailChangeToken
            existing_token = (
                self.session.query(TapirEmailChangeToken)
                .filter(TapirEmailChangeToken.secret == token)
                .first()
            )
            
            # Also check if it exists in the used tokens table
            existing_used_token = self.session.execute(
                t_tapir_email_change_tokens_used.select()
                .where(t_tapir_email_change_tokens_used.c.secret == token)
            ).fetchone()
            
            # If the token doesn't exist in either table, we can use it
            if not existing_token and not existing_used_token:
                # Get current user
                user = self.session.query(TapirUser).filter(TapirUser.user_id == self.user_id).one_or_none()
                if not user:
                    raise ValueError(f"User with ID {self.user_id} not found")
                    
                # Add an entry to the t_tapir_email_change_tokens_used table
                try:
                    unix_timestamp = int(time.time())
                    self.session.execute(
                        t_tapir_email_change_tokens_used.insert().values(
                            user_id=int(self.user_id),
                            secret=token,
                            used_when=unix_timestamp,
                            used_from=change_request.remote_ip,
                            remote_host=change_request.remote_hostname,
                            session_id=tapir_session_id
                        )
                    )
                    self.session.flush()
                    return token
                except Exception as e:
                    self.session.rollback()
                    logger.error(f"Failed to add token to used tokens table: {str(e)}")
                    # Continue to next attempt
            
        # If we tried 10 times and still couldn't get a unique token, raise an error
        raise RuntimeError("Unable to generate a unique email verification token")

