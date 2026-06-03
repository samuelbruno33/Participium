from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.routes.api import _as_bool
from participium.core.exceptions import DomainError
from participium.core.exceptions import AuthenticationError, ValidationError
from participium.core.security import verify_password
from participium.models.enums import Role
from participium.services.user_service import UserService
from participium.services.auth_service import AuthService
from tests.conftest import user as _user, token as _token


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


@pytest.fixture
def auth_bundle():
    session = Mock()
    user_repository = Mock()
    token_repository = Mock()
    email_gateway = Mock()
    service = AuthService(
        session=session,
        user_repository=user_repository,
        token_repository=token_repository,
        email_gateway=email_gateway,
    )
    return {
        "service": service,
        "session": session,
        "user_repository": user_repository,
        "token_repository": token_repository,
        "email_gateway": email_gateway,
    }


class TestRegisterUser:

    def test_registers_successfully_without_url(self, auth_bundle, user_payload):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        token_repository = auth_bundle["token_repository"]
        session = auth_bundle["session"]

        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        user, url = service.register_user(user_payload)

        assert user.username == "new.user"
        assert user.is_email_verified is False
        assert user.role == Role.CITIZEN
        assert url is None
        user_repository.add.assert_called_once()
        token_repository.add.assert_called_once()
        session.commit.assert_called_once()

    def test_sends_email_and_returns_url_when_base_url_given(self, auth_bundle, user_payload):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        email_gateway = auth_bundle["email_gateway"]

        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        user, url = service.register_user(user_payload, verification_base_url="https://app.com/verify")

        assert url is not None
        assert url.startswith("https://app.com/verify/")
        email_gateway.send.assert_called_once()
        sent_fields = email_gateway.send.call_args[1]
        assert sent_fields["recipient"] == user.email
        assert url in sent_fields["body"]

    def test_raises_on_missing_fields(self, auth_bundle):
        service = auth_bundle["service"]
        with pytest.raises(ValidationError, match="Missing required fields"):
            service.register_user({"username": "only"})

    def test_raises_on_duplicate_username(self, auth_bundle, user_payload):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        user_repository.get_by_username.return_value = _user()

        with pytest.raises(ValidationError, match="Username already in use"):
            service.register_user(user_payload)

    def test_raises_on_duplicate_email(self, auth_bundle, user_payload):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = _user()

        with pytest.raises(ValidationError, match="Email already in use"):
            service.register_user(user_payload)

    def test_email_is_lowercased(self, auth_bundle, user_payload):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        user, _ = service.register_user(user_payload)
        assert user.email == "new.user@example.com"

    def test_no_email_sent_without_base_url(self, auth_bundle, user_payload):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        email_gateway = auth_bundle["email_gateway"]
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        service.register_user(user_payload)
        email_gateway.send.assert_not_called()



    def test_password_is_hashed(self, auth_bundle, user_payload):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        user_repository.get_by_username.return_value = None
        user_repository.get_by_email.return_value = None

        user, _ = service.register_user(user_payload)
        assert user.password_hash != user_payload["password"]
        assert verify_password(user_payload["password"], user.password_hash)


class TestVerifyEmail:
    def test_verifies_valid_token(self, auth_bundle):
        service = auth_bundle["service"]
        token_repository = auth_bundle["token_repository"]
        session = auth_bundle["session"]

        tok = _token()
        token_repository.get_by_token.return_value = tok

        result = service.verify_email("token1")

        assert result.is_email_verified is True
        assert tok.is_used is True
        session.commit.assert_called_once()

    def test_with_non_nonexistent_token(self, auth_bundle):
        service = auth_bundle["service"]
        token_repository = auth_bundle["token_repository"]
        token_repository.get_by_token.return_value = None

        with pytest.raises(ValidationError, match="invalid"):
            service.verify_email("non-existent-token")

    def test_with_already_used_token(self, auth_bundle):
        service = auth_bundle["service"]
        token_repository = auth_bundle["token_repository"]
        token_repository.get_by_token.return_value = _token(is_used=True)

        with pytest.raises(ValidationError, match="invalid"):
            service.verify_email("token1")

    def test_with_expired_token(self, auth_bundle):
        service = auth_bundle["service"]
        token_repository = auth_bundle["token_repository"]
        token_repository.get_by_token.return_value = _token(expired=True)

        with pytest.raises(ValidationError, match="expired"):
            service.verify_email("abc-token")

    def test_does_not_commit_on_invalid_token(self, auth_bundle):
        service = auth_bundle["service"]
        token_repository = auth_bundle["token_repository"]
        session = auth_bundle["session"]
        token_repository.get_by_token.return_value = None

        with pytest.raises(ValidationError):
            service.verify_email("bad-token")

        session.commit.assert_not_called()


class TestAuthenticate:
    def test_authenticates_with_username(self, auth_bundle):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        user = _user(password="Password1!")
        user_repository.get_by_username_or_email.return_value = user

        result = service.authenticate(user.username, "Password1!")

        assert result is user

    def test_authenticates_with_email(self, auth_bundle):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        user = _user(password="Password1!")
        user_repository.get_by_username_or_email.return_value = user

        result = service.authenticate(user.email, "Password1!")

        assert result is user

    def test_authenticates_with_invalid_password(self, auth_bundle):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        user = _user(password="Password1!")
        user_repository.get_by_username_or_email.return_value = user

        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            service.authenticate(user.username, "WrongPassword1!")

    def test_unknown_user(self, auth_bundle):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        user_repository.get_by_username_or_email.return_value = None

        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            service.authenticate("unknown.user", "Password1!")

    def test_inactive_user(self, auth_bundle):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        user = _user(is_active=False, password="Password1!")
        user_repository.get_by_username_or_email.return_value = user

        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            service.authenticate(user.username, "Password1!")

    def test_unverified_email(self, auth_bundle):
        service = auth_bundle["service"]
        user_repository = auth_bundle["user_repository"]
        user = _user(is_email_verified=False, password="Password1!")
        user_repository.get_by_username_or_email.return_value = user

        with pytest.raises(AuthenticationError, match="Email verification is required"):
            service.authenticate(user.username, "Password1!")



def test_domain_error_custom_status_code():
    err = DomainError("something went wrong", status_code=422)
    assert err.status_code == 422
    assert str(err) == "something went wrong"


        
def test_as_bool_parses_truthy_and_falsey_values():

    assert _as_bool("true") is True
    assert _as_bool("on") is True
    assert _as_bool("false") is False
    assert _as_bool(None, default=True) is True