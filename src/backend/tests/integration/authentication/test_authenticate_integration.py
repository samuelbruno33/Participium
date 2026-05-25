from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
import pytest

from participium.core.exceptions import ValidationError, AuthenticationError
from participium.models.user import User
from participium.repositories.token_repository import TokenRepository
from participium.repositories.user_repository import UserRepository
from participium.services.auth_service import AuthService

pytestmark = pytest.mark.integration


#we're testing auth+db+repo not sending email 
@pytest.fixture
def auth_service(db):
    email_gateway = Mock()
    return AuthService(
        session=db,
        user_repository=UserRepository(db),
        token_repository=TokenRepository(db),
        email_gateway=email_gateway,
    ), db, email_gateway

def test_user_repository_get_by_username_or_email_returns_user(db, create_user):
    repo = UserRepository(db)
    user = create_user()
    db.add(user)
    db.commit()

    assert repo.get_by_username_or_email(user.username).id == user.id
    assert repo.get_by_username_or_email(user.email).id == user.id


def test_token_repository_persists_token_and_lists_for_user(db, create_user, create_token):
    token_repo = TokenRepository(db)
    user = create_user()
    db.add(user)
    db.commit()

    token = create_token(user_id=user.id, token="token1", expires_at=datetime.now(UTC) + timedelta(hours=24))
    token_repo.add(token)
    db.commit()

    assert token_repo.get_by_token("token1").id == token.id
    tokens = token_repo.list_for_user(user.id)
    assert len(tokens) == 1


def test_register_user_creates_user_and_token(auth_service) -> None:
    svc, db, email_gateway = auth_service
    payload = {
        "username": "new.user",
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@example.com",
        "password": "Password1!",
    }

    user, verification_url = svc.register_user(payload, verification_base_url="http://localhost/verifytoken")

    assert user.id is not None
    assert user.email == "new.user@example.com"
    assert verification_url is not None

    saved_user = UserRepository(db).get_by_email(user.email)
    assert saved_user is not None
    assert saved_user.is_email_verified is False
    assert email_gateway.send.called

    token = TokenRepository(db).get_by_token(verification_url.rsplit("/", 1)[-1])
    assert token is not None
    assert token.user_id == user.id


def test_verify_email_marks_user_as_verified(auth_service, create_user, create_token) -> None:
    service, db, _ = auth_service
    user = create_user(is_email_verified=False)
    db.add(user)
    db.commit()

    token = create_token(user_id=user.id, token="verify-token", expires_at=datetime.now() + timedelta(hours=24))
    db.add(token)
    db.commit()

    verified_user = service.verify_email("verify-token")
    assert verified_user.is_email_verified is True


def test_verify_email_invalid_token(auth_service) -> None:
    service, _, _ = auth_service
    with pytest.raises(ValidationError, match="invalid"):
        service.verify_email("missing-token")


def test_authenticate_success_username(auth_service, create_user) -> None:
    service, db, _ = auth_service
    user = create_user(password="Password1!")
    db.add(user)
    db.commit()    
    result = service.authenticate(user.username, "Password1!")
    assert isinstance(result, User)
    assert result.id == user.id


def test_authenticate_success_email(auth_service, create_user) -> None:
    service, db, _ = auth_service
    user = create_user(password="Password1!")
    db.add(user)
    db.commit()    
    result = service.authenticate(user.email, "Password1!")
    assert isinstance(result, User)
    assert result.id == user.id


def test_authenticate_wrong_password(auth_service, create_user) -> None:
    service, db, _ = auth_service
    user = create_user(password="Password1!")
    db.add(user)
    db.commit()    
    with pytest.raises(AuthenticationError):
        service.authenticate(user.username, "WrongPassword1!")


def test_authenticate_unknown_user(auth_service) -> None:
    svc, _, _ = auth_service
    with pytest.raises(AuthenticationError):
        svc.authenticate("non_existent_user@example.com", "Password1!")


def test_authenticate_inactive_user(auth_service, create_user) -> None:
    svc, db, _ = auth_service
    user = create_user(is_active=False, password="Password1!")
    db.add(user)
    db.commit()

    with pytest.raises(AuthenticationError):
        svc.authenticate(user.username, "Password1!")


def test_authenticate_unverified_email(auth_service, create_user) -> None:
    svc, db, _ = auth_service
    user = create_user(is_email_verified=False, password="Password1!")
    db.add(user)
    db.commit()

    with pytest.raises(AuthenticationError):
        svc.authenticate(user.username, "Password1!")