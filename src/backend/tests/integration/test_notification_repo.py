from __future__ import annotations

from participium.repositories.notification_repository import NotificationRepository
from participium.models.notification import Notification
from participium.models.enums import NotificationType


class TestNotificationRepository:

    def test_add_returns_notification(self, db, create_user):

        repo = NotificationRepository(db)
        user = create_user()
        db.add(user)
        db.commit()

        notification = Notification(
            user_id=user.id,
            type=NotificationType.STATUS_CHANGE,
            title="Test",
            body="Body",
            is_read=False,
        )
        result = repo.add(notification)
        db.commit()

        assert result is notification

    def test_get_by_id_returns_notification(self, db, create_user):

        repo = NotificationRepository(db)
        user = create_user()
        db.add(user)
        db.commit()

        notification = Notification(
            user_id=user.id,
            type=NotificationType.MESSAGE,
            title="Test",
            body="Body",
            is_read=False,
        )
        db.add(notification)
        db.commit()

        fetched = repo.get_by_id(notification.id)
        assert fetched is notification


    def test_delete_for_user_removes_all_notifications(self, db, create_user):

        repo = NotificationRepository(db)
        user = create_user()
        db.add(user)
        db.commit()

        for i in range(3): db.add(Notification(user_id=user.id, type=NotificationType.STATUS_CHANGE, title="T", body="B", is_read=False))
        db.commit()

        repo.delete_for_user(user.id)
        db.commit()

        assert repo.list_for_user(user.id) == []
