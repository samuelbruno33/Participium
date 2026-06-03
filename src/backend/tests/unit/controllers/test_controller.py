from __future__ import annotations


from unittest.mock import Mock
from participium.controllers.admin_controller import AdminController
from participium.controllers.operator_controller import OperatorController
from participium.models.enums import Role
from participium.controllers.statistics_controller import StatisticsController
from participium.controllers.user_controller import UserController


class TestAdminController:
	def _make_controller(self):
		category_service = Mock()
		user_service = Mock()
		statistics_service = Mock()
		ctrl = AdminController(
               category_service=category_service,
               user_service=user_service,
               statistics_service=statistics_service,)
		return ctrl, category_service, user_service, statistics_service

	def test_create_category_delegates(self):
		ctrl, category_service, _, _ = self._make_controller()
		fake_category = Mock()
		category_service.create_category.return_value = fake_category   

		result = ctrl.create_category("Roads and Highways")

		category_service.create_category.assert_called_once_with("Roads and Highways")
		assert result is fake_category

	def test_update_category_delegates(self):
		ctrl, category_service, _, _ = self._make_controller()
		fake_category = Mock()
		category_service.update_category.return_value = fake_category  

		result = ctrl.update_category(1, {"name": "New Name", "is_active": False})

		category_service.update_category.assert_called_once_with(1, name="New Name", is_active=False)
		assert result is fake_category

	def test_admin_statistics_delegates(self):
		ctrl, _, _, statistics_service = self._make_controller()
		statistics_service.admin_statistics.return_value = {"total": 40}

		result = ctrl.admin_statistics()

		statistics_service.admin_statistics.assert_called_once()
		assert result == {"total": 40}



class TestOperatorController:
    def _make_controller(self):
        report_service = Mock()
        notification_service = Mock()
        ctrl = OperatorController(
             report_service=report_service,
             notification_service=notification_service,
        )
        return ctrl, report_service, notification_service

    def _operator(self, role, category_id=None):
        user = Mock()
        user.role = role
        user.category_id = category_id
        user.id = 1
        return user

    def test_build_dashboard_operator(self):
        ctrl, report_service, notification_service = self._make_controller()
        report_service.list_pending_reports.return_value = ["r2"]
        report_service.list_operator_reports.return_value = []
        notification_service.count_unread_message_notifications_by_report.return_value = {}

        operator = self._operator(Role.OPERATOR, category_id=7)
        ct = ctrl.build_dashboard(operator, {"sort": "asc"})

        report_service.list_pending_reports.assert_called_once_with({"sort": "asc", "category_id": 7})
        assert ct.pending_reports == ["r2"]

    def test_build_dashboard_with_unhandled_role(self):

        ctrl, report_service, notification_service = self._make_controller()

        report_service.list_operator_reports.return_value = []
        notification_service.count_unread_message_notifications_by_report.return_value = {}

        citizen = self._operator(Role.CITIZEN)
        ct = ctrl.build_dashboard(citizen, {})
        assert ct.assigned_reports == []



class TestUserController:

    def _make_controller(self):
        user_service = Mock()
        notification_service = Mock()
        ctrl = UserController(user_service=user_service, notification_service=notification_service)
        return ctrl, user_service, notification_service

    def test_list_users_delegates(self):
        ctrl, user_service, _ = self._make_controller()
        user_service.list_users.return_value = ["u1", "u2"]
        assert ctrl.list_users() == ["u1", "u2"]

    def test_create_user_delegates(self):
        ctrl, user_service, _ = self._make_controller()
        fake_user = Mock()
        user_service.create_user.return_value = fake_user
        result = ctrl.create_user({"username": "user"})
        user_service.create_user.assert_called_once_with({"username": "user"})
        assert result is fake_user

    def test_update_user_delegates(self):
        ctrl, user_service, _ = self._make_controller()
        fake_user = Mock()
        user_service.update_user.return_value = fake_user
        result = ctrl.update_user(1, {"first_name": "Test"})
        user_service.update_user.assert_called_once_with(1, {"first_name": "Test"})
        assert result is fake_user

    def test_list_notifications_delegates(self):
        ctrl, _, notification_service = self._make_controller()
        notification_service.list_notifications.return_value = ["n1"]
        assert ctrl.list_notifications(7) == ["n1"]
        notification_service.list_notifications.assert_called_once_with(7)

    def test_get_notification_for_user_delegates(self):
        ctrl, _, notification_service = self._make_controller()
        fake_notif = Mock()
        notification_service.get_user_notification.return_value = fake_notif
        result = ctrl.get_notification_for_user(7, 99)
        notification_service.get_user_notification.assert_called_once_with(7, 99)
        assert result is fake_notif

    def test_mark_notification_as_read_delegates(self):
        ctrl, _, notification_service = self._make_controller()
        fake_notif = Mock()
        notification_service.mark_as_read.return_value = fake_notif
        n = Mock()
        result = ctrl.mark_notification_as_read(n)
        notification_service.mark_as_read.assert_called_once_with(n)
        assert result is fake_notif


class TestReportController:

    @staticmethod
    def _make_controller():
        from participium.controllers.report_controller import ReportController
        from participium.services.messaging_service import MessagingService
        from participium.services.notification_service import NotificationService
        from participium.services.report_service import ReportService

        report_service = Mock(spec=ReportService)
        messaging_service = Mock(spec=MessagingService)
        notification_service = Mock(spec=NotificationService)
        ctrl = ReportController(
            report_service=report_service,
            messaging_service=messaging_service,
            notification_service=notification_service,
        )
        return ctrl, report_service, messaging_service, notification_service

    class DummyUser:
        def __init__(self, id=7):
            self.id = id

    def test_list_user_reports_delegates(self):
        ctrl, report_service, _, _ = self._make_controller()
        user = self.DummyUser(id=5)
        expected_reports = [Mock()]
        report_service.list_user_reports.return_value = expected_reports

        result = ctrl.list_user_reports(user)

        report_service.list_user_reports.assert_called_once_with(user)
        assert result is expected_reports



class TestStatisticsController:

    def test_public_statistics_delegates(self):
        statistics_service = Mock()
        ctrl = StatisticsController(statistics_service=statistics_service)

        statistics_service.public_statistics.return_value = {"total": 99}
        result = ctrl.public_statistics("month")

        statistics_service.public_statistics.assert_called_once_with("month")
        assert result == {"total": 99}

