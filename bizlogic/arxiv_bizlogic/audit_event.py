"""
Tapir Admin audit event interface

Each admin event is represented vy a sub-class of AdminAuditEvent.
"""

import re
from abc import abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Tuple, Dict, Callable

from poetry.console.commands import self
from sqlalchemy.orm import Session
from arxiv.db.models import TapirAdminAudit
from .user_status import UserVetoStatus, UserFlags
from .validation.email_validation import is_valid_email
from inspect import isfunction


class AdminActionEnum(str, Enum):
    """Enumeration of admin actions that can be audited in the system.
    
    This enum defines all possible administrative actions that can be performed
    and logged in the audit trail. Each action corresponds to a specific
    administrative operation that affects users, papers, or system state.
    """
    ADD_COMMENT = "add-comment"
    ADD_PAPER_OWNER = "add-paper-owner"
    ADD_PAPER_OWNER_2 = "add-paper-owner-2"
    ARXIV_CHANGE_PAPER_PW = "arXiv-change-paper-pw"
    ARXIV_CHANGE_STATUS = "arXiv-change-status"
    ARXIV_MAKE_AUTHOR = "arXiv-make-author"
    ARXIV_MAKE_NONAUTHOR = "arXiv-make-nonauthor"
    ARXIV_REVOKE_PAPER_OWNER = "arXiv-revoke-paper-owner"
    ARXIV_UNREVOKE_PAPER_OWNER = "arXiv-unrevoke-paper-owner"
    BECOME_USER = "become-user"
    CHANGE_EMAIL = "change-email"
    CHANGE_PAPER_PW = "change-paper-pw"
    CHANGE_PASSWORD = "change-password"
    ENDORSED_BY_SUSPECT = "endorsed-by-suspect"
    FLIP_FLAG = "flip-flag"
    GOT_NEGATIVE_ENDORSEMENT = "got-negative-endorsement"
    MAKE_MODERATOR = "make-moderator"
    REVOKE_PAPER_OWNER = "revoke-paper-owner"
    SUSPEND_USER = "suspend-user"
    UNMAKE_MODERATOR = "unmake-moderator"
    UNSUSPEND_USER = "unsuspend-user"

#
# create table tapir_admin_audit
# (
#     log_date        int unsigned default '0' not null,
#     session_id      int unsigned             null,
#     ip_addr         varchar(16)  default ''  not null,
#     remote_host     varchar(255) default ''  not null,
#     admin_user      int unsigned             null,
#     affected_user   int unsigned default '0' not null,
#     tracking_cookie varchar(255) default ''  not null,
#     action          varchar(32)  default ''  not null,
#     data            text                     not null,
#     comment         text                     not null,
#     entry_id        int unsigned auto_increment
#         primary key,
#     constraint `0_553`
#         foreign key (session_id) references tapir_sessions (session_id),
#     constraint `0_554`
#         foreign key (admin_user) references tapir_users (user_id),
#     constraint `0_555`
#         foreign key (affected_user) references tapir_users (user_id)
# )

class AdminAuditEvent:
    """Base class for all administrative audit events.
    
    This abstract base class defines the common structure and interface
    for all audit events in the system. Each audit event captures information
    about an administrative action including who performed it, who was affected,
    when it occurred, and relevant session/network information.
    
    Attributes:
        timestamp: Unix timestamp when the event occurred
        admin_user: ID of the administrator performing the action
        affected_user: ID of the user being affected by the action
        session_id: Optional session ID associated with the action
        remote_ip: Optional IP address of the administrator
        remote_hostname: Optional hostname of the administrator
        tracking_cookie: Optional tracking cookie for the session
        _comment: Optional comment associated with the action
    """
    timestamp: int
    admin_user: str
    affected_user: str
    session_id: Optional[str]
    remote_ip: Optional[str]
    remote_hostname: Optional[str]
    tracking_cookie: Optional[str]
    _comment: Optional[str]
    _data: Optional[str]

    def __init__(self,
                 admin_id: str,
                 affected_user: str,
                 session_id: str,
                 remote_ip: str | None = None,
                 remote_hostname: str | None = None,
                 tracking_cookie: str | None = None,
                 comment: str | None = None,
                 data: str | None = None,
                 timestamp: int | None = None):
        self.admin_user = admin_id
        self.affected_user = affected_user
        self.session_id = session_id
        if timestamp is None:
            timestamp = int(datetime.now(tz=timezone.utc).timestamp())
        self.timestamp = timestamp
        self.remote_ip = remote_ip
        self.remote_hostname = remote_hostname
        self.tracking_cookie = tracking_cookie
        self._comment = comment
        self._data = data
        pass


    @property
    def comment(self) -> str:
        return self._comment

    @property
    def data(self) -> str:
        return self._data

    @property
    def action(self) -> AdminActionEnum:
        return self.__class__._action

    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        """
        Generate constructor parameters from an audit record.

        This method can be overridden by subclasses to provide custom
        parameter generation for their __init__ methods.

        Args:
            audit_record: The TapirAdminAudit database record

        Returns:
            A tuple of (args, kwargs) for the constructor
        """
        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "data": audit_record.data,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
        }



class AdminAudit_PaperEvent(AdminAuditEvent):
    """Base class for audit events related to paper ownership and management.

    This class handles audit events that involve paper-related actions,
    storing the paper ID as the data field and validating it as an integer.

    Attributes:
        _data: The paper ID associated with this event
    """

    def __init__(self, *args, **kwargs):
        data = kwargs.pop("paper_id")
        kwargs['data'] = data
        super().__init__(*args, **kwargs)
        pass

    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        """
        Generate constructor parameters from an audit record.

        This method can be overridden by subclasses to provide custom
        parameter generation for their __init__ methods.

        Args:
            audit_record: The TapirAdminAudit database record

        Returns:
            A tuple of (args, kwargs) for the constructor
        """
        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "paper_id": audit_record.data,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
        }


class AdminAudit_AddPaperOwner(AdminAudit_PaperEvent):
    """Audit event for adding a paper owner to a submission."""
    _action = AdminActionEnum.ADD_PAPER_OWNER


class AdminAudit_AddPaperOwner2(AdminAudit_PaperEvent):
    """Audit event for adding a secondary paper owner to a submission."""
    _action = AdminActionEnum.ADD_PAPER_OWNER_2


class AdminAudit_ChangePaperPassword(AdminAudit_PaperEvent):
    """Audit event for changing a paper's password."""
    _action = AdminActionEnum.CHANGE_PAPER_PW

class AdminAudit_AdminChangePaperPassword(AdminAudit_PaperEvent):
    """Audit event for changing a paper's password."""
    _action =  AdminActionEnum.ARXIV_CHANGE_PAPER_PW

class AdminAudit_AdminMakeAuthor(AdminAudit_PaperEvent):
    """Audit event for making a user an author of a paper."""
    _action = AdminActionEnum.ARXIV_MAKE_AUTHOR

class AdminAudit_AdminMakeNonauthor(AdminAudit_PaperEvent):
    """Audit event for removing a user's authorship of a paper."""
    _action = AdminActionEnum.ARXIV_MAKE_NONAUTHOR


class AdminAudit_AdminRevokePaperOwner(AdminAudit_PaperEvent):
    """Audit event for revoking a user's paper ownership."""
    _action = AdminActionEnum.ARXIV_REVOKE_PAPER_OWNER


class AdminAudit_AdminUnrevokePaperOwner(AdminAudit_PaperEvent):
    """Audit event for restoring a user's paper ownership."""
    _action = AdminActionEnum.ARXIV_UNREVOKE_PAPER_OWNER


class AdminAudit_BecomeUser(AdminAuditEvent):
    """Audit event for when an admin becomes another user.
    
    This event is logged when an administrator uses the 'become user'
    functionality to impersonate another user for support purposes.
    The new session ID is stored as data.
    """
    _action = AdminActionEnum.BECOME_USER

    def __init__(self, *argc, **kwargs):
        data = str(kwargs.pop("new_session_id"))
        _ = int(data)
        kwargs["data"] = data
        super().__init__(*argc, **kwargs)
        pass

    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        """
        Generate constructor parameters from an audit record.

        This method can be overridden by subclasses to provide custom
        parameter generation for their __init__ methods.

        Args:
            audit_record: The TapirAdminAudit database record

        Returns:
            A tuple of (args, kwargs) for the constructor
        """
        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "new_session_id": audit_record.data,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
        }

class AdminAudit_ChangeEmail(AdminAuditEvent):
    """Audit event for changing a user's email address.
    
    This event is logged when an administrator changes a user's email address.
    The new email address is validated and stored as data.
    
    Raises:
        ValueError: If the provided email address is not valid
    """
    _action = AdminActionEnum.CHANGE_EMAIL

    def __init__(self, *argc, **kwargs):
        data = str(kwargs.pop("email"))
        if not is_valid_email(data):
            raise ValueError(f"email '{data}' is not a valid email")
        kwargs["data"] = data
        super().__init__(*argc, **kwargs)
        pass

    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        """
        Generate constructor parameters from an audit record.

        This method can be overridden by subclasses to provide custom
        parameter generation for their __init__ methods.

        Args:
            audit_record: The TapirAdminAudit database record

        Returns:
            A tuple of (args, kwargs) for the constructor
        """
        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "email": audit_record.data,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
        }


class AdminAudit_ChangePassword(AdminAuditEvent):
    """Audit event for changing a user's password.
    
    This event is logged when an administrator changes a user's password.
    No additional data or comment is stored for security reasons.
    """
    _action = AdminActionEnum.CHANGE_PASSWORD


class AdminAudit_SetFlag(AdminAuditEvent):
    """Audit event for setting or unsetting a user flag.
    
    This event is logged when an administrator modifies a user's flags
    (such as banned, approved, etc.). The flag name and value are stored as data.
    
    Args:
        flag: The UserFlag being modified
        value: The new value for the flag
        
    Raises:
        ValueError: If the flag is not a valid UserFlags enum
    """
    _action = AdminActionEnum.FLIP_FLAG
    _flag: UserFlags
    _value_name: str
    _value_type: type

    def __init__(self, *argc, **kwargs):
        if not hasattr(self, "_value_type"):
            raise NotImplementedError(f"AdminAudit_SetFlag is a base class and should not be instantiated directly")

        if self._value_type is bool:
            value = kwargs.pop(self._value_name)
            if isinstance(value, str):
                normalized = value.lower() in ("yes", "true", "1")
            elif isinstance(value, int):
                normalized = value != 0
            elif isinstance(value, bool):
                normalized = value
            else:
                raise ValueError(f"Invalid value type for flag {self._flag.value}: {type(value)}")
            boolean_value = 1 if normalized else 0
            data = f"{self._flag.value}={boolean_value}"
        elif self._value_type is int:
            data = f"{self._flag.value}={kwargs.pop(self._value_name)}"
        elif self._value_type is str:
            data = f"{self._flag.value}={kwargs.pop(self._value_name)}"
        else:
            raise NotImplementedError(f"Unsupported flag type: {self._value_type}")
        kwargs["data"] = data
        if "flag" in kwargs:
            _ = kwargs.pop("flag")
        if "value" in kwargs:
            _ = kwargs.pop("value")
        super().__init__(*argc, **kwargs)
        pass


    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        """
        Generate constructor parameters from an audit record.

        This method can be overridden by subclasses to provide custom
        parameter generation for their __init__ methods.

        Args:
            audit_record: The TapirAdminAudit database record

        Returns:
            A tuple of (args, kwargs) for the constructor
        """
        data = audit_record.data.split("=")
        if len(data) != 2:
            raise ValueError(f"data '{audit_record.data}' is not a valid flag=value")
        flag = UserFlags(data[0])
        value = data[1]

        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "flag": flag,
            "value": value,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
        }


class AdminAudit_EndorseEvent(AdminAuditEvent):
    """Base class for audit events related to user endorsements.
    
    This class handles audit events that involve endorsement actions,
    storing the endorser ID, endorsee ID, and category as data.
    
    Args:
        endorser: ID of the user providing the endorsement
        endorsee: ID of the user receiving the endorsement
        category: The subject category for the endorsement
    """
    def __init__(self, *argc, **kwargs):
        endorser_id = kwargs.pop("endorser")
        _ = int(endorser_id)
        endorsee_id = kwargs.pop("endorsee")
        _ = int(endorsee_id)
        category = kwargs.pop("category")
        data = f"{endorser_id} {category} {endorsee_id}"
        kwargs["data"] = data
        super().__init__(*argc, **kwargs)
        pass

    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        """
        Generate constructor parameters from an audit record.

        This method can be overridden by subclasses to provide custom
        parameter generation for their __init__ methods.

        Args:
            audit_record: The TapirAdminAudit database record

        Returns:
            A tuple of (args, kwargs) for the constructor
        """
        data = audit_record.data.split(" ")
        if len(data) != 3:
            raise ValueError(f"data '{audit_record.data}' is not valid")
        endorser = data[0]
        category = data[1]
        endorsee = data[2]

        if not re.match(r"^\d+$", endorser) or \
                not re.match(r"^\d+$", endorsee) or \
                not re.match(r"[\w\-]+\..*", category):
            raise ValueError(f"data '{audit_record.data}' is not valid")

        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "endorser": endorser,
            "endorsee": endorsee,
            "category": category,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
        }


class AdminAudit_EndorsedBySuspect(AdminAudit_EndorseEvent):
    """Audit event for when a user is endorsed by a suspect user."""
    _action = AdminActionEnum.ENDORSED_BY_SUSPECT


class AdminAudit_GotNegativeEndorsement(AdminAudit_EndorseEvent):
    """Audit event for when a user receives a negative endorsement."""
    _action = AdminActionEnum.GOT_NEGATIVE_ENDORSEMENT


class AdminAudit_MakeModerator(AdminAuditEvent):
    """Audit event for making a user a moderator.
    
    This event is logged when an administrator grants moderator privileges
    to a user for a specific category. The category is stored as data.
    
    Args:
        category: The subject category for which the user is being made a moderator
    """
    _action = AdminActionEnum.MAKE_MODERATOR

    def __init__(self, *argc, **kwargs):
        category = kwargs.pop("category")
        data = f"{category}"
        kwargs["data"] = data
        super().__init__(*argc, **kwargs)
        pass

    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        category = audit_record.data

        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "category": category,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
        }


class AdminAudit_UnmakeModerator(AdminAuditEvent):
    """Audit event for removing a user's moderator privileges.
    
    This event is logged when an administrator revokes moderator privileges
    from a user for a specific category. The category is stored as data.
    
    Args:
        category: The subject category for which the user's moderator privileges are being revoked
    """
    _action = AdminActionEnum.UNMAKE_MODERATOR

    def __init__(self, *argc, **kwargs):
        category = kwargs.pop("category")
        data = f"{category}"
        kwargs["data"] = data
        super().__init__(*argc, **kwargs)
        pass

    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        category = audit_record.data

        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "category": category,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
        }


class AdminAudit_SuspendUser(AdminAuditEvent):
    """Audit event for suspending a user.
    
    This event is logged when an administrator suspends a user account.
    The banned flag is automatically set to 1 and a comment is required
    to explain the reason for suspension.
    """
    _action = AdminActionEnum.SUSPEND_USER

    def __init__(self, *argc, **kwargs):
        data = f'{UserFlags.TAPIR_FLAG_BANNED.value}=1'
        kwargs["data"] = data
        super().__init__(*argc, **kwargs)

    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        category = audit_record.data

        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
        }

class AdminAudit_UnuspendUser(AdminAuditEvent):
    """Audit event for unsuspending a user.
    
    This event is logged when an administrator removes a user's suspension.
    The banned flag is automatically set to 0 and a comment is required
    to explain the reason for unsuspension.
    """
    _action = AdminActionEnum.UNSUSPEND_USER

    def __init__(self, *argc, **kwargs):
        data = f'{UserFlags.TAPIR_FLAG_BANNED.value}=0'
        kwargs["data"] = data
        super().__init__(*argc, **kwargs)

    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        category = audit_record.data

        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
        }


class AdminAudit_ChangeStatus(AdminAuditEvent):
    """Audit event for changing a user's status.
    
    This event is logged when an administrator changes a user's veto status.
    The before and after status values are stored as data in the format
    'before_status -> after_status'.
    
    Args:
        status_before: The user's status before the change
        status_after: The user's status after the change
        
    Raises:
        ValueError: If either status is not a valid UserVetoStatus enum
    """
    _action = AdminActionEnum.ARXIV_CHANGE_STATUS

    def __init__(self, *argc, **kwargs):
        status_before = kwargs.pop("status_before")
        status_after = kwargs.pop("status_after")
        if not isinstance(status_before, UserVetoStatus):
            raise ValueError(f"status_before '{status_before!r}' is not a UserStatus'")
        if not isinstance(status_after, UserVetoStatus):
            raise ValueError(f"status_after '{status_after!r}' is not a UserStatus'")
        data = f"{status_before.value} -> {status_after.value}"
        kwargs["data"] = data
        super().__init__(*argc, **kwargs)
        pass

    @classmethod
    def get_init_params(cls, audit_record: TapirAdminAudit) -> Tuple[list, dict]:
        # data = f"{status_before.value} -> {status_after.value}"
        match = re.match(r"([\w\-]+) -> ([\w\-]+)", audit_record.data)

        if not match:
            raise ValueError(f"Invalid status change format: {audit_record.data}")

        status_before = UserVetoStatus(match.group(1))
        status_after = UserVetoStatus(match.group(2))

        return [
            audit_record.admin_user,
            audit_record.affected_user,
            audit_record.session_id,
        ], {
            "comment": audit_record.comment,
            "remote_ip": audit_record.ip_addr,
            "remote_hostname": audit_record.remote_host,
            "tracking_cookie": audit_record.tracking_cookie,
            "timestamp": audit_record.log_date,
            "status_before": status_before,
            "status_after": status_after,
        }


class AdminAudit_SetGroupTest(AdminAudit_SetFlag):
    _flag = UserFlags.ARXIV_FLAG_GROUP_TEST
    _value_name = "group_test"
    _value_type = bool

class AdminAudit_SetProxy(AdminAudit_SetFlag):
    _flag = UserFlags.ARXIV_FLAG_PROXY
    _value_name = "proxy"
    _value_type = bool

class AdminAudit_SetSuspect(AdminAudit_SetFlag):
    _flag = UserFlags.ARXIV_FLAG_SUSPECT
    _value_name = "suspect"
    _value_type = bool

class AdminAudit_SetXml(AdminAudit_SetFlag):
    _flag = UserFlags.ARXIV_FLAG_XML
    _value_name = "xml"
    _value_type = bool

class AdminAudit_SetEndorsementValid(AdminAudit_SetFlag):
    _flag = UserFlags.ARXIV_ENDORSEMENT_FLAG_VALID
    _value_name = "endorsement_valid"
    _value_type = bool

class AdminAudit_SetPointValue(AdminAudit_SetFlag):
    _flag = UserFlags.ARXIV_ENDORSEMENT_POINT_VALUE
    _value_name = "point_value"
    _value_type = int

class AdminAudit_SetEndorsementRequestsValid(AdminAudit_SetFlag):
    _flag = UserFlags.ARXIV_ENDORSEMENT_REQUEST_FLAG_VALID
    _value_name = "endorsement_requests_valid"
    _value_type = bool

class AdminAudit_SetEmailBouncing(AdminAudit_SetFlag):
    _flag = UserFlags.TAPIR_EMAIL_BOUNCING
    _value_name = "email_bouncing"
    _value_type = bool

class AdminAudit_SetBanned(AdminAudit_SetFlag):
    _flag = UserFlags.TAPIR_FLAG_BANNED
    _value_name = "banned"
    _value_type = bool

class AdminAudit_SetEditSystem(AdminAudit_SetFlag):
    _flag = UserFlags.TAPIR_FLAG_EDIT_SYSTEM
    _value_name = "edit_system"
    _value_type = bool

class AdminAudit_SetEditUsers(AdminAudit_SetFlag):
    _flag = UserFlags.TAPIR_FLAG_EDIT_USERS
    _value_name = "edit_users"
    _value_type = bool

class AdminAudit_SetEmailVerified(AdminAudit_SetFlag):
    _flag = UserFlags.TAPIR_FLAG_EMAIL_VERIFIED
    _value_name = "verified"
    _value_type = bool



def admin_audit(session: Session,
                event: AdminAuditEvent,
                admin_user: str,
                affected_user: str,
                session_id: str | None = None,
                remote_ip: str | None = None,
                remote_hostname: str | None = None,
                tracking_cookie: str | None = None,
                timestamp: int | None = None,):
    """
    Audit function for admin actions.
    
    This function logs an administrative action to the audit trail by creating
    a new entry in the TapirAdminAudit table. It captures all relevant information
    about the action including who performed it, who was affected, when it occurred,
    and any additional context.

    Args:
        session: SQLAlchemy database session for persisting the audit record
        event: The AdminAuditEvent containing action details and data
        admin_user: ID of the administrator performing the action
        affected_user: ID of the user being affected by the action
        session_id: Optional session ID associated with the admin action
        remote_ip: Optional IP address of the administrator
        remote_hostname: Optional hostname of the administrator
        tracking_cookie: Optional tracking cookie for session correlation
        timestamp: Optional timestamp; if None, current UTC time is used
    """
    # Prepare session_id for SQL
    if not session_id:
        _session_id = None
    else:
        _session_id = f"'{session_id}'"

    entry = TapirAdminAudit(
        log_date=timestamp,
        session_id=_session_id,
        ip_addr=remote_ip,
        remote_host=remote_hostname,
        admin_user=admin_user,
        affected_user=affected_user,
        tracking_cookie=tracking_cookie,
        action=event.action,
        data=event.data,
        comment=event.comment,
    )
    session.add(entry)


set_flag_event_classes: Dict[str, AdminAuditEvent] = {
    cls._flag.value : cls for cls in [
        AdminAudit_SetGroupTest,
        AdminAudit_SetProxy,
        AdminAudit_SetSuspect,
        AdminAudit_SetXml,
        AdminAudit_SetEndorsementValid,
        AdminAudit_SetPointValue,
        AdminAudit_SetEndorsementRequestsValid,
        AdminAudit_SetEmailBouncing,
        AdminAudit_SetBanned,
        AdminAudit_SetEditSystem,
        AdminAudit_SetEditUsers,
        AdminAudit_SetEmailVerified,
    ]
}


def admin_audit_flip_flag_instantiator(audit_record: TapirAdminAudit) -> AdminAuditEvent:
    args, kwargs = AdminAudit_SetFlag.get_init_params(audit_record)
    flag = kwargs["flag"]
    value = kwargs["value"]
    event_class = set_flag_event_classes.get(flag)
    if not event_class:
        raise ValueError(f"{audit_record.action}.{flag} is not a valid admin action of flip flag")
    if not hasattr(event_class, "_value_name"):
        raise NotImplementedError(f"AdminAudit_SetFlag is a base class and not intended to be instantiated directly")
    value_name = event_class._value_name
    kwargs.update({value_name: value})
    return event_class(*args, **kwargs)


event_classes: Dict[str, AdminAuditEvent] = {
    cls._action.value : cls for cls in [
        AdminAudit_AddPaperOwner,
        AdminAudit_AddPaperOwner2,
        AdminAudit_ChangePaperPassword,
        AdminAudit_AdminMakeAuthor,
        AdminAudit_AdminMakeNonauthor,
        AdminAudit_AdminRevokePaperOwner,
        AdminAudit_AdminUnrevokePaperOwner,
        AdminAudit_BecomeUser,
        AdminAudit_ChangeEmail,
        AdminAudit_ChangePassword,
        AdminAudit_EndorsedBySuspect,
        AdminAudit_GotNegativeEndorsement,
        AdminAudit_MakeModerator,
        AdminAudit_UnmakeModerator,
        AdminAudit_SuspendUser,
        AdminAudit_UnuspendUser,
        AdminAudit_ChangeStatus,
        AdminAudit_AdminChangePaperPassword,
        AdminAudit_SetEmailVerified,
    ]
} | {
    AdminActionEnum.FLIP_FLAG.value: admin_audit_flip_flag_instantiator
}


def create_admin_audit_event(audit_record: TapirAdminAudit) -> AdminAuditEvent:
    """
    Create an AdminAuditEvent instance from a TapirAdminAudit database record.

    This function is the reverse of admin_audit(). It examines the action type
    in the audit record and instantiates the appropriate AdminAuditEvent subclass.

    Args:
        audit_record: The TapirAdminAudit database record

    Returns:
        An instance of the appropriate AdminAuditEvent subclass
    """


    # Find the appropriate event class or use this base class as fallback
    event_class = event_classes.get(audit_record.action)
    if not event_class:
        raise ValueError(f"{audit_record.action} is not a valid admin action")

    if isfunction(event_class):
        return event_class(audit_record)

    args, kwargs = event_class.get_init_params(audit_record)
    return event_class(*args, **kwargs)
