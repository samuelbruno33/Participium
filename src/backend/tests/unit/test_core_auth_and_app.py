from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from participium import create_app
from participium.database import close_connection
from participium.core.auth import roles_required
from participium.core.exceptions import AuthenticationError, AuthorizationError
from participium.core.auth import login_required
from flask import g
from pathlib import Path
from participium.config.settings import Settings
from participium.app import create_app



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

class TestCoreAuth:

    def test_api_requires_login(self, client):
        @login_required
        def view():
            return "ok"

        with client.application.test_request_context("/api/v1/resource"):
            from flask import g
            if hasattr(g, "current_user"):
                delattr(g, "current_user")

            with pytest.raises(AuthenticationError):
                view()

    def test_page_redirects_to_login(self, client):

        @login_required
        def view():
            return "ok"

        with patch("participium.core.auth.url_for", lambda endpoint, **values: "/login?next=" + values.get("next", "")):
            with client.application.test_request_context("/some/page"):
                if hasattr(g, "current_user"):
                    delattr(g, "current_user")

                resp = view()
                assert resp.status_code in (301, 302, 303, 307, 308)
                assert resp.headers["Location"] == "/login?next=/some/page"

    def test_roles_required(self, client):

        @roles_required("admin")
        def view():
            return "ok"

        with client.application.test_request_context("/"):
            if hasattr(g, "current_user"):
                delattr(g, "current_user")
            with pytest.raises(AuthenticationError):
                view()

        with client.application.test_request_context("/"):
            g.current_user = Mock()
            g.current_user.role = "citizen"
            with pytest.raises(AuthorizationError):
                view()

        with client.application.test_request_context("/"):
            g.current_user = Mock()
            g.current_user.role = "admin"
            assert view() == "ok"

class TestApp:
    
    def test_create_app_runs_seeders(self, monkeypatch):
        monkeypatch.setenv("BOOTSTRAP_REFERENCE_DATA", "true")
        monkeypatch.setenv("BOOTSTRAP_DEMO_DATA", "true")

        with patch("participium.app.open_connection") as mock_open_conn, \
             patch("participium.app.create_all") as mock_create_all, \
             patch("participium.app.seed_reference_data") as mock_ref, \
             patch("participium.app.seed_demo_data") as mock_demo:
            create_app()
            mock_open_conn.assert_called_once()
            mock_create_all.assert_called_once()
            mock_ref.assert_called_once()
            mock_demo.assert_called_once()


    def test_create_app_without_auto_init(self):

        settings = Settings(
            app_name="participium",
            secret_key="test-key",
            debug=False,
            frontend_origin="http://localhost",
            host="0.0.0.0",
            port=5050,
            auto_init_db=False,
            bootstrap_reference_data=False,
            bootstrap_demo_data=False,
            mail_backend="console",
            mail_from="test@example.com",
            mail_outbox_dir=Path.cwd(),
            smtp_host=None,
            smtp_port=587,
            smtp_username=None,
            smtp_password=None,
            smtp_use_tls=False,
            expose_verification_links=True,
            media_root=Path.cwd(),
            max_content_length=1024 * 1024,
            instance_path=Path.cwd(),
        )

        with patch("participium.app.open_connection") as mock_open_conn, \
             patch("participium.app.create_all") as mock_create_all, \
             patch("participium.app.seed_reference_data") as mock_ref, \
             patch("participium.app.seed_demo_data") as mock_demo, \
             patch("participium.app.init_swagger") as mock_init_swagger, \
             patch("participium.app.register_blueprints") as mock_register_blueprints, \
             patch("participium.app.AppContainer") as mock_app_container:
            create_app(settings=settings)

        mock_open_conn.assert_called_once()
        mock_create_all.assert_not_called()
        mock_ref.assert_not_called()
        mock_demo.assert_not_called()
        mock_init_swagger.assert_called_once()
        mock_register_blueprints.assert_called_once()


