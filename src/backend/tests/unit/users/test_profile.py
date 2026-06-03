import pytest
from unittest.mock import MagicMock
from werkzeug.datastructures import FileStorage

from participium.services.user_service import UserService
from participium.models.user import User
from participium.core.exceptions import ValidationError


@pytest.fixture
def mock_deps():
    """Fixture providing all mocked dependencies for the UserService."""
    return {
        "session": MagicMock(),
        "user_repository": MagicMock(),
        "category_repository": MagicMock(),
        "token_repository": MagicMock(),
        "notification_repository": MagicMock(),
        "storage_service": MagicMock(),
    }


@pytest.fixture
def user_service(mock_deps):
    """Fixture providing an instance of UserService with injected mocks."""
    return UserService(**mock_deps)


@pytest.fixture
def dummy_user():
    """Fixture providing a standard user object for testing."""
    return User(
        id=1,
        username="samuel_b",
        first_name="Samuel",
        last_name="Bruno",
        email_notifications_enabled=True
    )


# --- Tests for update_profile ---

def test_update_profile_success(user_service, mock_deps, dummy_user):
    # Setup: simulate username is not taken
    mock_deps["user_repository"].get_by_username.return_value = None

    updated_user = user_service.update_profile(
        user=dummy_user,
        username="new_username ",
        first_name=" NewFirst ",
        last_name=" NewLast ",
        email_notifications_enabled=False
    )

    # Verify fields are updated and correctly stripped
    assert updated_user.username == "new_username"
    assert updated_user.first_name == "NewFirst"
    assert updated_user.last_name == "NewLast"
    assert updated_user.email_notifications_enabled is False

    # Verify DB commit
    mock_deps["session"].commit.assert_called_once()


def test_update_profile_with_picture(user_service, mock_deps, dummy_user):
    # Setup mock file storage
    mock_picture = MagicMock(spec=FileStorage)
    mock_picture.filename = "avatar.png"
    mock_deps["storage_service"].save.return_value = "/static/uploads/avatar.png"

    updated_user = user_service.update_profile(
        user=dummy_user,
        profile_picture=mock_picture
    )

    # Verify storage service integration
    mock_deps["storage_service"].save.assert_called_once_with(mock_picture)
    assert updated_user.profile_picture_path == "/static/uploads/avatar.png"
    mock_deps["session"].commit.assert_called_once()


def test_update_profile_username_already_in_use(user_service, mock_deps, dummy_user):
    # Setup: user repository returns another user for the requested username
    existing_user = User(id=2, username="taken_user")
    mock_deps["user_repository"].get_by_username.return_value = existing_user

    # Execute and Verify exception
    with pytest.raises(ValidationError, match="Username already in use."):
        user_service.update_profile(user=dummy_user, username="taken_user")


def test_update_profile_no_changes(user_service, mock_deps, dummy_user):
    # Test update with no optional parameters provided
    updated_user = user_service.update_profile(user=dummy_user)

    assert updated_user.username == "samuel_b"
    mock_deps["session"].commit.assert_called_once()


# --- Tests for delete_account ---

def test_delete_account_cascade(user_service, mock_deps, dummy_user):
    # 1. Setup internal mocked entities
    mock_report = MagicMock()
    mock_report.reporter_id = dummy_user.id
    mock_report.is_anonymous = False

    mock_follower = MagicMock()

    mock_message = MagicMock()
    mock_message.sender_id = dummy_user.id
    mock_message.recipient_id = dummy_user.id

    mock_history = MagicMock()
    mock_history.changed_by_id = dummy_user.id

    # session.scalars is called exactly 4 times for different entities.
    # We mock the return iteration in the exact order: Reports, Followers, Messages, Histories
    mock_deps["session"].scalars.side_effect = [
        [mock_report],
        [mock_follower],
        [mock_message],
        [mock_history]
    ]

    mock_notification = MagicMock()
    mock_deps["notification_repository"].list_for_user.return_value = [mock_notification]

    mock_token = MagicMock()
    mock_deps["token_repository"].list_for_user.return_value = [mock_token]

    # 2. Execute
    user_service.delete_account(dummy_user)

    # 3. Verify cascading logic applied to attributes
    assert mock_report.reporter_id is None
    assert mock_report.is_anonymous is True

    assert mock_message.sender_id is None
    assert mock_message.recipient_id is None

    assert mock_history.changed_by_id is None

    # 4. Verify cascading deletes on dependent entities
    mock_deps["session"].delete.assert_any_call(mock_follower)

    mock_deps["notification_repository"].list_for_user.assert_called_once_with(dummy_user.id)
    mock_deps["session"].delete.assert_any_call(mock_notification)

    mock_deps["token_repository"].list_for_user.assert_called_once_with(dummy_user.id)
    mock_deps["session"].delete.assert_any_call(mock_token)

    # 5. Verify user deletion and final commit
    mock_deps["user_repository"].delete.assert_called_once_with(dummy_user)
    mock_deps["session"].commit.assert_called_once()


def test_delete_account_message_branches(user_service, mock_deps, dummy_user):
    # Setup messages where the user is ONLY sender or ONLY recipient
    msg_sender_only = MagicMock(sender_id=dummy_user.id, recipient_id=999)
    msg_recipient_only = MagicMock(sender_id=999, recipient_id=dummy_user.id)

    # Mock the exact sequence for session.scalars
    mock_deps["session"].scalars.side_effect = [
        [],  # reports
        [],  # followers
        [msg_sender_only, msg_recipient_only],  # messages
        []  # histories
    ]

    mock_deps["notification_repository"].list_for_user.return_value = []
    mock_deps["token_repository"].list_for_user.return_value = []

    # Execute
    user_service.delete_account(dummy_user)

    # Verify branches
    assert msg_sender_only.sender_id is None
    assert msg_sender_only.recipient_id == 999
    assert msg_recipient_only.sender_id == 999
    assert msg_recipient_only.recipient_id is None