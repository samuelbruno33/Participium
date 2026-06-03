from unittest.mock import Mock, patch
from participium.models.enums import Role
from participium.core.serialization import _serialize_reporter
from participium.core.serialization import serialize_report_detail
from participium.core.serialization import serialize_message
from participium.core.serialization import serialize_notification, serialize_photo
from participium.models.enums import NotificationType



class TestSerialization:

    def _make_user(self, role, user_id=1, category_id=None):
        user = Mock()
        user.id = user_id
        user.role = role
        user.category_id = category_id
        user.username = "test.user"
        user.first_name = "Test"
        user.last_name = "User"
        user.email = "test@example.com"
        user.is_active = True
        user.is_email_verified = True
        user.email_notifications_enabled = True
        user.profile_picture_path = None
        user.created_at = None
        user.category = None
        return user

    def _make_report(self, reporter, is_anonymous=False, reporter_id=1, category_id=1):
        report = Mock()
        report.reporter = reporter
        report.reporter_id = reporter_id
        report.is_anonymous = is_anonymous
        report.category_id = category_id
        report.followers = []
        report.photos = []
        report.status_history = []
        report.messages = []
        report.title = "T"
        report.description = "D"
        report.status = Mock(value="pending")
        report.rejection_reason = None
        report.latitude = 1.0
        report.longitude = 2.0
        report.created_at = None
        report.updated_at = None
        from participium.config.constants import PUBLIC_VISIBLE_STATUSES
        report.status.__eq__ = lambda self, other: False
        return report

    def test_serialize_reporter_deleted(self):
        report = Mock()
        report.reporter = None
        report.is_anonymous = False
        result = _serialize_reporter(report)
        assert result["display_name"] == "Deleted Citizen"
        assert result["id"] is None

    def test_serialize_reporter_anonymous_no_viewer(self):
        reporter = self._make_user(Role.CITIZEN)
        report = self._make_report(reporter, is_anonymous=True)
        result = _serialize_reporter(report, viewer=None)
        assert result["display_name"] == "Anonymous Citizen"

    def test_serialize_reporter_anonymous_admin_sees_real(self):
        reporter = self._make_user(Role.CITIZEN, user_id=2)
        report = self._make_report(reporter, is_anonymous=True, reporter_id=2)
        admin = self._make_user(Role.ADMIN, user_id=1)
        result = _serialize_reporter(report, viewer=admin)
        assert result["id"] == 2

    def test_serialize_reporter_anonymous_operator_same_category_sees_real(self):
        reporter = self._make_user(Role.CITIZEN, user_id=2)
        report = self._make_report(reporter, is_anonymous=True, reporter_id=2, category_id=5)
        operator = self._make_user(Role.OPERATOR, user_id=3, category_id=5)
        result = _serialize_reporter(report, viewer=operator)
        assert result["id"] == 2

    def test_serialize_reporter_anonymous_reporter_sees_self(self):
        reporter = self._make_user(Role.CITIZEN, user_id=2)
        report = self._make_report(reporter, is_anonymous=True, reporter_id=2)
        result = _serialize_reporter(report, viewer=reporter)
        assert result["id"] == 2

    def test_serialize_reporter_anonymous_other_citizen_sees_anonymous(self):
        reporter = self._make_user(Role.CITIZEN, user_id=2)
        report = self._make_report(reporter, is_anonymous=True, reporter_id=2, category_id=5)
        other = self._make_user(Role.CITIZEN, user_id=99, category_id=5)
        result = _serialize_reporter(report, viewer=other)
        assert result["display_name"] == "Anonymous Citizen"

 

    def test_serialize_report_detail_includes_messages_when_flag_set(self):
        reporter = self._make_user(Role.CITIZEN, user_id=1)
        report = self._make_report(reporter)

        msg = Mock()
        msg.id = 1
        msg.report_id = 1
        msg.body = "hello"
        msg.sender = reporter
        msg.recipient = reporter
        msg.created_at = None
        report.messages = [msg]
        report.status_history = []

        result = serialize_report_detail(report, viewer=None, include_messages=True)
        assert "messages" in result
        assert len(result["messages"]) == 1

    def test_serialize_message_with_deleted_party(self):

        message = Mock()
        message.id = 1
        message.report_id = 1
        message.body = "hello"
        message.sender = None
        message.recipient = None
        message.created_at = None

        result = serialize_message(message)
        assert result["sender"]["display_name"] == "Deleted User"
        assert result["recipient"]["display_name"] == "Deleted User"

    def test_serialize_notification_and_photo(self):
        notification = Mock()
        notification.id = 4
        notification.type = NotificationType.MESSAGE
        notification.title = "T"
        notification.body = "B"
        notification.report_id = 10
        notification.is_read = False
        notification.created_at = None

        photo = Mock()
        photo.id = 2
        photo.file_path = "photo.jpg"
        photo.original_filename = "photo.jpg"
        photo.content_type = "image/jpeg"

        notification_payload = serialize_notification(notification)
        assert notification_payload["id"] == 4
        assert notification_payload["type"] == "message"

        photo_payload = serialize_photo(photo)
        assert photo_payload["url"] == "/static/uploads/photo.jpg"
        assert photo_payload["file_path"] == "photo.jpg"


