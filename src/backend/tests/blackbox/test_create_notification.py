from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from participium.services.notification_service import NotificationService
from participium.core.exceptions import NotFoundError
from participium.models.user import User
from participium.models.report import Report
from participium.models.enums import NotificationType
from participium.models.notification import Notification

# TC-01
def test_create_notification_success() -> None:
    mock_repo = MagicMock()
    mock_email = MagicMock()

    service = NotificationService(
        notification_repository=mock_repo,
        email_gateway=mock_email
    )

    user = User(id=1, email_notifications_enabled=False)

    result = service.create_notification(
        user=user,
        notification_type=NotificationType.STATUS_CHANGE,
        title="Update",
        body="Your report has been assigned to an operator."
    )

    assert isinstance(result, Notification)
    assert result.user_id == 1
    assert result.type == NotificationType.STATUS_CHANGE
    assert result.title == "Update"
    assert result.body == "Your report has been assigned to an operator."

    mock_repo.add.assert_called_once_with(result)
    mock_email.send.assert_not_called()

# TC-02
def test_create_notification_null_user() -> None:
    mock_repo = MagicMock()
    mock_email = MagicMock()

    service = NotificationService(
        notification_repository=mock_repo,
        email_gateway=mock_email
    )

    result = service.create_notification(
        user=None,
        notification_type=NotificationType.MESSAGE,
        title="New Message",
        body="You have a new message."
    )

    assert result is None
    mock_repo.add.assert_not_called()
    mock_email.send.assert_not_called()

# TC-03
def test_create_notification_with_report() -> None:
    mock_repo = MagicMock()
    mock_email = MagicMock()

    service = NotificationService(
        notification_repository=mock_repo,
        email_gateway=mock_email
    )

    user = User(id=1, email_notifications_enabled=False)
    report = Report(id=10)

    result = service.create_notification(
        user=user,
        notification_type=NotificationType.STATUS_CHANGE,
        title="Report Update",
        body="Body of the notification",
        report=report
    )

    assert isinstance(result, Notification)
    assert result.report_id == 10

    mock_repo.add.assert_called_once_with(result)

# TC-04
def test_create_notification_email_sent() -> None:
    mock_repo = MagicMock()
    mock_email = MagicMock()

    service = NotificationService(
        notification_repository=mock_repo,
        email_gateway=mock_email
    )

    user = User(
        id=2,
        email="test@example.com",
        email_notifications_enabled=True
    )

    result = service.create_notification(
        user=user,
        notification_type=NotificationType.SYSTEM,
        title="System Alert",
        body="System is sending a notification."
    )

    assert isinstance(result, Notification)

    mock_repo.add.assert_called_once_with(result)
    mock_email.send.assert_called_once_with(
        "test@example.com",
        "System Alert",
        "System is sending a notification."
    )

# TC-05
def test_create_notification_with_email_failure() -> None:
    mock_repo = MagicMock()
    mock_email = MagicMock()
    mock_email.send.side_effect = Exception("Email server down")

    service = NotificationService(
        notification_repository=mock_repo,
        email_gateway=mock_email
    )

    user = User(
        id=3,
        email="fail@example.com",
        email_notifications_enabled=True
    )

    result = service.create_notification(
        user=user,
        notification_type=NotificationType.MESSAGE,
        title="Hi",
        body="Hello"
    )

    assert isinstance(result, Notification)

    mock_repo.add.assert_called_once()
    mock_email.send.assert_called_once()