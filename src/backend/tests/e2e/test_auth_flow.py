from __future__ import annotations

from urllib.parse import urlparse
import pytest
from flask.testing import FlaskClient
from pathlib import Path
from participium.app import create_app


from participium import create_app
from participium.core.security import hash_password
from participium.database import close_connection, get_session
from participium.models.enums import Role
from participium.models.user import User

pytestmark = pytest.mark.e2e


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("AUTO_INIT_DB", "true")
    monkeypatch.setenv("BOOTSTRAP_REFERENCE_DATA", "false")
    monkeypatch.setenv("BOOTSTRAP_DEMO_DATA", "false")

    

    application = create_app()
    application.config.update(TESTING=True)
    
    yield application.test_client()
    
    close_connection()

def _register(client: FlaskClient, *, username: str, email: str, password: str = "Password1!") -> dict:
    payload = {
        "username": username,
        "first_name": username.split(".")[0].capitalize(),
        "last_name": username.split(".")[-1].capitalize(),
        "email": email,
        "password": password,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    return response, response.get_json()


def _verify(client: FlaskClient, verification_url: str):
    path = urlparse(verification_url).path
    return client.get(path)


def _login(client: FlaskClient, identifier: str, password: str = "Password1!"):
    return client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})


def _register_and_verify(client: FlaskClient, *, username: str, email: str, password: str = "Password1!"):
    resp, body = _register(client, username=username, email=email, password=password)
    assert resp.status_code == 201, f"Registration failed: {body}"
    _verify(client, body["verification_url"])
    return {"username": username, "email": email, "password": password}


def _create_admin_user(*, username: str, email: str, password: str = "Password1!") -> dict:
    session = get_session()
    admin = User(
        username=username,
        first_name=username.split(".")[0].capitalize(),
        last_name=username.split(".")[-1].capitalize(),
        email=email.lower(),
        password_hash=hash_password(password),
        role=Role.ADMIN,
        is_active=True,
        is_email_verified=True,
        email_notifications_enabled=True,
    )
    session.add(admin)
    session.commit()
    return {"username": username, "email": email, "password": password}


# registration

class TestRegisterEndpoint:
    def test_register_returns_201_with_user_data(self, client):
        response, body = _register(client, username="registered.user", email="registered.user@example.com")

        assert response.status_code == 201
        assert body["user"]["username"] == "registered.user"
        assert "verification_url" in body

    def test_register_missing_fields(self, client):
        response = client.post("/api/v1/auth/register", json={"username": "incomplete"})

        assert response.status_code == 400

    def test_register_duplicate_username(self, client):
        _register(client, username="duplicate.user", email="dup.user@example.com")

        response, _ = _register(client, username="duplicate.user", email="other@example.com")

        assert response.status_code == 400

    def test_register_duplicate_email(self, client):
        _register(client, username="first.user", email="shared@example.com")

        response, _ = _register(client, username="second.user", email="shared@example.com")

        assert response.status_code == 400


# Email verification

class TestVerifyEmailEndpoint:
    def test_verify_valid_token(self, client):
        response, body = _register(client, username="verify.tok", email="verify.tok@example.com")
        assert response.status_code == 201

        verify_resp = _verify(client, body["verification_url"])

        assert verify_resp.status_code == 200
        assert verify_resp.get_json()["message"] == "Email verified."

    def test_verify_invalid_token(self, client):
        response = client.get("/api/v1/auth/verify/not-a-real-token")

        assert response.status_code == 400

    def test_verify_same_token_twice(self, client):
        resp, body = _register(client, username="reuse.token", email="reuse.token@example.com")
        assert resp.status_code == 201

        _verify(client, body["verification_url"])
        second = _verify(client, body["verification_url"])

        assert second.status_code == 400


# login

class TestLoginEndpoint:
    def test_login_with_username(self, client):
        creds = _register_and_verify(client, username="login.user", email="login.user@example.com")

        response = _login(client, creds["username"])

        assert response.status_code == 200
        assert response.get_json()["message"] == "Logged in."

    def test_login_with_email(self, client):
        creds = _register_and_verify(client, username="login.email", email="login.email@example.com")

        response = _login(client, creds["email"])

        assert response.status_code == 200
        assert response.get_json()["user"]["email"] == creds["email"]

    def test_login_wrong_password(self, client):
        _register_and_verify(client, username="wrong.password", email="wrong.password@example.com")

        response = _login(client, "wrong.password", password="WrongPassword!")

        assert response.status_code == 401

    def test_login_unknown_user(self, client):
        response = _login(client, "unknown@example.com")

        assert response.status_code == 401

    def test_login_before_verification(self, client):
        _register(client, username="unverified.user", email="unverified@example.com")

        response = _login(client, "unverified.user")

        assert response.status_code == 401

        response = client.post("/api/v1/auth/login", json={"identifier": "", "password": ""})

        assert response.status_code == 401


#logout
class TestLogoutEndpoint:
    def test_logout_after_login(self, client):
        _register_and_verify(client, username="user", email="user@example.com")
        _login(client, "user")

        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        assert response.get_json()["message"] == "Logged out."

    def test_logout_without_login(self, client):
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200


#full flow: register -> verify -> login
class TestAuthFlows:
    def test_register_verify_login(self, client):
        response, body = _register(client, username="user", email="user@example.com")
        assert response.status_code == 201

        assert _login(client, "user").status_code == 401

        assert _verify(client, body["verification_url"]).status_code == 200

        login_resp = _login(client, "user")
        assert login_resp.status_code == 200
        assert login_resp.get_json()["user"]["username"] == "user"

    def test_login_response_contains_user_fields(self, client):

        _register_and_verify(client, username="fields.check", email="fields.check@example.com")

        resp = _login(client, "fields.check")
        user_data = resp.get_json()["user"]

        assert "username" in user_data
        assert "email" in user_data
        assert user_data["username"] == "fields.check"


    def test_protected_endpoint_without_login(self, client):
        resp = client.get("/api/v1/users/me")

        assert resp.status_code == 401

    def test_admin_endpoint_as_citizen(self, client):
        _register_and_verify(client, username="citizen.user", email="citizen.user@example.com")
        _login(client, "citizen.user")

        resp = client.get("/api/v1/admin/users")

        assert resp.status_code == 403


class TestAdminUserManagement:
    def test_admin_can_access_admin_endpoint(self, client):
        cred = _create_admin_user(
            username="admin.user",
            email="admin@example.com",
            password="Admin123!"
        )

        _login(client, cred["email"], password="Admin123!")

        resp = client.get("/api/v1/admin/users")

        assert resp.status_code == 200


    def test_create_admin_user(self,client):
        cred = _create_admin_user(
            username="admin.user",
            email="admin@example.com",
            password="Admin123!"
        )
        _login(client, cred["email"], password="Admin123!")
        create_resp = client.post("/api/v1/admin/users", json={
            "username": "user.to.update",
            "first_name": "Before",
            "last_name": "Update",
            "email": "user.to.update@example.com",
            "password": "Password1!",
            "role": "citizen",
        })
        assert create_resp.status_code == 201
        user_id = create_resp.get_json()["id"]

        resp = client.put(f"/api/v1/admin/users/{user_id}", json={"first_name": "After"})

        assert resp.status_code == 200
        assert resp.get_json()["first_name"] == "After"



    def test_admin_update_nonexistent_user(self,client):
        cred = _create_admin_user(
            username="admin.user",
            email="admin@example.com",
            password="Admin123!"
        )

        _login(client, cred["email"], password="Admin123!")

        resp = client.put("/api/v1/admin/users/999", json={"username": "nonexistent.user"})
        assert resp.status_code == 404



class TestAppHooks:

    def test_inactive_user_session_is_cleared(self, client):
        _register_and_verify(client, username="inactive.user", email="inactive.user@example.com")
        _login(client, "inactive.user")

        _create_admin_user(username="admin.user", email="admin@example.com", password="Admin123!")
        admin_client = client.application.test_client()
        _login(admin_client, "admin@example.com", password="Admin123!")

        users_resp = admin_client.get("/api/v1/admin/users")
        users = users_resp.get_json()
        user_id = next(u["id"] for u in users if u["username"] == "inactive.user")
        admin_client.put(f"/api/v1/admin/users/{user_id}", json={"is_active": False})

        # log back in as the now-inactive user's session (still has cookie)
        _login(client, "inactive.user")  # this will fail
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401

