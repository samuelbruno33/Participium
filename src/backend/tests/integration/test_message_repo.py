from __future__ import annotations

import pytest

from participium.database import open_connection, close_connection, create_all, get_session
from participium.models.enums import Role, ReportStatus
from participium.models.user import User
from participium.models.report import Report
from participium.models.message import Message
from participium.models.category import Category
from participium.repositories.message_repository import MessageRepository

@pytest.fixture
def db_session(monkeypatch):
    """Create an in-memory SQLite database for integration testing."""
    # Force the app to use an in-memory database
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    
    open_connection()
    create_all()
    session = get_session()
    
    yield session
    
    close_connection()

@pytest.fixture
def setup_data(db_session):
    """Seed the in-memory DB with the minimal entities required for messaging."""
    # Create Category
    category = Category(name="Roads", is_active=True)
    db_session.add(category)
    db_session.flush()
    
    # Create Users
    citizen = User(
        username="citizen_joe",
        email="joe@example.com",
        password_hash="hash",
        role=Role.CITIZEN,
        first_name="Joe",
        last_name="Citizen"
    )
    operator = User(
        username="op_anna",
        email="anna@example.com",
        password_hash="hash",
        role=Role.OPERATOR,
        category_id=category.id,
        first_name="Anna",
        last_name="Operator"
    )
    db_session.add_all([citizen, operator])
    db_session.flush()
    
    # Create Report
    report = Report(
        title="Pothole",
        description="Big hole in the street",
        latitude=45.0,
        longitude=9.0,
        status=ReportStatus.ASSIGNED,
        reporter_id=citizen.id,
        category_id=category.id
    )
    db_session.add(report)
    db_session.commit()
    
    return {
        "citizen": citizen,
        "operator": operator,
        "report": report
    }

def test_add_and_retrieve_message(db_session, setup_data):
    repo = MessageRepository(db_session)
    report = setup_data["report"]
    citizen = setup_data["citizen"]
    operator = setup_data["operator"]
    
    new_msg = Message(
        report_id=report.id,
        sender_id=citizen.id,
        recipient_id=operator.id,
        body="Hello, is anyone fixing this?"
    )
    
    repo.add(new_msg)
    db_session.commit()
    
    messages = repo.list_for_report(report.id)
    assert len(messages) == 1
    assert messages[0].body == "Hello, is anyone fixing this?"
    assert messages[0].sender_id == citizen.id
    assert messages[0].recipient_id == operator.id

def test_list_for_report_isolation(db_session, setup_data):
    repo = MessageRepository(db_session)
    report = setup_data["report"]
    citizen = setup_data["citizen"]
    operator = setup_data["operator"]
    
    # Create a second report
    other_report = Report(
        title="Other",
        description="Other",
        latitude=45.1,
        longitude=9.1,
        reporter_id=citizen.id,
        category_id=report.category_id
    )
    db_session.add(other_report)
    db_session.flush()
    
    # Message for original report
    db_session.add(Message(report_id=report.id, sender_id=citizen.id, recipient_id=operator.id, body="Msg 1"))
    # Message for other report
    db_session.add(Message(report_id=other_report.id, sender_id=citizen.id, recipient_id=operator.id, body="Msg 2"))
    db_session.commit()
    
    # Verify isolation
    report_messages = repo.list_for_report(report.id)
    assert len(report_messages) == 1
    assert report_messages[0].body == "Msg 1"