from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from participium.services.notification_service import NotificationService

pytestmark = pytest.mark.whitebox

def test_count_unread_zero_iterations():
    """
    Target Path: N1 -> N2 -> N6
    Condition Coverage: Loop condition evaluates to False immediately.
    """
    # Setup isolated mock repository
    mock_notification_repo = MagicMock()
    mock_notification_repo.list_unread_message_notifications.return_value = []

    # Inject dependency into service
    service = NotificationService(notification_repository=mock_notification_repo)

    # Execution
    user_id = 1
    result = service.count_unread_message_notifications_by_report(user_id=user_id)

    # Assertions
    assert result == {}
    mock_notification_repo.list_unread_message_notifications.assert_called_once_with(user_id=user_id)


def test_count_unread_report_id_none():
    """
    Target Path: N1 -> N2 -> N3 -> N4 -> N2 -> N6
    Condition Coverage: Loop entered, if-condition evaluates to True.
    """
    # Setup mock notification where report_id is None
    mock_notification = MagicMock()
    mock_notification.report_id = None

    mock_notification_repo = MagicMock()
    mock_notification_repo.list_unread_message_notifications.return_value = [mock_notification]

    service = NotificationService(notification_repository=mock_notification_repo)

    # Execution
    result = service.count_unread_message_notifications_by_report(user_id=2)

    # Assertions
    assert result == {}


def test_count_unread_valid_multiple_iterations():
    """
    Target Path: Multiple iterations covering N1 -> N2 -> N3 -> N5 -> N2 -> N6
    Condition Coverage: Loop entered multiple times, if-condition evaluates to False.
    Loop Coverage: > 1 iterations.
    """
    # Setup multiple mock notifications to test dictionary aggregation logic
    notif_1 = MagicMock()
    notif_1.report_id = 100

    notif_2 = MagicMock()
    notif_2.report_id = 100

    notif_3 = MagicMock()
    notif_3.report_id = 200

    mock_notification_repo = MagicMock()
    # Returns 3 elements: two targeting report_id=100, one targeting report_id=200
    mock_notification_repo.list_unread_message_notifications.return_value = [notif_1, notif_2, notif_3]

    service = NotificationService(notification_repository=mock_notification_repo)

    # Execution
    result = service.count_unread_message_notifications_by_report(user_id=3)

    # Assertions
    assert result == {100: 2, 200: 1}
    mock_notification_repo.list_unread_message_notifications.assert_called_once_with(user_id=3)