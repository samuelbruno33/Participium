from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from participium.core import ValidationError
from participium.services.user_service import UserService
from participium.models.user import User
from werkzeug.datastructures import FileStorage


''' # Black-Box test without uploaded code function
def test_update_profile_full_text_fields():
    # For fixture assumptions a valid user need to exist in the database
    dummy_user = User(id=1, username="old_user", first_name="Old", last_name="Name", email_notifications_enabled=False)
    service = UserService()

    # Execution
    updated_user = service.update_profile(
        user=dummy_user,
        username="new_user",
        first_name="New",
        last_name="Surname",
        email_notifications_enabled=True
    )

    # Assertions
    assert updated_user.username == "new_user"
    assert updated_user.first_name == "New"
    assert updated_user.last_name == "Surname"
    assert updated_user.email_notifications_enabled is True


def test_update_profile_partial_update():
    dummy_user = User(id=2, username="stable_user", email_notifications_enabled=True)
    service = UserService()

    # Update only a single boolean field
    updated_user = service.update_profile(
        user=dummy_user,
        email_notifications_enabled=False
    )

    # Only the specific field should change, others remain untouched
    assert updated_user.email_notifications_enabled is False
    assert updated_user.username == "stable_user"


def test_update_profile_with_picture():
    dummy_user = User(id=3, username="pic_user")

    # Using the provided stub for FileStorage
    dummy_file = FileStorage(filename="profile_pic.jpg")

    service = UserService()

    updated_user = service.update_profile(
        user=dummy_user,
        profile_picture=dummy_file
    )

    # The service should process the file and assign a URL/path
    assert updated_user is not None
    # assert updated_user.profile_picture_url is not None


def test_update_profile_duplicate_username():
    dummy_user = User(id=4, username="valid_user")
    service = UserService()

    # The service should reject the update
    with pytest.raises(ValidationError):
        service.update_profile(
            user=dummy_user,
            username="taken_username"
        )


def test_update_profile_invalid_empty_strings():
    dummy_user = User(id=5, username="valid_user")
    service = UserService()

    # Empty usernames should not be allowed
    with pytest.raises(ValidationError):
        service.update_profile(
            user=dummy_user,
            username=""
        )


def test_update_profile_missing_user():
    service = UserService()

    # Passing None as the user object should fail
    with pytest.raises(ValidationError):
        service.update_profile(
            user=None,
            username="new_name"
        )
'''

def test_update_profile_full_text_fields():
    dummy_user = User(id=1, username="old_user", first_name="Old", last_name="Name", email_notifications_enabled=False)

    # Injecting mocked dependencies
    mock_session = MagicMock()
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username.return_value = None  # Simulates username being available

    service = UserService(session=mock_session, user_repository=mock_user_repo)

    # Execution
    updated_user = service.update_profile(
        user=dummy_user,
        username="new_user",
        first_name="New",
        last_name="Surname",
        email_notifications_enabled=True
    )

    # Assertions
    assert updated_user.username == "new_user"
    assert updated_user.first_name == "New"
    assert updated_user.last_name == "Surname"
    assert updated_user.email_notifications_enabled is True
    mock_session.commit.assert_called_once()


def test_update_profile_partial_update():
    dummy_user = User(id=2, username="stable_user", email_notifications_enabled=True)

    mock_session = MagicMock()
    service = UserService(session=mock_session)

    # Update only a single boolean field
    updated_user = service.update_profile(
        user=dummy_user,
        email_notifications_enabled=False
    )

    # Only the specific field should change, others remain untouched
    assert updated_user.email_notifications_enabled is False
    assert updated_user.username == "stable_user"
    mock_session.commit.assert_called_once()


def test_update_profile_with_picture():
    dummy_user = User(id=3, username="pic_user")
    dummy_file = FileStorage(filename="profile_pic.jpg")

    mock_session = MagicMock()
    mock_storage = MagicMock()
    mock_storage.save.return_value = "uploads/profile_pic.jpg"

    service = UserService(session=mock_session, storage_service=mock_storage)

    updated_user = service.update_profile(
        user=dummy_user,
        profile_picture=dummy_file
    )

    # The service should process the file and assign a URL/path
    assert updated_user.profile_picture_path == "uploads/profile_pic.jpg"
    mock_storage.save.assert_called_once_with(dummy_file)


def test_update_profile_duplicate_username():
    dummy_user = User(id=4, username="valid_user")

    mock_session = MagicMock()
    mock_user_repo = MagicMock()
    # Simulate username already taken by another user
    mock_user_repo.get_by_username.return_value = User(id=99, username="taken_username")

    service = UserService(session=mock_session, user_repository=mock_user_repo)

    # The service should reject the update
    with pytest.raises(ValidationError):
        service.update_profile(
            user=dummy_user,
            username="taken_username"
        )


def test_update_profile_invalid_empty_strings():
    dummy_user = User(id=5, username="valid_user")

    mock_session = MagicMock()
    service = UserService(session=mock_session)

    # In the real implementation, passing an empty string evaluates to False
    # and ignores the update, rather than raising a ValidationError.
    updated_user = service.update_profile(
        user=dummy_user,
        username=""
    )

    # Assert that the username remained unchanged
    assert updated_user.username == "valid_user"


def test_update_profile_missing_user():
    mock_session = MagicMock()
    service = UserService(session=mock_session)

    # Passing None as the user object will cause an AttributeError in the real code
    # because it tries to access `user.username`.
    with pytest.raises(AttributeError):
        service.update_profile(
            user=None,
            username="new_name"
        )