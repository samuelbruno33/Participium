from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from participium.services.messaging_service import MessagingService
from participium.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from participium.models.user import User
from participium.models.report import Report
from participium.models.enums import Role
from participium.models.message import Message

# TC-01
def test_send_message_success() -> None:
    mock_session = MagicMock()
    mock_message_repo = MagicMock()
    mock_notification_service = MagicMock()
    
    service = MessagingService(
        session=mock_session,
        message_repository=mock_message_repo,
        notification_service=mock_notification_service
    )
    
    sender = User(id=1, role=Role.ADMIN, first_name="AdminName", last_name="AdminLastName", username="AdminUsername")
    recipient = User(id=2)
    report = Report(id=10, reporter=recipient)

    # Valid message
    result = service.send_message(
        report=report,
        sender=sender,
        body="Normal message"
    )
    
    assert isinstance(result, Message)
    assert result.report_id == 10
    assert result.sender_id == 1
    assert result.recipient_id == 2
    assert result.body == "Normal message"
    
    mock_message_repo.add.assert_called_once_with(result)
    mock_notification_service.notify_new_message.assert_called_once_with(
        recipient=recipient,
        report=report,
        sender_name="AdminName AdminLastName",
        body="Normal message"
    )
    mock_session.commit.assert_called_once()

# TC-02
def test_send_message_requires_authenticated_sender() -> None:
    mock_session = MagicMock()
    mock_message_repo = MagicMock()
    mock_notification_service = MagicMock()
    
    service = MessagingService(
        session=mock_session,
        message_repository=mock_message_repo,
        notification_service=mock_notification_service
    )
    
    report = Report(id=10)
    
    # Passing None as sender raises AuthorizationError because it can't be validated for thread access
    with pytest.raises(AuthorizationError):
        service.send_message(report=report, sender=None, body="Hello?")

# TC-03
def test_send_message_recipient_not_found() -> None:
    mock_session = MagicMock()
    mock_message_repo = MagicMock()
    mock_notification_service = MagicMock()
    
    service = MessagingService(
        session=mock_session,
        message_repository=mock_message_repo,
        notification_service=mock_notification_service
    )

    sender = User(id=1, role=Role.CITIZEN)
    report = Report(id=10, reporter_id=1, reporter=sender, status_history=[])
    
    mock_message_repo.list_for_report.return_value = []

    # If no recipient can be resolved, a ValidationError is raised
    with pytest.raises(ValidationError, match="No recipient available for this conversation"):
        service.send_message(report=report, sender=sender, body="Hello?")

# TC-04
def test_send_message_report_not_found() -> None:
    mock_session = MagicMock()
    mock_message_repo = MagicMock()
    mock_notification_service = MagicMock()
    
    service = MessagingService(
        session=mock_session,
        message_repository=mock_message_repo,
        notification_service=mock_notification_service
    )
    
    sender = User(id=1, role=Role.ADMIN)
    
    # Passing None as report will cause an AttributeError when trying to access its attributes
    with pytest.raises(AttributeError):
        service.send_message(report=None, sender=sender, body="Valid content")

# TC-05
def test_send_message_invalid_content() -> None:
    mock_session = MagicMock()
    mock_message_repo = MagicMock()
    mock_notification_service = MagicMock()
    
    service = MessagingService(
        session=mock_session,
        message_repository=mock_message_repo,
        notification_service=mock_notification_service
    )
    
    sender = User(id=1, role=Role.ADMIN)
    report = Report(id=10)

    # Message is empty or whitespace
    with pytest.raises(ValidationError, match="Message body cannot be empty."):
        service.send_message(report=report, sender=sender, body="   ")

# TC-06
def test_send_message_unauthorized_sender() -> None:
    mock_session = MagicMock()
    mock_message_repo = MagicMock()
    mock_notification_service = MagicMock()
    
    service = MessagingService(
        session=mock_session,
        message_repository=mock_message_repo,
        notification_service=mock_notification_service
    )

    sender = User(id=5, role=Role.CITIZEN)
    report = Report(id=10, reporter_id=2)
    
    # The sender is a USER but not the reporter of this report
    with pytest.raises(AuthorizationError):
        service.send_message(report=report, sender=sender, body="Normal Message")

# TC-07
def test_send_message_operator_with_matching_category() -> None:
    mock_session = MagicMock()
    mock_message_repo = MagicMock()
    mock_notification_service = MagicMock()

    service = MessagingService(
        session=mock_session,
        message_repository=mock_message_repo,
        notification_service=mock_notification_service
    )

    operator = User(
        id=5,
        role=Role.OPERATOR,
        category_id=3,
        first_name="Mario",
        last_name="Rossi"
    )

    reporter = User(id=2)

    report = Report(
        id=10,
        reporter=reporter,
        category_id=3
    )

    result = service.send_message(
        report=report,
        sender=operator,
        body="Operator response"
    )

    assert result.sender_id == 5
    assert result.recipient_id == 2

    # Should be successful since the category of the report matches that of the operator
    mock_session.commit.assert_called_once()

# TC-08
def test_send_message_operator_wrong_category() -> None:
    mock_session = MagicMock()

    service = MessagingService(
        session=mock_session,
        message_repository=MagicMock(),
        notification_service=MagicMock()
    )

    operator = User(
        id=5,
        role=Role.OPERATOR,
        category_id=7
    )

    report = Report(
        id=10,
        reporter_id=2,
        category_id=3
    )


    with pytest.raises(AuthorizationError):
        service.send_message(
            report=report,
            sender=operator,
            body="Trying to send this message."
        )