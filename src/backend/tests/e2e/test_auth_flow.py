from __future__ import annotations

from urllib.parse import urlparse
import pytest
from flask.testing import FlaskClient

from participium import create_app
from participium.database import close_connection

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


