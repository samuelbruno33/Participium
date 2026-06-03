from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from participium import create_app
from participium.database import close_connection
from types import SimpleNamespace
from participium.models.enums import Role



@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("AUTO_INIT_DB", "true")
    monkeypatch.setenv("BOOTSTRAP_REFERENCE_DATA", "false")
    monkeypatch.setenv("BOOTSTRAP_DEMO_DATA", "false")

    app = create_app()
    app.config.update(TESTING=True)
    
    yield app.test_client()
    
    close_connection()


class TestApiRoutes:

    def _make_user(self, role, user_id=1):
        user = Mock()
        user.id = user_id
        user.role = role
        return user

    def _make_controllers(self):
        return SimpleNamespace(
            auth=Mock(),
            reports=Mock(),
            statistics=Mock(),
            users=Mock(),
            operators=Mock(),
            admin=Mock(),
        )

    def _make_authenticated_user_patches(self, user):
        return (patch("participium.routes.api.current_user", return_value=user), patch("participium.core.auth.current_user", return_value=user),)


    def test_health_check(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "ok"}

    @pytest.mark.parametrize("expose, expected_in_response", [(True, True),(False, False),])
    def test_register_user_verification_link_visibility(self, client, expose, expected_in_response):
        controllers = self._make_controllers()
        controllers.auth.register.return_value = (Mock(), "http://localhost/api/v1/auth/verify/test")
        client.application.config["SETTINGS"].expose_verification_links = expose

        with patch("participium.routes.api.get_controllers", return_value=controllers), \
            patch("participium.routes.api.serialize_user", return_value={"id": 1}):
            resp = client.post("/api/v1/auth/register", json={"username": "u", "email": "u@example.com", "password": "Password1!"})

        assert resp.status_code == 201
        assert ("verification_url" in resp.get_json()) == expected_in_response



    def test_reference_data_api_returns_expected_lists(self, client):
        resp = client.get("/api/v1/meta/reference-data")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert "roles" in payload
        assert "report_statuses" in payload
        assert "public_report_statuses" in payload


    def test_statistics_api_delegates(self, client):
        controllers = self._make_controllers()
        controllers.statistics.public_statistics.return_value = {"items": 1}

        with patch("participium.routes.api.get_controllers", return_value=controllers):
            resp = client.get("/api/v1/stats/public?granularity=week")

        assert resp.status_code == 200
        assert resp.get_json() == {"items": 1}

    def test_me_api_returns_serialized_user(self, client):
        user = self._make_user(Role.CITIZEN)
        with patch("participium.routes.api.serialize_user", return_value={"id": 1}), \
             patch("participium.routes.api.current_user", return_value=user), \
             patch("participium.core.auth.current_user", return_value=user):
            resp = client.get("/api/v1/users/me")

        assert resp.status_code == 200
        assert resp.get_json() == {"id": 1}

    def test_my_reports_api_returns_user_reports(self, client):
        user = self._make_user(Role.CITIZEN)
        controllers = self._make_controllers()
        controllers.reports.list_user_reports.return_value = [Mock()]

        with patch("participium.routes.api.get_controllers", return_value=controllers), \
             patch("participium.routes.api.serialize_report_summary", return_value={"id": 1}), \
             patch("participium.routes.api.current_user", return_value=user), \
             patch("participium.core.auth.current_user", return_value=user):
            resp = client.get("/api/v1/users/me/reports")

        assert resp.status_code == 200
        assert resp.get_json() == [{"id": 1}]

    @pytest.mark.parametrize("payload, is_json", [({"email_notifications_enabled": "on"}, False),({"email_notifications_enabled": "false"}, True),])
    def test_update_me_api_parses_email_notifications(self, client, payload, is_json):
        user = self._make_user(Role.CITIZEN)
        controllers = self._make_controllers()
        controllers.users.update_profile.return_value = Mock()

        kwargs = {"json": payload} if is_json else {"data": payload}

        with patch("participium.routes.api.get_controllers", return_value=controllers), \
            patch("participium.routes.api.serialize_user", return_value={"id": 1}), \
            patch("participium.routes.api.current_user", return_value=user), \
            patch("participium.core.auth.current_user", return_value=user):
            resp = client.put("/api/v1/users/me", **kwargs)

        assert resp.status_code == 200
        controllers.users.update_profile.assert_called_once()

    def test_my_notifications_api_returns_notifications(self, client):
        user = self._make_user(Role.CITIZEN)
        controllers = self._make_controllers()
        controllers.users.list_notifications.return_value = [Mock()]

        with patch("participium.routes.api.get_controllers", return_value=controllers), \
             patch("participium.routes.api.serialize_notification", return_value={"id": 1}), \
             patch("participium.routes.api.current_user", return_value=user), \
             patch("participium.core.auth.current_user", return_value=user):
            resp = client.get("/api/v1/users/me/notifications")

        assert resp.status_code == 200
        assert resp.get_json() == [{"id": 1}]

    def test_mark_notification_read_api(self, client):
        user = self._make_user(Role.CITIZEN)
        controllers = self._make_controllers()
        controllers.users.get_notification_for_user.return_value = Mock()
        controllers.users.mark_notification_as_read.return_value = Mock()

        with patch("participium.routes.api.get_controllers", return_value=controllers), \
             patch("participium.routes.api.serialize_notification", return_value={"id": 1}), \
             patch("participium.routes.api.current_user", return_value=user), \
             patch("participium.core.auth.current_user", return_value=user):
            resp = client.post("/api/v1/users/me/notifications/1/read")

        assert resp.status_code == 200
        assert resp.get_json() == {"id": 1}

    def test_pending_and_assigned_reports_apis(self, client):
        user = self._make_user(Role.ADMIN)
        controllers = self._make_controllers()
        pending_report = Mock()
        pending_report.id = 1
        assigned_report = Mock()
        assigned_report.id = 1
        controllers.operators.build_dashboard.return_value = Mock(
            pending_reports=[pending_report],
            assigned_reports=[assigned_report],
            unread_message_counts={1: 5},
        )

        with patch("participium.routes.api.get_controllers", return_value=controllers), \
             patch("participium.routes.api.serialize_report_summary", return_value={"id": 1}), \
             patch("participium.routes.api.current_user", return_value=user), \
             patch("participium.core.auth.current_user", return_value=user):
            pending = client.get("/api/v1/operator/reports/pending")
            assigned = client.get("/api/v1/operator/reports/assigned")

        assert pending.status_code == 200
        assert assigned.status_code == 200
        assert pending.get_json() == [{"id": 1}]
        assert assigned.get_json() == [{"id": 1, "unread_message_count": 5}]

    def test_assign_and_update_report_status_apis(self, client):
        user = self._make_user(Role.ADMIN)
        controllers = self._make_controllers()
        controllers.operators.assign_report.return_value = Mock()
        controllers.operators.update_status.return_value = Mock()

        with patch("participium.routes.api.get_controllers", return_value=controllers), \
             patch("participium.routes.api.serialize_report_detail", return_value={"id": 1}), \
             patch("participium.routes.api.current_user", return_value=user), \
             patch("participium.core.auth.current_user", return_value=user):
            assign_resp = client.post("/api/v1/operator/reports/1/assign")
            status_resp = client.post("/api/v1/operator/reports/1/status", json={"status": "resolved", "note": "ok"})

        assert assign_resp.status_code == 200
        assert status_resp.status_code == 200
        controllers.operators.assign_report.assert_called_once_with(1, user)
        controllers.operators.update_status.assert_called_once_with(1, user, "resolved", "ok")

    def test_admin_category_and_stats_apis(self, client):
        user = self._make_user(Role.ADMIN)
        controllers = self._make_controllers()
        controllers.admin.list_categories.return_value = [Mock()]
        controllers.admin.create_category.return_value = Mock()
        controllers.admin.update_category.return_value = Mock()
        controllers.admin.admin_statistics.return_value = {"total": 42}

        with patch("participium.routes.api.get_controllers", return_value=controllers), \
             patch("participium.routes.api.serialize_category", return_value={"id": 1}), \
             patch("participium.routes.api.current_user", return_value=user), \
             patch("participium.core.auth.current_user", return_value=user):
            cat_list = client.get("/api/v1/admin/categories")
            cat_create = client.post("/api/v1/admin/categories", json={"name": "Roads"})
            cat_update = client.put("/api/v1/admin/categories/1", json={"is_active": "true"})
            stats = client.get("/api/v1/admin/stats")

        assert cat_list.status_code == 200
        assert cat_create.status_code == 201
        assert cat_update.status_code == 200
        assert stats.status_code == 200
        controllers.admin.create_category.assert_called_once_with("Roads")
        controllers.admin.update_category.assert_called_once_with(1, {"is_active": True})
        controllers.admin.admin_statistics.assert_called_once()

    def test_admin_update_category_parses_is_active(self, client):
        user = self._make_user(Role.ADMIN)
        controllers = self._make_controllers()
        controllers.admin.update_category.return_value = Mock()

        with patch("participium.routes.api.get_controllers", return_value=controllers), \
             patch("participium.routes.api.serialize_category", return_value={"id": 1}), \
             patch("participium.routes.api.current_user", return_value=user), \
             patch("participium.core.auth.current_user", return_value=user):
            resp = client.put("/api/v1/admin/categories/2", json={"is_active": "false"})

        assert resp.status_code == 200
        assert resp.get_json() == {"id": 1}
        controllers.admin.update_category.assert_called_once_with(2, {"is_active": False})

    def test_admin_update_category_without_is_active(self, client):
        user = self._make_user(Role.ADMIN)
        controllers = self._make_controllers() 
        controllers.admin.update_category.return_value = Mock()

        with patch("participium.routes.api.get_controllers", return_value=controllers), \
             patch("participium.routes.api.serialize_category", return_value={"id": 1}), \
             patch("participium.routes.api.current_user", return_value=user), \
             patch("participium.core.auth.current_user", return_value=user):
            resp = client.put("/api/v1/admin/categories/2", json={"name": "Services"})

        assert resp.status_code == 200
        assert resp.get_json() == {"id": 1}
        controllers.admin.update_category.assert_called_once_with(2, {"name": "Services"})

        