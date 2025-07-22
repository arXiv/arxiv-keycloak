import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from unittest import TestCase

from arxiv.db.models import TapirAdminAudit
from bizlogic.arxiv_bizlogic.audit_event import (
    create_admin_audit_event,
    AdminAuditActionEnum,
    AdminAudit_AddPaperOwner,
    AdminAudit_AddPaperOwner2,
    AdminAudit_ChangePaperPassword,
    AdminAudit_AdminChangePaperPassword,
    AdminAudit_AdminMakeAuthor,
    AdminAudit_AdminMakeNonauthor,
    AdminAudit_AdminRevokePaperOwner,
    AdminAudit_AdminUnrevokePaperOwner,
    AdminAudit_BecomeUser,
    AdminAudit_ChangeEmail,
    AdminAudit_ChangePassword,
    AdminAudit_SetFlag,
    AdminAudit_EndorsedBySuspect,
    AdminAudit_GotNegativeEndorsement,
    AdminAudit_MakeModerator,
    AdminAudit_UnmakeModerator,
    AdminAudit_SuspendUser,
    AdminAudit_UnuspendUser,
    AdminAudit_ChangeStatus,

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
)


def create_base_audit_record(**kwargs):
    """Factory function to create TapirAdminAudit test data."""
    defaults = {
        'log_date': int(datetime.now(tz=timezone.utc).timestamp()),
        'session_id': 12345,
        'ip_addr': '192.168.1.1',
        'remote_host': 'test.example.com',
        'admin_user': 100,
        'affected_user': 200,
        'tracking_cookie': 'test_cookie_123',
        'data': 'test_data',
        'comment': 'Test comment',
        'entry_id': 1,
        'action': "test-bug"
    }
    defaults.update(kwargs)
    
    audit_record = Mock(spec=TapirAdminAudit)
    for key, value in defaults.items():
        setattr(audit_record, key, value)
    
    return audit_record


class TestCreateAdminAuditEvent(TestCase):
    """Test suite for create_admin_audit_event function."""
    
    def test_invalid_action_raises_error(self):
        """Test that invalid action raises ValueError."""
        audit_record = create_base_audit_record(action="invalid-action")
        
        with pytest.raises(ValueError, match="invalid-action is not a valid admin action"):
            create_admin_audit_event(audit_record)
    
    def test_add_paper_owner_event(self):
        """Test creating AdminAudit_AddPaperOwner event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ADD_PAPER_OWNER.value,
            data="12345",
            comment="Added paper owner"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_AddPaperOwner)
        assert event.action == AdminAuditActionEnum.ADD_PAPER_OWNER
        assert event.data == "12345"
        assert event.comment == "Added paper owner"
        assert event.admin_user == 100
        assert event.affected_user == 200
    
    def test_add_paper_owner_2_event(self):
        """Test creating AdminAudit_AddPaperOwner2 event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ADD_PAPER_OWNER_2.value,
            data="67890",
            comment="Added secondary paper owner"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_AddPaperOwner2)
        assert event.action == AdminAuditActionEnum.ADD_PAPER_OWNER_2
        assert event.data == "67890"
    
    def test_change_paper_password_event(self):
        """Test creating AdminAudit_ChangePaperPassword event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.CHANGE_PAPER_PW.value,
            data="paper123",
            comment="Changed paper password"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_ChangePaperPassword)
        assert event.action == AdminAuditActionEnum.CHANGE_PAPER_PW
        assert event.data == "paper123"
    
    def test_admin_change_paper_password_event(self):
        """Test creating AdminAudit_AdminChangePaperPassword event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_CHANGE_PAPER_PW.value,
            data="paper456",
            comment="Admin changed paper password"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_AdminChangePaperPassword)
        assert event.action == AdminAuditActionEnum.ARXIV_CHANGE_PAPER_PW
        assert event.data == "paper456"
    
    def test_admin_make_author_event(self):
        """Test creating AdminAudit_AdminMakeAuthor event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_MAKE_AUTHOR.value,
            data="paper789",
            comment="Made user an author"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_AdminMakeAuthor)
        assert event.action == AdminAuditActionEnum.ARXIV_MAKE_AUTHOR
        assert event.data == "paper789"
    
    def test_admin_make_nonauthor_event(self):
        """Test creating AdminAudit_AdminMakeNonauthor event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_MAKE_NONAUTHOR.value,
            data="paper101",
            comment="Removed user authorship"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_AdminMakeNonauthor)
        assert event.action == AdminAuditActionEnum.ARXIV_MAKE_NONAUTHOR
        assert event.data == "paper101"
    
    def test_admin_revoke_paper_owner_event(self):
        """Test creating AdminAudit_AdminRevokePaperOwner event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_REVOKE_PAPER_OWNER.value,
            data="paper202",
            comment="Revoked paper ownership"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_AdminRevokePaperOwner)
        assert event.action == AdminAuditActionEnum.ARXIV_REVOKE_PAPER_OWNER
        assert event.data == "paper202"
    
    def test_admin_unrevoke_paper_owner_event(self):
        """Test creating AdminAudit_AdminUnrevokePaperOwner event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_UNREVOKE_PAPER_OWNER.value,
            data="paper303",
            comment="Restored paper ownership"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_AdminUnrevokePaperOwner)
        assert event.action == AdminAuditActionEnum.ARXIV_UNREVOKE_PAPER_OWNER
        assert event.data == "paper303"
    
    def test_become_user_event(self):
        """Test creating AdminAudit_BecomeUser event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.BECOME_USER.value,
            data="54321",
            comment="Admin became user"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_BecomeUser)
        assert event.action == AdminAuditActionEnum.BECOME_USER
        assert event.data == "54321"
    
    def test_change_email_event(self):
        """Test creating AdminAudit_ChangeEmail event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.CHANGE_EMAIL.value,
            data="test@example.com",
            comment="Changed user email"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_ChangeEmail)
        assert event.action == AdminAuditActionEnum.CHANGE_EMAIL
        assert event.data == "test@example.com"
    
    def test_change_password_event(self):
        """Test creating AdminAudit_ChangePassword event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.CHANGE_PASSWORD.value,
            data="",
            comment="Changed user password"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_ChangePassword)
        assert event.action == AdminAuditActionEnum.CHANGE_PASSWORD
    
    def test_set_flag_event(self):
        """Test creating AdminAudit_SetFlag event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.flag_banned=1",
            comment="Set user flag"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetFlag)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "tapir_users.flag_banned=1"
    
    def test_set_flag_event_invalid_data(self):
        """Test creating AdminAudit_SetFlag event with invalid data format."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="invalid_data",
            comment="Set user flag"
        )
        
        with pytest.raises(ValueError, match="data 'invalid_data' is not a valid flag=value"):
            create_admin_audit_event(audit_record)
    
    def test_endorsed_by_suspect_event(self):
        """Test creating AdminAudit_EndorsedBySuspect event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ENDORSED_BY_SUSPECT.value,
            data="123 cs.AI 456",
            comment="User endorsed by suspect"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_EndorsedBySuspect)
        assert event.action == AdminAuditActionEnum.ENDORSED_BY_SUSPECT
        assert event.data == "123 cs.AI 456"
    
    def test_endorsed_by_suspect_invalid_data(self):
        """Test creating AdminAudit_EndorsedBySuspect event with invalid data format."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ENDORSED_BY_SUSPECT.value,
            data="invalid data format",
            comment="User endorsed by suspect"
        )
        
        with pytest.raises(ValueError, match="data 'invalid data format' is not valid"):
            create_admin_audit_event(audit_record)
    
    def test_got_negative_endorsement_event(self):
        """Test creating AdminAudit_GotNegativeEndorsement event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.GOT_NEGATIVE_ENDORSEMENT.value,
            data="789 math.CO 101",
            comment="User got negative endorsement"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_GotNegativeEndorsement)
        assert event.action == AdminAuditActionEnum.GOT_NEGATIVE_ENDORSEMENT
        assert event.data == "789 math.CO 101"
    
    def test_make_moderator_event(self):
        """Test creating AdminAudit_MakeModerator event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.MAKE_MODERATOR.value,
            data="cs.AI",
            comment="Made user a moderator"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_MakeModerator)
        assert event.action == AdminAuditActionEnum.MAKE_MODERATOR
        assert event.data == "cs.AI"
    
    def test_unmake_moderator_event(self):
        """Test creating AdminAudit_UnmakeModerator event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.UNMAKE_MODERATOR.value,
            data="math.CO",
            comment="Removed moderator privileges"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_UnmakeModerator)
        assert event.action == AdminAuditActionEnum.UNMAKE_MODERATOR
        assert event.data == "math.CO"
    
    def test_suspend_user_event(self):
        """Test creating AdminAudit_SuspendUser event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.SUSPEND_USER.value,
            data="tapir_users.flag_banned=1",
            comment="Suspended user"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SuspendUser)
        assert event.action == AdminAuditActionEnum.SUSPEND_USER
        assert event.data == "tapir_users.flag_banned=1"
    
    def test_unsuspend_user_event(self):
        """Test creating AdminAudit_UnuspendUser event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.UNSUSPEND_USER.value,
            data="tapir_users.flag_banned=0",
            comment="Unsuspended user"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_UnuspendUser)
        assert event.action == AdminAuditActionEnum.UNSUSPEND_USER
        assert event.data == "tapir_users.flag_banned=0"
    
    def test_change_status_event(self):
        """Test creating AdminAudit_ChangeStatus event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_CHANGE_STATUS.value,
            data="ok -> no-upload",
            comment="Changed user status"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_ChangeStatus)
        assert event.action == AdminAuditActionEnum.ARXIV_CHANGE_STATUS
        assert event.data == "ok -> no-upload"
    
    def test_all_required_fields_populated(self):
        """Test that all required fields are populated correctly."""
        timestamp = int(datetime.now(tz=timezone.utc).timestamp())
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ADD_PAPER_OWNER.value,
            log_date=timestamp,
            session_id=98765,
            ip_addr='10.0.0.1',
            remote_host='admin.example.com',
            admin_user=300,
            affected_user=400,
            tracking_cookie='admin_cookie_xyz',
            data="paper555",
            comment="Test audit event"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert event.timestamp == timestamp
        assert event.session_id == 98765
        assert event.remote_ip == '10.0.0.1'
        assert event.remote_hostname == 'admin.example.com'
        assert event.admin_user == 300
        assert event.affected_user == 400
        assert event.tracking_cookie == 'admin_cookie_xyz'
        assert event.data == "paper555"
        assert event.comment == "Test audit event"
    
    def test_optional_fields_none(self):
        """Test handling of optional fields when they are None."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.CHANGE_PASSWORD.value,
            session_id=None,
            ip_addr=None,
            remote_host=None,
            tracking_cookie=None,
            data=None,
            comment=""
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert event.session_id is None
        assert event.remote_ip is None
        assert event.remote_hostname is None
        assert event.tracking_cookie is None
        assert event.data is None
        assert event.comment == ""


class TestAdminAuditEventClasses:
    """Test individual AdminAudit event classes."""
    
    def test_paper_event_construction(self):
        """Test paper event classes require paper_id."""
        with pytest.raises(KeyError):
            AdminAudit_AddPaperOwner("100", "200", "session123")
    
    def test_become_user_construction(self):
        """Test BecomeUser event requires new_session_id."""
        with pytest.raises(KeyError):
            AdminAudit_BecomeUser("100", "200", "session123")
    
    def test_change_email_construction(self):
        """Test ChangeEmail event requires email."""
        with pytest.raises(KeyError):
            AdminAudit_ChangeEmail("100", "200", "session123")
    
    def test_endorse_event_construction(self):
        """Test EndorseEvent requires endorser, endorsee, and category."""
        with pytest.raises(KeyError):
            AdminAudit_EndorsedBySuspect("100", "200", "session123")
    
    def test_make_moderator_construction(self):
        """Test MakeModerator event requires category."""
        with pytest.raises(KeyError):
            AdminAudit_MakeModerator("100", "200", "session123")
    
    def test_change_status_construction(self):
        """Test ChangeStatus event requires status_before and status_after."""
        with pytest.raises(KeyError):
            AdminAudit_ChangeStatus("100", "200", "session123")


class TestAdminAuditEventSetFlagClasses:

    def test_set_flag_construction_fail_1(self):
        """Test SetFlag event requires flag and value."""
        with pytest.raises(KeyError):
            AdminAudit_SetBanned("100", "200", "session123")
    
    def test_set_group_test_event(self):
        """Test creating AdminAudit_SetGroupTest event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_demographics.flag_group_test=1",
            comment="Set group test flag"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetGroupTest)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "arXiv_demographics.flag_group_test=1"
        assert event.comment == "Set group test flag"
    
    def test_set_proxy_event(self):
        """Test creating AdminAudit_SetProxy event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_demographics.flag_proxy=0",
            comment="Unset proxy flag"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetProxy)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "arXiv_demographics.flag_proxy=0"
    
    def test_set_suspect_event(self):
        """Test creating AdminAudit_SetSuspect event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_demographics.flag_suspect=1",
            comment="Mark user as suspect"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetSuspect)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "arXiv_demographics.flag_suspect=1"
    
    def test_set_xml_event(self):
        """Test creating AdminAudit_SetXml event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_demographics.flag_xml=1",
            comment="Enable XML flag"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetXml)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "arXiv_demographics.flag_xml=1"
    
    def test_set_endorsement_valid_event(self):
        """Test creating AdminAudit_SetEndorsementValid event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_endorsements.flag_valid=1",
            comment="Mark endorsement as valid"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetEndorsementValid)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "arXiv_endorsements.flag_valid=1"
    
    def test_set_point_value_event(self):
        """Test creating AdminAudit_SetPointValue event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_endorsements.point_value=5",
            comment="Set endorsement point value"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetPointValue)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "arXiv_endorsements.point_value=5"
    
    def test_set_endorsement_requests_valid_event(self):
        """Test creating AdminAudit_SetEndorsementRequestsValid event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_endorsement_requests.flag_valid=0",
            comment="Mark endorsement requests as invalid"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetEndorsementRequestsValid)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "arXiv_endorsement_requests.flag_valid=0"
    
    def test_set_email_bouncing_event(self):
        """Test creating AdminAudit_SetEmailBouncing event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.email_bouncing=1",
            comment="Mark email as bouncing"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetEmailBouncing)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "tapir_users.email_bouncing=1"
    
    def test_set_banned_event(self):
        """Test creating AdminAudit_SetBanned event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.flag_banned=1",
            comment="Ban user"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetBanned)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "tapir_users.flag_banned=1"
    
    def test_set_edit_system_event(self):
        """Test creating AdminAudit_SetEditSystem event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.flag_edit_system=1",
            comment="Grant system edit privileges"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetEditSystem)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "tapir_users.flag_edit_system=1"
    
    def test_set_edit_users_event(self):
        """Test creating AdminAudit_SetEditUsers event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.flag_edit_users=0",
            comment="Revoke user edit privileges"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetEditUsers)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "tapir_users.flag_edit_users=0"
    
    def test_set_email_verified_event(self):
        """Test creating AdminAudit_SetEmailVerified event."""
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.flag_email_verified=1",
            comment="Mark email as verified"
        )
        
        event = create_admin_audit_event(audit_record)
        
        assert isinstance(event, AdminAudit_SetEmailVerified)
        assert event.action == AdminAuditActionEnum.FLIP_FLAG
        assert event.data == "tapir_users.flag_email_verified=1"


@patch('bizlogic.arxiv_bizlogic.bizmodels.user_model.UserModel.one_user')
class TestAdminAuditEventDescribe:
    """Test suite for audit event describe() methods."""
    
    @classmethod
    def setup_class(cls):
        """Set up mock user lookup function for all tests."""
        def mock_user_lookup(session, user_id):
            mock_user = Mock()
            mock_user.user_id = user_id
            mock_user.email = f'{user_id}@example.com'
            mock_user.username = {
                "100": "admin_user",
                "200": "test_user"
            }.get(user_id, f'user_{user_id}')
            return mock_user
        cls.mock_user_lookup = staticmethod(mock_user_lookup)
    
    def test_add_paper_owner_describe(self, mock_one_user):
        """Test AdminAudit_AddPaperOwner describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ADD_PAPER_OWNER.value,
            data="12345",
            comment="Added paper owner"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "owner of paper" in description
        assert "12345" in description
    
    def test_add_paper_owner_2_describe(self, mock_one_user):
        """Test AdminAudit_AddPaperOwner2 describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ADD_PAPER_OWNER_2.value,
            data="67890",
            comment="Added secondary paper owner"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "owner of paper" in description
        assert "process-ownership screen" in description
        assert "67890" in description
    
    def test_change_paper_password_describe(self, mock_one_user):
        """Test AdminAudit_ChangePaperPassword describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.CHANGE_PAPER_PW.value,
            data="paper123",
            comment="Changed paper password"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "changed the paper password" in description
        assert "paper123" in description
    
    def test_admin_change_paper_password_describe(self, mock_one_user):
        """Test AdminAudit_AdminChangePaperPassword describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_CHANGE_PAPER_PW.value,
            data="paper456",
            comment="Admin changed paper password"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "changed the paper password" in description
        assert "paper456" in description
    
    def test_admin_make_author_describe(self, mock_one_user):
        """Test AdminAudit_AdminMakeAuthor describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_MAKE_AUTHOR.value,
            data="paper789",
            comment="Made user an author"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "made" in description
        assert "an author of" in description
        assert "paper789" in description
    
    def test_admin_make_nonauthor_describe(self, mock_one_user):
        """Test AdminAudit_AdminMakeNonauthor describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_MAKE_NONAUTHOR.value,
            data="paper101",
            comment="Removed user authorship"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "made" in description
        assert "nonauthor of" in description
        assert "paper101" in description
    
    def test_admin_revoke_paper_owner_describe(self, mock_one_user):
        """Test AdminAudit_AdminRevokePaperOwner describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_REVOKE_PAPER_OWNER.value,
            data="paper202",
            comment="Revoked paper ownership"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "revoked" in description
        assert "ownership of" in description
        assert "paper202" in description
    
    def test_admin_unrevoke_paper_owner_describe(self, mock_one_user):
        """Test AdminAudit_AdminUnrevokePaperOwner describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ARXIV_UNREVOKE_PAPER_OWNER.value,
            data="paper303",
            comment="Restored paper ownership"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "restored" in description
        assert "ownership of" in description
        assert "paper303" in description
    
    def test_become_user_describe(self, mock_one_user):
        """Test AdminAudit_BecomeUser describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.BECOME_USER.value,
            data="54321",
            comment="Admin became user"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "impersonated" in description
    
    def test_change_email_describe(self, mock_one_user):
        """Test AdminAudit_ChangeEmail describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.CHANGE_EMAIL.value,
            data="test@example.com",
            comment="Changed user email"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "changed email" in description
        assert "test@example.com" in description
    
    def test_change_password_describe(self, mock_one_user):
        """Test AdminAudit_ChangePassword describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.CHANGE_PASSWORD.value,
            data="",
            comment="Changed user password"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "changed password" in description
    
    def test_endorsed_by_suspect_describe(self, mock_one_user):
        """Test AdminAudit_EndorsedBySuspect describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.ENDORSED_BY_SUSPECT.value,
            data="123 cs.AI 456",
            comment="User endorsed by suspect"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "suspect" in description
        assert "endorsed" in description
        assert "cs.AI" in description
    
    def test_got_negative_endorsement_describe(self, mock_one_user):
        """Test AdminAudit_GotNegativeEndorsement describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.GOT_NEGATIVE_ENDORSEMENT.value,
            data="789 math.CO 101",
            comment="User got negative endorsement"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "suspect" in description
        assert "rejected" in description
        assert "endorsement request" in description
        assert "math.CO" in description
    
    def test_make_moderator_describe(self, mock_one_user):
        """Test AdminAudit_MakeModerator describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.MAKE_MODERATOR.value,
            data="cs.AI",
            comment="Made user a moderator"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "made" in description
        assert "moderator of" in description
        assert "cs.AI" in description
    
    def test_unmake_moderator_describe(self, mock_one_user):
        """Test AdminAudit_UnmakeModerator describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.UNMAKE_MODERATOR.value,
            data="math.CO",
            comment="Removed moderator privileges"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "removed" in description
        assert "moderator of" in description
        assert "math.CO" in description
    
    def test_suspend_user_describe(self, mock_one_user):
        """Test AdminAudit_SuspendUser describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.SUSPEND_USER.value,
            data="tapir_users.flag_banned=1",
            comment="Suspended user"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "suspended the account" in description
    
    def test_unsuspend_user_describe(self, mock_one_user):
        """Test AdminAudit_UnuspendUser describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.UNSUSPEND_USER.value,
            data="tapir_users.flag_banned=0",
            comment="Unsuspended user"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "unsuspended the account" in description
    
    def test_set_group_test_describe(self, mock_one_user):
        """Test AdminAudit_SetGroupTest describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_demographics.flag_group_test=1",
            comment="Set group test flag"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "arXiv_demographics.flag_group_test" in description
    
    def test_set_proxy_describe(self, mock_one_user):
        """Test AdminAudit_SetProxy describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_demographics.flag_proxy=0",
            comment="Unset proxy flag"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "arXiv_demographics.flag_proxy" in description
    
    def test_set_suspect_describe(self, mock_one_user):
        """Test AdminAudit_SetSuspect describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_demographics.flag_suspect=1",
            comment="Mark user as suspect"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "arXiv_demographics.flag_suspect" in description
    
    def test_set_xml_describe(self, mock_one_user):
        """Test AdminAudit_SetXml describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_demographics.flag_xml=1",
            comment="Enable XML flag"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "arXiv_demographics.flag_xml" in description
    
    def test_set_endorsement_valid_describe(self, mock_one_user):
        """Test AdminAudit_SetEndorsementValid describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_endorsements.flag_valid=1",
            comment="Mark endorsement as valid"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "arXiv_endorsements.flag_valid" in description
    
    def test_set_point_value_describe(self, mock_one_user):
        """Test AdminAudit_SetPointValue describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_endorsements.point_value=5",
            comment="Set endorsement point value"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "arXiv_endorsements.point_value" in description
    
    def test_set_endorsement_requests_valid_describe(self, mock_one_user):
        """Test AdminAudit_SetEndorsementRequestsValid describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="arXiv_endorsement_requests.flag_valid=0",
            comment="Mark endorsement requests as invalid"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "arXiv_endorsement_requests.flag_valid" in description
    
    def test_set_email_bouncing_describe(self, mock_one_user):
        """Test AdminAudit_SetEmailBouncing describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.email_bouncing=1",
            comment="Mark email as bouncing"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "tapir_users.email_bouncing" in description
    
    def test_set_banned_describe(self, mock_one_user):
        """Test AdminAudit_SetBanned describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.flag_banned=1",
            comment="Ban user"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "tapir_users.flag_banned" in description
    
    def test_set_edit_system_describe(self, mock_one_user):
        """Test AdminAudit_SetEditSystem describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.flag_edit_system=1",
            comment="Grant system edit privileges"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "tapir_users.flag_edit_system" in description
    
    def test_set_edit_users_describe(self, mock_one_user):
        """Test AdminAudit_SetEditUsers describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.flag_edit_users=0",
            comment="Revoke user edit privileges"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "set the" in description
        assert "tapir_users.flag_edit_users" in description
    
    def test_set_email_verified_describe(self, mock_one_user):
        """Test AdminAudit_SetEmailVerified describe method."""
        mock_one_user.side_effect = self.mock_user_lookup
        
        audit_record = create_base_audit_record(
            action=AdminAuditActionEnum.FLIP_FLAG.value,
            data="tapir_users.flag_email_verified=1",
            comment="Mark email as verified"
        )
        
        event = create_admin_audit_event(audit_record)
        mock_session = Mock()
        
        description = event.describe(mock_session)
        
        assert "verified the email" in description

