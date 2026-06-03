import pytest
from flask.testing import FlaskClient

from participium import create_app
from participium.database import close_connection, get_session
from participium.models.user import User
from participium.models.enums import Role
from participium.core.security import hash_password


@pytest.fixture
def client(monkeypatch):
    """Configure the Flask test client with an in-memory database."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("AUTO_INIT_DB", "true")
    monkeypatch.setenv("BOOTSTRAP_REFERENCE_DATA", "false")
    monkeypatch.setenv("BOOTSTRAP_DEMO_DATA", "false")

    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client

    close_connection()


@pytest.fixture
def authenticated_client(client):
    """Provide a test client logged in as a standard citizen user."""
    session = get_session()

    # 1. Seed a user into the test database
    user = User(
        username="test_citizen",
        email="citizen@example.com",
        first_name="Test",
        last_name="Citizen",
        password_hash=hash_password("secure_pass"),
        role=Role.CITIZEN,
        is_active=True,
        is_email_verified=True
    )
    session.add(user)
    session.commit()

    # 2. Authenticate the client via the API
    client.post("/api/v1/auth/login", json={
        "identifier": "test_citizen",
        "password": "secure_pass"
    })

    return client


def test_e2e_update_profile_success(authenticated_client):
    # Execute: Update profile fields via API
    response = authenticated_client.put("/api/v1/users/me", json={
        "username": "updated_citizen",
        "first_name": "NewFirst",
        "last_name": "NewLast",
        "email_notifications_enabled": False
    })

    # Verify: HTTP status and JSON response
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "updated_citizen"
    assert data["first_name"] == "NewFirst"
    assert data["last_name"] == "NewLast"
    assert data["email_notifications_enabled"] is False

    # Verify: Database state has actually changed
    session = get_session()
    db_user = session.query(User).filter_by(email="citizen@example.com").first()
    assert db_user.username == "updated_citizen"


def test_e2e_update_profile_username_taken(client, authenticated_client):
    # Setup: Create another user that holds the target username
    session = get_session()
    other_user = User(
        username="taken_name",
        email="other@example.com",
        first_name="Other",
        last_name="User",
        password_hash="hash",
        role=Role.CITIZEN,
        is_active=True,
        is_email_verified=True
    )
    session.add(other_user)
    session.commit()

    # Execute: Attempt to update the authenticated user's username to the taken one
    response = authenticated_client.put("/api/v1/users/me", json={
        "username": "taken_name"
    })

    # Verify: API rejects the request with a 400 Bad Request
    assert response.status_code == 400


def test_e2e_delete_account(authenticated_client):
    # Execute: Request account deletion via API
    response = authenticated_client.delete("/api/v1/users/me")

    # Verify: HTTP status and response message
    assert response.status_code == 200
    assert response.get_json()["message"] == "Account deleted."

    # Verify: User is physically removed from the database
    session = get_session()
    deleted_user = session.query(User).filter_by(username="test_citizen").first()
    assert deleted_user is None