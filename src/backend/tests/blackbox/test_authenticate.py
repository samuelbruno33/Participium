from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.services.auth_service import AuthService
from participium.core.exceptions import AuthenticationError
from participium.models.user import User
from participium.core.security import hash_password


@pytest.fixture
def auth_service():
    session = Mock()
    user_repository = Mock()
    token_repository = Mock()
    email_gateway = Mock()
    service = AuthService(session, user_repository, token_repository, email_gateway)
    return service, user_repository


@pytest.fixture
def active_user():
    password = "CorrectPassword1!"
    user = User(
        id=1,
        username="maria.rossi",
        first_name="Maria",
        last_name="Rossi",
        email="maria.rossi@example.com",
        password_hash=hash_password(password),
        is_active=True,
        is_email_verified=True,
    )
    return user, password


@pytest.fixture
def inactive_user():
    password = "CorrectPassword1!"
    user = User(
        id=2,
        username="luca.bianchi",
        first_name="Luca",
        last_name="Bianchi",
        email="luca.bianchi@example.com",
        password_hash=hash_password(password),
        is_active=False,
        is_email_verified=True,
    )
    return user, password


@pytest.fixture
def active_unverified_user():
    password = "CorrectPassword1!"
    user = User(
        id=3,
        username="giulia.verdi",
        first_name="Giulia",
        last_name="Verdi",
        email="giulia.verdi@example.com",
        password_hash=hash_password(password),
        is_active=True,
        is_email_verified=False,
    )
    return user, password


@pytest.fixture
def active_user_wrong_hash():
    password = "CorrectPassword1!"
    user = User(
        id=4,
        username="mario.neri",
        first_name="Mario",
        last_name="Neri",
        email="mario.neri@example.com",
        password_hash=hash_password("WrongPassword1!"),
        is_active=True,
        is_email_verified=True,
    )
    return user, password


def test_authenticate_success_username(auth_service, active_user) -> None:
    service, user_repo = auth_service
    user, password = active_user
    user_repo.get_by_username_or_email.return_value = user

    result = service.authenticate(user.username, password)

    assert isinstance(result, User)
    assert result.id == user.id
    assert result.username == user.username
    assert result.first_name == user.first_name
    assert result.last_name == user.last_name
    assert result.email == user.email
    assert result.is_active is True


def test_authenticate_success_email(auth_service, active_user) -> None:
    service, user_repo = auth_service
    user, password = active_user
    user_repo.get_by_username_or_email.return_value = user

    result = service.authenticate(user.email, password)

    assert isinstance(result, User)
    assert result.id == user.id
    assert result.username == user.username
    assert result.first_name == user.first_name
    assert result.last_name == user.last_name
    assert result.email == user.email
    assert result.is_active is True


def test_authenticate_wrong_password(auth_service, active_user) -> None:
    service, user_repo = auth_service
    user, _ = active_user
    user_repo.get_by_username_or_email.return_value = user

    with pytest.raises(AuthenticationError):
        service.authenticate(user.username, "WrongPassword")


def test_authenticate_nonexistent_user(auth_service, active_user) -> None:
    service, user_repo = auth_service
    user, password = active_user
    user_repo.get_by_username_or_email.return_value = None

    with pytest.raises(AuthenticationError):
        service.authenticate(user.username, password)


def test_authenticate_inactive_user(auth_service, inactive_user) -> None:
    service, user_repo = auth_service
    user, password = inactive_user
    user_repo.get_by_username_or_email.return_value = user

    with pytest.raises(AuthenticationError):
        service.authenticate(user.username, password)


def test_authenticate_unverified_email(auth_service, active_unverified_user) -> None:
    service, user_repo = auth_service
    user, password = active_unverified_user
    user_repo.get_by_username_or_email.return_value = user

    with pytest.raises(AuthenticationError):
        service.authenticate(user.username, password)


def test_authenticate_empty_identifier(auth_service, active_user) -> None:
    service, user_repo = auth_service
    user, password = active_user
    user_repo.get_by_username_or_email.return_value = None

    with pytest.raises(AuthenticationError):
        service.authenticate("", password)


def test_authenticate_empty_password(auth_service, active_user) -> None:
    service, user_repo = auth_service
    user, _ = active_user
    user_repo.get_by_username_or_email.return_value = user

    with pytest.raises(AuthenticationError):
        service.authenticate(user.username, "")


def test_authenticate_none_identifier(auth_service, active_user) -> None:
    service, _ = auth_service
    user, password = active_user

    with pytest.raises(AttributeError):
        service.authenticate(None, password)


def test_authenticate_none_password(auth_service, active_user) -> None:
    service, user_repo = auth_service
    user, _ = active_user
    user_repo.get_by_username_or_email.return_value = user

    with pytest.raises(AttributeError):
        service.authenticate(user.username, None)


def test_authenticate_whitespace_identifier(auth_service, active_user) -> None:
    service, user_repo = auth_service
    user, password = active_user
    user_repo.get_by_username_or_email.return_value = None

    with pytest.raises(AuthenticationError):
        service.authenticate("   ", password)


def test_authenticate_wrong_hash(auth_service, active_user_wrong_hash) -> None:
    service, user_repo = auth_service
    user, password = active_user_wrong_hash
    user_repo.get_by_username_or_email.return_value = user

    with pytest.raises(AuthenticationError):
        service.authenticate(user.username, password)