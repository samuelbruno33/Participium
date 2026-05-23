from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.core.exceptions import NotFoundError, ValidationError
from participium.models.enums import Role
from participium.services.user_service import UserService
from tests.conftest import user as _user, category as _category

@pytest.fixture
def user_bundle():
    session = Mock()
    user_repository = Mock()
    category_repository = Mock()
    token_repository = Mock()
    notification_repository = Mock()
    storage_service = Mock()
    service = UserService(
        session=session,
        user_repository=user_repository,
        category_repository=category_repository,
        token_repository=token_repository,
        notification_repository=notification_repository,
        storage_service=storage_service,
    )
    return {
        "service": service,
        "session": session,
        "user_repository": user_repository,
        "category_repository": category_repository,
        "token_repository": token_repository,
        "notification_repository": notification_repository,
        "storage_service": storage_service,
    }


class TestListAndGetUsers:

    def test_get_user_returns_user(self, user_bundle):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        expected_user = _user()
        user_repository.get_by_id.return_value = expected_user

        result = service.get_user(expected_user.id)

        assert result == expected_user

    def test_get_user_not_found(self, user_bundle):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        user_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="User not found"):
            service.get_user(999)


class TestCreateUser:

    def test_create_citizen_and_commits(self, user_bundle,user_payload):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        session = user_bundle["session"]

        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        result = service.create_user(user_payload)

        assert result.username == "new.user"
        assert result.role == Role.CITIZEN
        assert result.is_email_verified is True
        assert result.email == "new.user@example.com"

        user_repository.add.assert_called_once_with(result)
        session.commit.assert_called_once()

   
    @pytest.mark.parametrize("missing_field", ["username", "email","password","role",])
    def test_rejects_missing_required_fields(self, user_bundle, missing_field,user_payload):
        service = user_bundle["service"]
        payload = {k: v for k, v in user_payload.items() if k != missing_field}
        with pytest.raises(ValidationError, match="Missing required fields"):
            service.create_user(payload)



    @pytest.mark.parametrize(("field", "repo_method", "error"),[("username", "get_by_username", "Username already in use"),("email", "get_by_email", "Email already in use"),],)
    def test_raises_on_duplicate_username_or_email(self,user_bundle,repo_method,error,field,user_payload):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]

        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        getattr(user_repository, repo_method).return_value = _user()

        with pytest.raises(ValidationError, match=error):
            service.create_user(user_payload)


    def test_raises_on_invalid_role(self, user_bundle, user_payload):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        payload = {**user_payload, "role": "superadmin"}
        with pytest.raises(ValidationError, match="Invalid user role"):
            service.create_user(payload)

    def test_creates_operator_with_active_category(self, user_bundle, user_payload):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        category_repository = user_bundle["category_repository"]
        session = user_bundle["session"]

        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None
        category_repository.get_by_id.return_value = _category(category_id=4, is_active=True)

        payload = {**user_payload, "role": "operator", "category_id": 4}
        result = service.create_user(payload)

        assert result.role == Role.OPERATOR
        assert result.category_id == 4
        session.commit.assert_called_once()

    def test_operator_without_category(self, user_bundle, user_payload):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        payload = {**user_payload, "role": "operator"}
        with pytest.raises(ValidationError):
            service.create_user(payload)


    def test_operator_with_inactive_category(self, user_bundle, user_payload):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        category_repository = user_bundle["category_repository"]

        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None
        category_repository.get_by_id.return_value = _category(category_id=4, is_active=False)

        payload = {**user_payload, "role": "operator", "category_id": 4}
        with pytest.raises(ValidationError):
            service.create_user(payload)


    def test_operator_with_nonexistent_category(self, user_bundle, user_payload):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        category_repository = user_bundle["category_repository"]

        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None
        category_repository.get_by_id.return_value = None

        payload = {**user_payload, "role": "operator", "category_id": 99}
        with pytest.raises(ValidationError):
            service.create_user(payload)


    def test_is_active_can_be_set_false(self, user_bundle, user_payload):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        result = service.create_user({**user_payload, "is_active": False})
        assert result.is_active is False

    def test_strips_whitespace_from_string_fields(self, user_bundle, user_payload):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        payload = {**user_payload, "username": "  spaced  ", "first_name": " Mario "}
        result = service.create_user(payload)
        assert result.username == "spaced"
        assert result.first_name == "Mario"


class TestUpdateUser:
    def test_updates_fields(self, user_bundle):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        session = user_bundle["session"]
        user = _user()
        user_repository.get_by_id.return_value = user
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        result = service.update_user(user.id, {"username": "updated_user", "email": "updated_user@example.com"})

        assert result.username == "updated_user"
        assert result.email == "updated_user@example.com"
        session.commit.assert_called_once()

    def test_update_user_raises_username_conflict(self, user_bundle):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        current_user = _user()
        user_repository.get_by_id.return_value = current_user
        user_repository.get_by_username.return_value = _user(user_id=2, username="existing.user")

        with pytest.raises(ValidationError, match="Username already in use"):
            service.update_user(current_user.id, {"username": "existing.user"})

    def test_update_user_raises_email_conflict(self, user_bundle):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        current_user = _user()
        user_repository.get_by_id.return_value = current_user
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = _user(user_id=2, email="existing@example.com")

        with pytest.raises(ValidationError, match="Email already in use"):
            service.update_user(current_user.id, {"email": "existing@example.com"})

    def test_update_user_rejects_invalid_role(self, user_bundle):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        current_user = _user()
        user_repository.get_by_id.return_value = current_user
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        with pytest.raises(ValidationError, match="Invalid user role"):
            service.update_user(current_user.id, {"role": "superadmin"})


    def test_update_user_operator_missing_category(self, user_bundle):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        current_user = _user()
        user_repository.get_by_id.return_value = current_user
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        with pytest.raises(ValidationError, match="Operator category is required"):
            service.update_user(current_user.id, {"role": "operator"})

    def test_update_user_operator_inactive_category(self, user_bundle):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        category_repository = user_bundle["category_repository"]
        current_user = _user()
        user_repository.get_by_id.return_value = current_user
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None
        category_repository.get_by_id.return_value = _category(category_id=5, is_active=False)

        with pytest.raises(ValidationError, match="A valid active category is required for operators"):
            service.update_user(current_user.id, {"role": "operator", "category_id": 5})

    def test_update_user_operator_assigns_category(self, user_bundle):
        service = user_bundle["service"]
        user_repository = user_bundle["user_repository"]
        category_repository = user_bundle["category_repository"]
        current_user = _user()
        user_repository.get_by_id.return_value = current_user
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None
        category_repository.get_by_id.return_value = _category(category_id=5, is_active=True)

        result = service.update_user(current_user.id, {"role": "operator", "category_id": 5})

        assert result.role == Role.OPERATOR
        assert result.category_id == 5


class TestDeleteAccount:
    def _setup_session_scalars(self, session, *result_lists):
        session.scalars.side_effect = [iter(result_list) for result_list in result_lists]

    def test_deletes_user_and_commits(self, user_bundle):
        service = user_bundle["service"]
        session = user_bundle["session"]
        user_repository = user_bundle["user_repository"]
        notification_repository = user_bundle["notification_repository"]
        token_repository = user_bundle["token_repository"]

        user = _user()
        self._setup_session_scalars(session, [], [], [], [])
        notification_repository.list_for_user.return_value = []
        token_repository.list_for_user.return_value = []

        service.delete_account(user)

        user_repository.delete.assert_called_once_with(user)
        session.commit.assert_called_once()

    def test_anonymises_reports(self, user_bundle):
        service = user_bundle["service"]
        session = user_bundle["session"]
        notification_repository = user_bundle["notification_repository"]
        token_repository = user_bundle["token_repository"]

        user = _user(user_id=9)

        report = Mock()
        report.reporter_id = 9
        report.is_anonymous = False

        self._setup_session_scalars(session, [report], [], [], [])
        notification_repository.list_for_user.return_value = []
        token_repository.list_for_user.return_value = []

        service.delete_account(user)

        assert report.reporter_id is None
        assert report.is_anonymous is True

    def test_deletes_report_followers(self, user_bundle):
        service = user_bundle["service"]
        session = user_bundle["session"]
        notification_repository = user_bundle["notification_repository"]
        token_repository = user_bundle["token_repository"]

        user = _user(user_id=7)
        follower = Mock()

        self._setup_session_scalars(session, [], [follower], [], [])
        notification_repository.list_for_user.return_value = []
        token_repository.list_for_user.return_value = []

        service.delete_account(user)

        session.delete.assert_any_call(follower)

    def test_nullifies_message_sender_and_recipient(self, user_bundle):
        service = user_bundle["service"]
        session = user_bundle["session"]
        notification_repository = user_bundle["notification_repository"]
        token_repository = user_bundle["token_repository"]

        user = _user(user_id=9)

        message_sent = Mock()
        message_sent.sender_id = 9
        message_sent.recipient_id = 99

        message_received = Mock()
        message_received.sender_id = 99
        message_received.recipient_id = 9

        self._setup_session_scalars(session, [], [], [message_sent, message_received], [])
        notification_repository.list_for_user.return_value = []
        token_repository.list_for_user.return_value = []

        service.delete_account(user)

        assert message_sent.sender_id is None
        assert message_sent.recipient_id == 99 
        assert message_received.recipient_id is None
        assert message_received.sender_id == 99  

    def test_deletes_status_history(self, user_bundle):
        service = user_bundle["service"]
        session = user_bundle["session"]
        notification_repository = user_bundle["notification_repository"]
        token_repository = user_bundle["token_repository"]

        user = _user(user_id=7)
        history = Mock()
        history.changed_by_id = 7

        self._setup_session_scalars(session, [], [], [], [history])
        notification_repository.list_for_user.return_value = []
        token_repository.list_for_user.return_value = []

        service.delete_account(user)

        assert history.changed_by_id is None

    def test_deletes_notifications_and_tokens(self, user_bundle):
        service = user_bundle["service"]
        session = user_bundle["session"]
        notification_repository = user_bundle["notification_repository"]
        token_repository = user_bundle["token_repository"]

        user = _user(user_id=9)
        notification = Mock()
        token = Mock()

        self._setup_session_scalars(session, [], [], [], [])
        notification_repository.list_for_user.return_value = [notification]
        token_repository.list_for_user.return_value = [token]

        service.delete_account(user)

        session.delete.assert_any_call(notification)
        session.delete.assert_any_call(token)

