from __future__ import annotations

from unittest.mock import Mock
import pytest

from participium.core.exceptions import AuthorizationError, ValidationError
from participium.models.enums import Role, ReportStatus
from participium.models.user import User
from participium.models.report import Report, ReportStatusHistory
from participium.models.message import Message
from participium.services.messaging_service import MessagingService
from participium.services.report_service import ReportService

def _user(user_id: int, role: Role, category_id: int | None = None) -> User:
    return User(
        id=user_id,
        role=role,
        category_id=category_id,
        username=f"user_{user_id}",
        first_name="Test",
        last_name="User"
    )

def _history_entry(changed_by: User, status: ReportStatus = ReportStatus.ASSIGNED) -> ReportStatusHistory:
    history = ReportStatusHistory(
        new_status=status,
        changed_by_id=changed_by.id
    )
    history.changed_by = changed_by
    return history

def _report(report_id: int, reporter_id: int, category_id: int, status: ReportStatus = ReportStatus.PENDING_APPROVAL) -> Report:
    rep = Report(
        id=report_id,
        reporter_id=reporter_id,
        category_id=category_id,
        status=status,
        title="Test Report",
        description="Test Description"
    )
    rep.reporter = _user(reporter_id, Role.CITIZEN)
    rep.status_history = []
    return rep

@pytest.fixture
def messaging_bundle() -> dict[str, object]:
    session = Mock()
    report_repository = Mock()
    message_repository = Mock()
    notification_service = Mock()
    
    service = MessagingService(
        session=session,
        report_repository=report_repository,
        message_repository=message_repository,
        notification_service=notification_service
    )
    
    return {
        "service": service,
        "session": session,
        "message_repo": message_repository,
        "notif_service": notification_service
    }

@pytest.fixture
def report_service_bundle() -> dict[str, object]:
    # Subset of ReportService needed for get_accessible_report
    session = Mock()
    report_repository = Mock()
    service = ReportService(
        session=session,
        report_repository=report_repository,
        category_repository=Mock(),
        storage_service=Mock(),
        notification_service=Mock()
    )
    return {"service": service, "repo": report_repository}

class TestMessagingAccess:
    """Tests for can_access_thread logic in MessagingService."""
    
    def test_admin_has_full_access(self, messaging_bundle):
        service = messaging_bundle["service"]
        admin = _user(1, Role.ADMIN)
        report = _report(100, 2, 10)
        assert service.can_access_thread(report, admin) is True

    def test_reporter_has_access(self, messaging_bundle):
        service = messaging_bundle["service"]
        reporter = _user(2, Role.CITIZEN)
        report = _report(100, 2, 10)
        assert service.can_access_thread(report, reporter) is True

    def test_other_citizen_has_no_access(self, messaging_bundle):
        service = messaging_bundle["service"]
        stranger = _user(3, Role.CITIZEN)
        report = _report(100, 2, 10)
        assert service.can_access_thread(report, stranger) is False

    def test_operator_same_category_has_access(self, messaging_bundle):
        service = messaging_bundle["service"]
        operator = _user(4, Role.OPERATOR, category_id=10)
        report = _report(100, 2, 10)
        assert service.can_access_thread(report, operator) is True

    def test_operator_different_category_no_access(self, messaging_bundle):
        service = messaging_bundle["service"]
        operator = _user(4, Role.OPERATOR, category_id=11)
        report = _report(100, 2, 10)
        assert service.can_access_thread(report, operator) is False

    def test_unauthenticated_user_no_access(self, messaging_bundle):
        service = messaging_bundle["service"]
        report = _report(100, 2, 10)
        assert service.can_access_thread(report, None) is False

class TestMessagingOperations:
    """Tests for list_messages and send_message workflows."""

    def test_list_messages_success(self, messaging_bundle):
        service = messaging_bundle["service"]
        repo = messaging_bundle["message_repo"]
        
        reporter = _user(2, Role.CITIZEN)
        report = _report(100, 2, 10)
        repo.list_for_report.return_value = [Mock(spec=Message)]
        
        messages = service.list_messages(report, reporter)
        assert len(messages) == 1
        repo.list_for_report.assert_called_once_with(report.id)

    def test_list_messages_unauthorized(self, messaging_bundle):
        service = messaging_bundle["service"]
        stranger = _user(3, Role.CITIZEN)
        report = _report(100, 2, 10)
        
        with pytest.raises(AuthorizationError):
            service.list_messages(report, stranger)

    def test_send_message_success(self, messaging_bundle):
        service = messaging_bundle["service"]
        repo = messaging_bundle["message_repo"]
        notif = messaging_bundle["notif_service"]
        
        sender = _user(1, Role.ADMIN)
        report = _report(100, 2, 10)
        body = "Hello citizen!"
        
        # Admin sending to reporter
        message = service.send_message(report, sender, body)
        
        assert message.body == body
        assert message.sender_id == sender.id
        assert message.recipient_id == report.reporter_id
        repo.add.assert_called_once()
        notif.notify_new_message.assert_called_once()
        messaging_bundle["session"].commit.assert_called_once()

    def test_send_message_empty_body(self, messaging_bundle):
        service = messaging_bundle["service"]
        sender = _user(2, Role.CITIZEN)
        report = _report(100, 2, 10)
        
        with pytest.raises(ValidationError, match="body cannot be empty"):
            service.send_message(report, sender, "   ")

    def test_send_message_no_recipient_resolved(self, messaging_bundle):
        service = messaging_bundle["service"]
        repo = messaging_bundle["message_repo"]
        
        citizen = _user(2, Role.CITIZEN)
        report = _report(100, 2, 10)
        
        # Mock repo to return no messages and history is empty
        repo.list_for_report.return_value = []
        report.status_history = []
        
        with pytest.raises(ValidationError, match="No recipient available"):
            service.send_message(report, citizen, "Help me")

class TestRecipientResolution:
    """Tests for the _resolve_recipient complex logic."""

    def test_resolve_from_messages(self, messaging_bundle):
        service = messaging_bundle["service"]
        repo = messaging_bundle["message_repo"]
        
        citizen = _user(2, Role.CITIZEN)
        report = _report(100, 2, 10)
        operator = _user(4, Role.OPERATOR, category_id=10)
        
        # Last message was from an operator
        msg = Mock(spec=Message)
        msg.sender = operator
        repo.list_for_report.return_value = [msg]
        
        result = service._resolve_recipient(report, citizen)
        assert result == operator

    def test_resolve_from_history_if_no_messages(self, messaging_bundle):
        service = messaging_bundle["service"]
        repo = messaging_bundle["message_repo"]
        
        citizen = _user(2, Role.CITIZEN)
        report = _report(100, 2, 10)
        admin = _user(1, Role.ADMIN)
        
        repo.list_for_report.return_value = []
        # Report was assigned by an Admin
        history = _history_entry(changed_by=admin)
        report.status_history = [history]
        
        result = service._resolve_recipient(report, citizen)
        assert result == admin

class TestReportAccessLogic:
    """Tests for ReportService.get_accessible_report."""

    def test_get_accessible_report_public(self, report_service_bundle):
        service = report_service_bundle["service"]
        repo = report_service_bundle["repo"]
        
        # Status RESOLVED (5) is public
        report = _report(100, 2, 10, status=ReportStatus.RESOLVED)
        repo.get_by_id.return_value = report
        
        assert service.get_accessible_report(100, None) == report

    def test_get_accessible_report_denied(self, report_service_bundle):
        service = report_service_bundle["service"]
        repo = report_service_bundle["repo"]
        
        # Pending reports are private
        report = _report(100, 2, 10, status=ReportStatus.PENDING_APPROVAL)
        repo.get_by_id.return_value = report
        stranger = _user(3, Role.CITIZEN)
        
        with pytest.raises(AuthorizationError):
            service.get_accessible_report(100, stranger)

    def test_get_accessible_report_operator_same_category(self, report_service_bundle):
        service = report_service_bundle["service"]
        repo = report_service_bundle["repo"]
        
        report = _report(100, 2, 10, status=ReportStatus.ASSIGNED)
        repo.get_by_id.return_value = report
        operator = _user(4, Role.OPERATOR, category_id=10)
        
        assert service.get_accessible_report(100, operator) == report