from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import logging
import time

from arxiv.db.models import TapirEmailChangeToken, TapirUser, t_tapir_email_change_tokens_used
from pydantic import BaseModel
from arxiv_bizlogic.randomness import generate_random_string

# Assuming this is defined somewhere in the module
EMAIL_CHANGE_RATE_LIMIT = timedelta(days=1)  # For example, 1 day rate limit

# Set up logging
logger = logging.getLogger(__name__)

def generate_email_verify_token() -> str:
    token = generate_random_string(alpha=True, digits=True, specials=False, length=12)
    return token[0:6] + "-" + token[6:12]


class EmailHistoryEntry(BaseModel):
    """
    Represents a record of email change using the TapirEmailChangeToken model.
    """
    class Config:
        from_attributes = True
    
    user_id: int
    email: str  # Current email
    new_email: str  # New email to change to
    secret: str  # Token secret
    remote_host: str
    remote_addr: str
    issued_when: datetime
    used: bool  # Boolean indicating if the token was used
    used_when: Optional[datetime] = None  # When the token was used (if used)
    used_from_ip: Optional[str] = None  # IP address from which token was used
    used_from_host: Optional[str] = None  # Hostname from which token was used


class EmailHistories:
    """
    Class to handle retrieving and managing email change history for a user.
    """
    session: Session
    user_id: str
    email_history: List[EmailHistoryEntry] = None
    rate_limit: timedelta

    def __init__(self, session: Session, user_id: str, rate_limit: timedelta = EMAIL_CHANGE_RATE_LIMIT):
        self.session = session
        self.user_id = user_id
        self.email_history = None
        self.rate_limit = rate_limit

    def list_email_history(self) -> List[EmailHistoryEntry]:
        """
        Retrieves the email change history for a user from TapirEmailChangeToken records
        and stores it in self.email_history.

        Returns:
            List[EmailHistoryEntry]: A list of email change history records for the user
        """
        query_result = (
            self.session.query(TapirEmailChangeToken)
            .filter(TapirEmailChangeToken.user_id == self.user_id)
            .order_by(TapirEmailChangeToken.issued_when.desc())
            .all()
        )

        self.email_history = [EmailHistoryEntry.model_validate(token) for token in query_result]
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
        if self.email_history is None:
            self.list_email_history()
            
        # If there's no history, the rate limit is not exceeded
        if not self.email_history:
            return False
            
        # Get the most recent email change request
        most_recent = self.email_history[0]  # List is already ordered by issued_when desc
        
        # Check if the most recent request is within the rate limit window
        now = datetime.now()
        time_since_last_request = now - most_recent.issued_when
        
        return time_since_last_request < self.rate_limit
    
    def add_email_change_request(self, entry: EmailHistoryEntry, timestamp: Optional[datetime] = None) -> EmailHistoryEntry:
        """
        Adds a new email change history entry to the database.
        
        If the email field is empty, retrieves the current email from the TapirUser record.
        If timestamp is provided, it is used as the issued_when value, otherwise current time is used.
        
        Args:
            entry: The EmailHistoryEntry containing the new email change information
            timestamp: Optional datetime to use as the issued_when value
            
        Returns:
            EmailHistoryEntry: The created entry with all fields populated
        """
        # If email is empty, retrieve it from TapirUsers
        if not entry.email:
            user = self.session.query(TapirUser).filter(TapirUser.user_id == self.user_id).one_or_none()
            if user:
                entry.email = user.email
            else:
                raise ValueError(f"User with ID {self.user_id} not found")
        
        # Use provided timestamp or current time
        if timestamp:
            entry.issued_when = timestamp
        else:
            entry.issued_when = datetime.now()
        
        # Ensure user_id matches
        entry.user_id = int(self.user_id)
        
        # Generate a random secret if not provided
        email_secret = self.generate_email_verify_token(entry)

        # Create a new token in the database
        new_token = TapirEmailChangeToken(
            user_id=entry.user_id,
            email=entry.email,
            new_email=entry.new_email,
            secret=email_secret,
            remote_host=entry.remote_host,
            remote_addr=entry.remote_addr,
            issued_when=entry.issued_when,
            used=entry.used or False,
            used_when=entry.used_when,
            used_from_ip=entry.used_from_ip,
            used_from_host=entry.used_from_host
        )
        
        self.session.add(new_token)
        return entry
    
    def email_verified(self, timestampL: datetime | None = None, remote_ip: str = "", remote_host: str = "",
                       session_id: str = None) -> bool:
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
            
        # Find the most recent unused token
        # Since the list is already ordered by issued_when desc, we can find the first unused token
        unused_token = None
        for token in self.email_history:
            if not token.used:
                unused_token = token
                break
                
        if unused_token is None:
            logger.warning(f"No unused email tokens found for user {self.user_id}")
            return False
        
        # Get the corresponding database record
        db_token = (
            self.session.query(TapirEmailChangeToken)
            .filter(
                TapirEmailChangeToken.user_id == self.user_id,
                TapirEmailChangeToken.new_email == unused_token.new_email,
                TapirEmailChangeToken.secret == unused_token.secret,
                TapirEmailChangeToken.used == False  # This ensures we only update if it's still unused
            )
            .first()
        )
        
        if not db_token:
            logger.warning(f"Could not find the unused token in the database for user {self.user_id}")
            return False
        
        # Get current timestamp
        now = datetime.now(tz=timezone.utc)
        unix_timestamp = int(time.time())  # Convert to Unix timestamp for used_when
            
        try:
            # Begin transaction
            
            # 1. Update the token as used
            db_token.used = True
            db_token.used_when = now
            db_token.used_from_ip = remote_ip
            db_token.used_from_host = remote_host
            
            # 2. Insert a record into the tapir_email_change_tokens_used table
            # Using the raw SQL connection to insert directly into the table
            self.session.execute(
                t_tapir_email_change_tokens_used.insert().values(
                    user_id=int(self.user_id),
                    secret=unused_token.secret,
                    used_when=unix_timestamp,
                    used_from=remote_ip[:16] if remote_ip else "",  # Limit to 16 chars as per schema
                    remote_host=remote_host[:255] if remote_host else "",  # Limit to 255 chars as per schema
                    session_id=session_id
                )
            )
            
            # 3. Also update the user's email_verified flag
            user = self.session.query(TapirUser).filter(TapirUser.user_id == self.user_id).one_or_none()
            if user:
                if not user.flag_email_verified:
                    user.flag_email_verified = True
                    logger.info(f"User {self.user_id} email flag marked as verified")
            
            logger.info(f"Email change token for user {self.user_id} marked as verified")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to mark email token as verified for user {self.user_id}: {str(e)}")
            return False


    def generate_email_verify_token(self, entry: EmailHistoryEntry) -> str:
        """
        Generates a unique email verification token.
        
        This function tries to generate a unique token by calling the global 
        generate_email_verify_token() function. It checks if the token already exists, 
        and if it does, it generates another one. If the token is unique, it adds an 
        entry to the tapir_email_change_tokens_used table.
        
        Returns:
            str: A unique email verification token
        """
        # Import at function level to avoid circular imports

        
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
                            used_from=entry.remote_addr,
                            remote_host=entry.remote_host,
                            session_id=0
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

