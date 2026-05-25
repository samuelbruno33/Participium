from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.models.enums import NotificationType
from participium.models.report import Report
from participium.models.user import User
from participium.services.notification_service import NotificationService


pytestmark = pytest.mark.whitebox


@pytest.fixture
def service_bundle() -> dict[str, object]:
    session = Mock()
    notification_repository = Mock()
    email_gateway = Mock()
    service = NotificationService(
        session=session,
        notification_repository=notification_repository,
        email_gateway=email_gateway,
    )
    # Isolate notify_status_change from create_notification's internal logic
    # so the assertions target this method's control flow only.
    service.create_notification = Mock()
    return {
        "service": service,
        "session": session,
        "notification_repository": notification_repository,
        "email_gateway": email_gateway,
    }


# TC-01: empty recipients list -> loop never entered, no notification created
def test_notify_status_change_empty_recipients(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    report = Report(id=10)

    result = service.notify_status_change(recipients=[], report=report, body="status update")

    assert result is None
    service.create_notification.assert_not_called()


# TC-02: single None recipient -> condition true (B=True), skipped via continue
def test_notify_status_change_none_recipient_skipped(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    report = Report(id=10)

    result = service.notify_status_change(recipients=[None], report=report, body="status update")

    assert result is None
    service.create_notification.assert_not_called()


# TC-03: single valid recipient -> B=False, C=False, notification created with the
# expected title built from report.id and the original body forwarded as-is
def test_notify_status_change_single_valid_recipient(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    report = Report(id=42)
    user = User(id=1)

    result = service.notify_status_change(recipients=[user], report=report, body="status update")

    assert result is None
    service.create_notification.assert_called_once_with(
        user,
        NotificationType.STATUS_CHANGE,
        "Report #42 status updated",
        "status update",
        report=report,
    )


# TC-04: two recipients with the same id -> first iteration creates a notification,
# second iteration hits C=True (id already in `seen`) and is skipped
def test_notify_status_change_duplicate_recipient(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    report = Report(id=10)
    user = User(id=1)
    duplicate = User(id=1)

    result = service.notify_status_change(
        recipients=[user, duplicate], report=report, body="status update"
    )

    assert result is None
    service.create_notification.assert_called_once_with(
        user,
        NotificationType.STATUS_CHANGE,
        "Report #10 status updated",
        "status update",
        report=report,
    )


# TC-05: two distinct valid recipients -> two notifications created (loop 2+ iterations,
# both taking the C=False branch)
def test_notify_status_change_multiple_distinct_recipients(
    service_bundle: dict[str, object],
) -> None:
    service = service_bundle["service"]
    report = Report(id=10)
    user_1 = User(id=1)
    user_2 = User(id=2)

    result = service.notify_status_change(
        recipients=[user_1, user_2], report=report, body="status update"
    )

    assert result is None
    assert service.create_notification.call_count == 2
    service.create_notification.assert_any_call(
        user_1,
        NotificationType.STATUS_CHANGE,
        "Report #10 status updated",
        "status update",
        report=report,
    )
    service.create_notification.assert_any_call(
        user_2,
        NotificationType.STATUS_CHANGE,
        "Report #10 status updated",
        "status update",
        report=report,
    )


# TC-06: mixed list (None, valid, duplicate, None) -> exercises both B=True and C=True
# inside the same call; only the first valid recipient triggers create_notification
def test_notify_status_change_mixed_recipients(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    report = Report(id=10)
    user_1 = User(id=1)
    duplicate = User(id=1)

    result = service.notify_status_change(
        recipients=[None, user_1, duplicate, None],
        report=report,
        body="status update",
    )

    assert result is None
    service.create_notification.assert_called_once_with(
        user_1,
        NotificationType.STATUS_CHANGE,
        "Report #10 status updated",
        "status update",
        report=report,
    )
