from __future__ import annotations

import pytest
from participium.models.enums import Role, ReportStatus
from participium import create_app
from participium.database import close_connection, get_session

@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    """Create the Flask application instance for testing."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///file:test_messaging?mode=memory&cache=shared")
    monkeypatch.setenv("AUTO_INIT_DB", "true")
    monkeypatch.setenv("BOOTSTRAP_REFERENCE_DATA", "false")
    monkeypatch.setenv("BOOTSTRAP_DEMO_DATA", "false")

    application = create_app()
    application.config.update(TESTING=True)
    
    return application
    
@pytest.fixture
def db_session(app):
    """Provides access to the database session used by the test client."""
    with app.app_context():
        yield get_session()

@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    yield app.test_client()
    close_connection()

@pytest.fixture
def messaging_setup(client, db_session):
    """Setup a report and two users for a messaging conversation."""
    # Create a category
    from participium.models.category import Category
    category = Category(name="Infrastructure", is_active=True)
    db_session.add(category)
    db_session.flush()

    # Create users
    from participium.models.user import User
    from participium.core.security import hash_password
    
    citizen = User(
        username="citizen_e2e", email="citizen@test.com", 
        password_hash=hash_password("Password123!"), role=Role.CITIZEN,
        is_active=True, is_email_verified=True, first_name="Joe", last_name="Citizen"
    )
    operator = User(
        username="operator_e2e", email="operator@test.com", 
        password_hash=hash_password("Password123!"), role=Role.OPERATOR,
        category_id=category.id, is_active=True, is_email_verified=True,
        first_name="Anna", last_name="Operator"
    )
    stranger = User(
        username="stranger_e2e", email="stranger@test.com",
        password_hash=hash_password("Password123!"), role=Role.CITIZEN,
        is_active=True, is_email_verified=True, first_name="Bob", last_name="Stranger"
    )
    db_session.add_all([citizen, operator, stranger])
    db_session.flush()

    # Create an assigned report
    from participium.models.report import Report, ReportStatusHistory
    report = Report(
        title="E2E Broken Light", description="Test", latitude=45.0, longitude=9.0,
        status=ReportStatus.ASSIGNED, reporter_id=citizen.id, category_id=category.id
    )
    db_session.add(report)
    db_session.flush()

    # Add history entry so recipient can be resolved (Operator assigned it)
    history = ReportStatusHistory(
        report_id=report.id, previous_status=ReportStatus.PENDING_APPROVAL,
        new_status=ReportStatus.ASSIGNED, changed_by_id=operator.id
    )
    db_session.add(history)
    db_session.commit()

    return {
        "report_id": report.id,
        "citizen_creds": ("citizen@test.com", "Password123!"),
        "operator_creds": ("operator@test.com", "Password123!"),
        "stranger_creds": ("stranger@test.com", "Password123!")
    }

def _login(client, email, password):
    resp = client.post("/api/v1/auth/login", json={"identifier": email, "password": password})
    return resp

def test_full_messaging_lifecycle(client, messaging_setup):
    report_id = messaging_setup["report_id"]
    
    # 1. Login as Citizen and send a message
    _login(client, *messaging_setup["citizen_creds"])
    
    resp = client.post(f"/api/v1/reports/{report_id}/messages", 
                       json={"body": "When will it be fixed?"})
    assert resp.status_code == 201
    assert resp.json["body"] == "When will it be fixed?"

    # 2. Login as Operator and reply
    _login(client, *messaging_setup["operator_creds"])
    
    # Check operator can see the message
    resp = client.get(f"/api/v1/reports/{report_id}/messages")
    assert resp.status_code == 200
    assert len(resp.json) == 1

    # Send reply
    resp = client.post(f"/api/v1/reports/{report_id}/messages", 
                       json={"body": "Tomorrow morning."})
    assert resp.status_code == 201

    # 3. Citizen views the reply
    _login(client, *messaging_setup["citizen_creds"])
    resp = client.get(f"/api/v1/reports/{report_id}/messages")
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert resp.json[1]["body"] == "Tomorrow morning."

def test_messaging_access_control(client, messaging_setup):
    report_id = messaging_setup["report_id"]
    
    # Login as Stranger
    _login(client, *messaging_setup["stranger_creds"])
    
    # Try to view messages of a report they don't own
    resp = client.get(f"/api/v1/reports/{report_id}/messages")
    assert resp.status_code == 403
    assert "access" in resp.get_data(as_text=True).lower()

    # Try to send a message to that report
    resp = client.post(f"/api/v1/reports/{report_id}/messages", 
                        json={"body": "I am snooping"})
    assert resp.status_code == 403