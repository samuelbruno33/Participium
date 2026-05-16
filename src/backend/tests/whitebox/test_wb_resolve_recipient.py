from __future__ import annotations

import pytest
from unittest.mock import Mock

from participium.models.enums import Role
from participium.models.user import User
from participium.models.message import Message
from participium.models.report import Report
from participium.services.messaging_service import MessagingService

pytestmark = pytest.mark.whitebox

def _user(
    *,
    user_id: int = 1,
    role: Role = Role.CITIZEN,
    first_name: str = "Mario",
    last_name: str = "Rossi",
    username: str = "mario.rossi",
) -> User:
    return User(
        id=user_id,
        role=role,
        first_name=first_name,
        last_name=last_name,
        username=username,
    )


def _message(*, sender: User | None) -> Message:
    msg = Mock(spec=Message)
    msg.sender = sender
    return msg


def _report(*, reporter: User, category_id: int = 1) -> Report:
    rep = Mock(spec=Report)
    rep.id = 1
    rep.reporter = reporter
    rep.category_id = category_id
    rep.status_history = []
    return rep


@pytest.fixture
def service_bundle() -> dict[str, object]:
    session = Mock()
    message_repository = Mock()
    report_repository = Mock()
    notification_service = Mock()

    service = MessagingService(
        session=session,
        message_repository=message_repository,
        report_repository=report_repository,
        notification_service=notification_service,
    )

    return {
        "service": service,
        "session": session,
        "message_repository": message_repository,
        "report_repository": report_repository,
        "notification_service": notification_service,
    }


# TC-01
def test_resolve_recipient_sender_is_admin(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]

    admin = _user(role=Role.ADMIN)
    reporter = _user(user_id=99)

    report = _report(reporter=reporter)

    result = service._resolve_recipient(report, admin)

    assert result == reporter


# TC-02
def test_resolve_recipient_first_message_valid(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    repo = service_bundle["message_repository"]

    reporter = _user(user_id=99)
    report = _report(reporter=reporter)

    sender = _user(role=Role.CITIZEN)

    admin_sender = _user(user_id=2, role=Role.ADMIN)
    repo.list_for_report.return_value = [
        _message(sender=admin_sender)
    ]

    result = service._resolve_recipient(report, sender)

    assert result == admin_sender


# TC-03
def test_resolve_recipient_skip_none_sender(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    repo = service_bundle["message_repository"]

    reporter = _user(user_id=99)
    report = _report(reporter=reporter)

    sender = _user(role=Role.CITIZEN)
    admin_sender = _user(user_id=2, role=Role.ADMIN)

    repo.list_for_report.return_value = [
        _message(sender=admin_sender),
        _message(sender=None),
    ]

    result = service._resolve_recipient(report, sender)

    assert result == admin_sender


# TC-04
def test_resolve_recipient_skip_invalid_role(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    repo = service_bundle["message_repository"]

    reporter = _user(user_id=99)
    report = _report(reporter=reporter)

    sender = _user(role=Role.CITIZEN)

    invalid_user = _user(user_id=2, role=Role.CITIZEN)
    admin_user = _user(user_id=3, role=Role.ADMIN)

    repo.list_for_report.return_value = [
        _message(sender=admin_user),    # 3. Found last (Oldest)
        _message(sender=invalid_user),  # 2. Seen and skipped
        _message(sender=None),          # 1. Seen and skipped (Most recent)
    ]

    result = service._resolve_recipient(report, sender)

    assert result == admin_user


# TC-05
def test_resolve_recipient_status_first_valid(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]

    repo = service_bundle["message_repository"]

    reporter = _user(user_id=99)
    report = _report(reporter=reporter)

    sender = _user(role=Role.CITIZEN)

    repo.list_for_report.return_value = []

    status_user = _user(user_id=10, role=Role.OPERATOR)
    report.status_history = [
        Mock(changed_by=status_user)
    ]

    result = service._resolve_recipient(report, sender)

    assert result == status_user


# TC-06
def test_resolve_recipient_status_skip_none(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]

    repo = service_bundle["message_repository"]

    reporter = _user(user_id=99)
    report = _report(reporter=reporter)

    sender = _user(role=Role.CITIZEN)

    repo.list_for_report.return_value = []

    valid_user = _user(user_id=10, role=Role.ADMIN)

    report.status_history = [
        Mock(changed_by=valid_user), # 2. Found last
        Mock(changed_by=None),       # 1. Seen and skipped
    ]

    result = service._resolve_recipient(report, sender)

    assert result == valid_user


# TC-07
def test_resolve_recipient_status_skip_invalid(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]

    repo = service_bundle["message_repository"]

    reporter = _user(user_id=99)
    report = _report(reporter=reporter)

    sender = _user(role=Role.CITIZEN)

    repo.list_for_report.return_value = []

    invalid_user = _user(user_id=10, role=Role.CITIZEN)
    valid_user = _user(user_id=11, role=Role.OPERATOR)

    report.status_history = [
        Mock(changed_by=valid_user),    # 3. Found last
        Mock(changed_by=invalid_user),  # 2. Seen and skipped
        Mock(changed_by=None),          # 1. Seen and skipped
    ]

    result = service._resolve_recipient(report, sender)

    assert result == valid_user


# TC-08
def test_resolve_recipient_returns_none(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]

    repo = service_bundle["message_repository"]

    reporter = _user(user_id=99)
    report = _report(reporter=reporter)

    sender = _user(role=Role.CITIZEN)

    repo.list_for_report.return_value = []
    report.status_history = []

    result = service._resolve_recipient(report, sender)

    assert result is None