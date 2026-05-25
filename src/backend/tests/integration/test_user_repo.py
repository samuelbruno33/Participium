import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from participium.models.base import Base
from participium.models.user import User
from participium.models.enums import Role
from participium.repositories.user_repository import UserRepository


@pytest.fixture(scope="module")
def db_engine():
    """Create an in-memory SQLite engine and initialize the schema."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Provide a clean database session for a single test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def user_repo(db_session):
    """Provide a UserRepository bound to the test session."""
    return UserRepository(db_session)


def test_integration_add_and_get_user(user_repo, db_session):
    # 1. Setup: Create and persist a real User object
    new_user = User(
        username="integration_user",
        email="integration@example.com",
        first_name="Test",
        last_name="User",
        password_hash="fake_hash",
        role=Role.CITIZEN,
        is_active=True
    )
    user_repo.add(new_user)
    db_session.commit()

    # 2. Execute: Retrieve via different repository methods
    fetched_by_username = user_repo.get_by_username("integration_user")
    fetched_by_email = user_repo.get_by_email("integration@example.com")

    # 3. Verify: Assert properties match database state
    assert fetched_by_username is not None
    assert fetched_by_username.id == new_user.id
    assert fetched_by_email is not None
    assert fetched_by_email.username == "integration_user"


def test_integration_delete_user(user_repo, db_session):
    # 1. Setup: Insert a user into the DB
    user_to_delete = User(
        username="to_delete",
        email="delete@example.com",
        first_name="Delete",
        last_name="Me",
        password_hash="fake_hash",
        role=Role.CITIZEN
    )
    user_repo.add(user_to_delete)
    db_session.commit()

    # Ensure it exists before deletion
    assert user_repo.get_by_username("to_delete") is not None

    # 2. Execute: Delete the user
    user_repo.delete(user_to_delete)
    db_session.commit()

    # 3. Verify: Check that it no longer exists
    assert user_repo.get_by_username("to_delete") is None


def test_integration_get_by_id(user_repo, db_session):
    # 1. Setup
    new_user = User(
        username="id_user",
        email="id@example.com",
        first_name="Test",
        last_name="User",
        password_hash="fake_hash",
        role=Role.CITIZEN
    )
    user_repo.add(new_user)
    db_session.commit()

    # 2. Execute
    fetched_user = user_repo.get_by_id(new_user.id)

    # 3. Verify
    assert fetched_user is not None
    assert fetched_user.username == "id_user"


def test_integration_get_by_username_or_email(user_repo, db_session):
    # 1. Setup
    new_user = User(
        username="multi_user",
        email="multi@example.com",
        first_name="Test",
        last_name="User",
        password_hash="fake_hash",
        role=Role.CITIZEN
    )
    user_repo.add(new_user)
    db_session.commit()

    # 2. Execute
    fetched_by_username = user_repo.get_by_username_or_email("multi_user")
    fetched_by_email = user_repo.get_by_username_or_email("multi@example.com")
    fetched_none = user_repo.get_by_username_or_email("nonexistent")

    # 3. Verify
    assert fetched_by_username is not None
    assert fetched_by_username.id == new_user.id

    assert fetched_by_email is not None
    assert fetched_by_email.id == new_user.id

    assert fetched_none is None


def test_integration_list_all(user_repo, db_session):
    # 1. Setup
    user1 = User(
        username="list_user1",
        email="list1@example.com",
        first_name="A",
        last_name="B",
        password_hash="hash",
        role=Role.CITIZEN
    )
    user2 = User(
        username="list_user2",
        email="list2@example.com",
        first_name="C",
        last_name="D",
        password_hash="hash",
        role=Role.CITIZEN
    )
    user_repo.add(user1)
    user_repo.add(user2)
    db_session.commit()

    # 2. Execute
    users = user_repo.list_all()

    # 3. Verify
    assert len(users) >= 2
    usernames = [u.username for u in users]
    assert "list_user1" in usernames
    assert "list_user2" in usernames