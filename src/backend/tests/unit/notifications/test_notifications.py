from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest

from participium.core.exceptions import AuthorizationError, NotFoundError
from participium.models.enums import NotificationType
from participium.models.notification import Notification
from participium.models.report import Report
from participium.models.user import User
from participium.services.notification_service import NotificationService


pytestmark = pytest.mark.unit


@pytest.fixture
def service_bundle() -> dict[str, object]:
    """Build a NotificationService with mocked session, repository, gateway."""
    session = Mock()
    notification_repository = Mock()
    email_gateway = Mock()
    service = NotificationService(
        session=session,
        notification_repository=notification_repository,
        email_gateway=email_gateway,
    )
    return {
        "service": service,
        "session": session,
        "repository": notification_repository,
        "gateway": email_gateway,
    }


def _user(
    user_id: int = 1,
    email: str = "user@example.com",
    email_notifications_enabled: bool = True,
) -> User:
    return User(
        id=user_id,
        email=email,
        email_notifications_enabled=email_notifications_enabled,
    )


class TestCreateNotification:
    """create_notification persists a notification and optionally sends an email."""

    def test_none_user_returns_none_and_skips_side_effects(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        gateway = service_bundle["gateway"]

        result = service.create_notification(
            user=None,
            notification_type=NotificationType.MESSAGE,
            title="t",
            body="b",
        )

        assert result is None
        repository.add.assert_not_called()
        gateway.send.assert_not_called()

    def test_notifications_disabled_persists_but_does_not_email(
        self, service_bundle
    ) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        gateway = service_bundle["gateway"]
        user = _user(email_notifications_enabled=False)

        result = service.create_notification(
            user=user,
            notification_type=NotificationType.STATUS_CHANGE,
            title="Update",
            body="Body",
        )

        assert isinstance(result, Notification)
        assert result.user_id == user.id
        assert result.report_id is None
        assert result.type == NotificationType.STATUS_CHANGE
        assert result.title == "Update"
        assert result.body == "Body"
        assert result.is_read is False
        repository.add.assert_called_once_with(result)
        gateway.send.assert_not_called()

    def test_notifications_enabled_persists_and_sends_email(
        self, service_bundle
    ) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        gateway = service_bundle["gateway"]
        user = _user(email="alice@example.com", email_notifications_enabled=True)

        result = service.create_notification(
            user=user,
            notification_type=NotificationType.SYSTEM,
            title="Title",
            body="Body",
        )

        assert isinstance(result, Notification)
        repository.add.assert_called_once_with(result)
        gateway.send.assert_called_once_with("alice@example.com", "Title", "Body")

    def test_with_report_sets_report_id(self, service_bundle) -> None:
        service = service_bundle["service"]
        user = _user(email_notifications_enabled=False)
        report = Report(id=99)

        result = service.create_notification(
            user=user,
            notification_type=NotificationType.STATUS_CHANGE,
            title="t",
            body="b",
            report=report,
        )

        assert result.report_id == 99

    def test_email_gateway_failure_is_swallowed_and_logged(
        self, service_bundle, caplog
    ) -> None:
        # The contract states delivery failures are swallowed after logging,
        # so the notification must still be created and returned.
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        gateway = service_bundle["gateway"]
        gateway.send.side_effect = RuntimeError("SMTP unavailable")
        user = _user(user_id=42, email_notifications_enabled=True)

        with caplog.at_level(logging.ERROR, logger="participium.services.notification_service"):
            result = service.create_notification(
                user=user,
                notification_type=NotificationType.MESSAGE,
                title="Title",
                body="Body",
            )

        assert isinstance(result, Notification)
        repository.add.assert_called_once_with(result)
        gateway.send.assert_called_once()
        # Exception was logged with user identifier and traceback context
        assert any("Email notification delivery failed" in rec.message for rec in caplog.records)
        assert any(rec.exc_info is not None for rec in caplog.records)

    def test_email_gateway_failure_does_not_raise(self, service_bundle) -> None:
        # Sanity: even with a bare Exception (the broadest type the catch handles),
        # the caller never sees the exception.
        service = service_bundle["service"]
        gateway = service_bundle["gateway"]
        gateway.send.side_effect = Exception("anything")
        user = _user(email_notifications_enabled=True)

        # No exception should propagate.
        service.create_notification(
            user=user,
            notification_type=NotificationType.MESSAGE,
            title="t",
            body="b",
        )


class TestNotifyNewMessage:
    """notify_new_message wraps create_notification with the message format."""

    def test_forwards_with_formatted_title_and_body(self, service_bundle) -> None:
        service = service_bundle["service"]
        service.create_notification = Mock()
        report = Report(id=7)
        recipient = _user(user_id=3)

        service.notify_new_message(
            recipient=recipient,
            report=report,
            sender_name="Anna",
            body="Hello there",
        )

        service.create_notification.assert_called_once_with(
            recipient,
            NotificationType.MESSAGE,
            "New message on report #7",
            "Anna: Hello there",
            report=report,
        )

    def test_none_recipient_still_calls_create_notification(self, service_bundle) -> None:
        # The method does not pre-filter None; create_notification handles that.
        service = service_bundle["service"]
        service.create_notification = Mock()
        report = Report(id=7)

        service.notify_new_message(
            recipient=None,
            report=report,
            sender_name="Anna",
            body="Hi",
        )

        service.create_notification.assert_called_once_with(
            None,
            NotificationType.MESSAGE,
            "New message on report #7",
            "Anna: Hi",
            report=report,
        )


class TestListNotifications:
    """list_notifications forwards to the repository."""

    def test_returns_repository_list_verbatim(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        expected = [Mock(name="n1"), Mock(name="n2")]
        repository.list_for_user.return_value = expected

        result = service.list_notifications(user_id=10)

        assert result is expected
        repository.list_for_user.assert_called_once_with(10)


class TestCountUnreadMessageNotificationsByReport:
    """Counts unread MESSAGE notifications grouped by report_id."""

    def test_groups_counts_by_report_id(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        repository.list_unread_message_notifications.return_value = [
            Mock(report_id=1),
            Mock(report_id=1),
            Mock(report_id=2),
            Mock(report_id=1),
            Mock(report_id=2),
        ]

        result = service.count_unread_message_notifications_by_report(user_id=42)

        assert result == {1: 3, 2: 2}
        repository.list_unread_message_notifications.assert_called_once_with(user_id=42)

    def test_skips_notifications_without_report_id(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        repository.list_unread_message_notifications.return_value = [
            Mock(report_id=None),
            Mock(report_id=5),
            Mock(report_id=None),
            Mock(report_id=5),
        ]

        assert service.count_unread_message_notifications_by_report(user_id=1) == {5: 2}

    def test_empty_input_returns_empty_dict(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        repository.list_unread_message_notifications.return_value = []

        assert service.count_unread_message_notifications_by_report(user_id=1) == {}


class TestMarkReportMessageNotificationsAsRead:
    """Marks unread MESSAGE notifications for a report as read in bulk."""

    def test_marks_all_and_commits_when_present(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]
        notifications = [
            Notification(
                user_id=1, report_id=8, type=NotificationType.MESSAGE,
                title="t", body="b", is_read=False,
            ),
            Notification(
                user_id=1, report_id=8, type=NotificationType.MESSAGE,
                title="t", body="b", is_read=False,
            ),
        ]
        repository.list_unread_message_notifications.return_value = notifications

        count = service.mark_report_message_notifications_as_read(user_id=1, report_id=8)

        assert count == 2
        assert all(n.is_read is True for n in notifications)
        repository.list_unread_message_notifications.assert_called_once_with(
            user_id=1, report_id=8
        )
        session.commit.assert_called_once()

    def test_no_commit_when_empty(self, service_bundle) -> None:
        # Optimization: when there is nothing to update, no commit is issued.
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]
        repository.list_unread_message_notifications.return_value = []

        count = service.mark_report_message_notifications_as_read(user_id=1, report_id=8)

        assert count == 0
        session.commit.assert_not_called()


class TestGetUserNotification:
    """Lookup with ownership check."""

    def test_returns_notification_for_owner(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        notification = Notification(
            id=1, user_id=42, type=NotificationType.SYSTEM,
            title="t", body="b", is_read=False,
        )
        repository.get_by_id.return_value = notification

        assert service.get_user_notification(user_id=42, notification_id=1) is notification
        repository.get_by_id.assert_called_once_with(1)

    def test_missing_raises_not_found(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Notification not found."):
            service.get_user_notification(user_id=1, notification_id=999)

    def test_wrong_owner_raises_authorization(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        notification = Notification(
            id=1, user_id=10, type=NotificationType.SYSTEM,
            title="t", body="b", is_read=False,
        )
        repository.get_by_id.return_value = notification

        with pytest.raises(AuthorizationError, match="You cannot access this notification."):
            service.get_user_notification(user_id=99, notification_id=1)


class TestMarkAsRead:
    """Single-notification flag flip with commit."""

    def test_sets_is_read_true_and_commits(self, service_bundle) -> None:
        service = service_bundle["service"]
        session = service_bundle["session"]
        notification = Notification(
            id=1, user_id=1, type=NotificationType.SYSTEM,
            title="t", body="b", is_read=False,
        )

        result = service.mark_as_read(notification)

        assert result is notification
        assert notification.is_read is True
        session.commit.assert_called_once()

    def test_already_read_remains_read_and_still_commits(self, service_bundle) -> None:
        service = service_bundle["service"]
        session = service_bundle["session"]
        notification = Notification(
            id=1, user_id=1, type=NotificationType.SYSTEM,
            title="t", body="b", is_read=True,
        )

        result = service.mark_as_read(notification)

        assert result is notification
        assert notification.is_read is True
        session.commit.assert_called_once()
