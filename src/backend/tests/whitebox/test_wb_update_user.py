from __future__ import annotations

from unittest.mock import Mock

import pytest
from participium.models.category import Category
from participium.models.user import User
from participium.core.exceptions import NotFoundError, ValidationError
from participium.models.enums import Role
from participium.services.user_service import UserService


pytestmark = pytest.mark.whitebox


def _user(*,user_id: int = 1, username: str = "maria.rossi", first_name: str = "Maria", 
    last_name: str = "Rossi",
    email: str = "maria.rossi@example.com", 
    role: Role = Role.CITIZEN, 
    category_id: int | None = None, 
    is_active: bool = True,
    email_notifications_enabled: bool = True,
)-> User:
    return User(
        id = user_id,
        username = username,
        first_name = first_name,
        last_name = last_name,
        email = email,
        role = role,
        category_id = category_id,
        is_active = is_active,
        email_notifications_enabled = email_notifications_enabled,
    )


def _category(*, category_id: int, is_active: bool = True) -> Category:
    return Category(
        id = category_id,
        name = f"Category {category_id}",
        is_active = is_active
    )




@pytest.fixture
def service_bundle() -> dict[str, object]:
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


# TC-01: user not found
def test_update_user_not_found(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    user_repository = service_bundle["user_repository"]

    user_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.update_user(999, {})

#TC-02: username already in use
def test_update_user_username_already_in_use(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    user_repository = service_bundle["user_repository"]

    current_user = _user(user_id=1, username="old_username")
    existing_user = _user(user_id=2, username="existing_username")
    user_repository.get_by_id.return_value = current_user #the user we're trying to update
    user_repository.get_by_username.return_value = existing_user #there's already a user with that username
    with pytest.raises(ValidationError):
        service.update_user(1, {"username": "existing_username"})


#TC-03: email already in use
def test_update_user_email_already_in_use(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    user_repository = service_bundle["user_repository"]

    current_user = _user(user_id=1, email="old.user@example.com")       
    existing_user = _user(user_id=2, email="existing.user@example.com")
    user_repository.get_by_id.return_value = current_user   
    user_repository.get_by_email.return_value = existing_user  

    with pytest.raises(ValidationError):
        service.update_user(1, {"email": "existing.user@example.com"})


#TC-04: operator with invalid role
def test_update_user_operator_invalid_role(service_bundle: dict[str, object]) -> None:
    service = service_bundle["service"]
    user_repository = service_bundle["user_repository"]

    user_repository.get_by_id.return_value = _user()
    user_repository.get_by_username.return_value = None
    user_repository.get_by_email.return_value = None
    
    with pytest.raises(ValidationError):
        service.update_user(1,{"role": "superadmin"},)


# TC-05: operator without category
def test_update_user_operator_without_category(service_bundle: dict[str, object],) -> None:
    service = service_bundle["service"]
    user_repository = service_bundle["user_repository"]

    user_repository.get_by_id.return_value = _user()

    with pytest.raises(ValidationError):
        service.update_user(1,{"role": "operator","category_id": None,},)

# TC-05B: operator with non-integer category_id
def test_update_user_operator_invalid_category_id(service_bundle: dict[str, object],) -> None:
    service = service_bundle["service"]
    user_repository = service_bundle["user_repository"]

    user_repository.get_by_id.return_value = _user()

    with pytest.raises(ValidationError):
        service.update_user(1,{"role": "operator","category_id": "abc",},)



# TC-06: update base string fields
def test_update_user_string_fields(service_bundle: dict[str, object],) -> None:
    service = service_bundle["service"]
    session = service_bundle["session"]
    user_repository = service_bundle["user_repository"]

    user_repository.get_by_id.return_value = _user()
    user_repository.get_by_username.return_value = None
    user_repository.get_by_email.return_value = None

    result = service.update_user(1,{ "username": "giulia.verdi", "first_name": "Giulia", "last_name": "Verdi", "email": "giulia@example.com",},
    )

    assert result.username == "giulia.verdi"
    assert result.first_name == "Giulia"
    assert result.last_name == "Verdi"
    assert result.email == "giulia@example.com"

    session.commit.assert_called_once_with()


# TC-07: role becomes operator with valid category
def test_update_user_role_to_operator( service_bundle: dict[str, object],) -> None:
    service = service_bundle["service"]
    session = service_bundle["session"]
    user_repository = service_bundle["user_repository"]
    category_repository = service_bundle["category_repository"]

    user_repository.get_by_id.return_value = _user()
    category_repository.get_by_id.return_value = _category(category_id=3, is_active=True)

    result = service.update_user(1, {"role": "operator","category_id": 3},)

    assert result.role == Role.OPERATOR
    assert result.category_id == 3

    session.commit.assert_called_once_with()


# TC-07B: operator with inactive category
def test_update_user_operator_inactive_category(service_bundle: dict[str, object],) -> None:
    service = service_bundle["service"]
    user_repository = service_bundle["user_repository"]
    category_repository = service_bundle["category_repository"]

    user_repository.get_by_id.return_value = _user()

    category_repository.get_by_id.return_value = _category(category_id=99,is_active=False,)

    with pytest.raises(ValidationError):
        service.update_user(1,{"role": "operator","category_id": 99,},)


# TC-08: role changes from operator to citizen
def test_update_user_role_to_citizen_clears_category(service_bundle: dict[str, object],) -> None:
    service = service_bundle["service"]
    session = service_bundle["session"]
    user_repository = service_bundle["user_repository"]

    user = _user(role=Role.OPERATOR,category_id=3,)

    user_repository.get_by_id.return_value = user

    result = service.update_user(1,{"role": "citizen"},)

    assert result.role == Role.CITIZEN
    assert result.category_id is None

    session.commit.assert_called_once_with()


# TC-09: update boolean field
def test_update_user_bool_field(service_bundle: dict[str, object],) -> None:
    service = service_bundle["service"]
    session = service_bundle["session"]
    user_repository = service_bundle["user_repository"]

    user = _user()
    user_repository.get_by_id.return_value = user
    result = service.update_user(1,{"is_active": False},)

    assert result.is_active is False
    session.commit.assert_called_once_with()


# TC-10: empty payload
def test_update_user_empty_payload(service_bundle: dict[str, object],) -> None:
    service = service_bundle["service"]
    session = service_bundle["session"]
    user_repository = service_bundle["user_repository"]

    user = _user()

    user_repository.get_by_id.return_value = user

    result = service.update_user(1, {})

    assert result.username == user.username
    assert result.role == user.role

    session.commit.assert_called_once_with()


# TC-11: same username -> uniqueness check skipped
def test_update_user_same_username(service_bundle: dict[str, object],) -> None:
    service = service_bundle["service"]
    user_repository = service_bundle["user_repository"]

    user = _user()

    user_repository.get_by_id.return_value = user
    user_repository.get_by_username.return_value = None

    service.update_user(1,{"username": "maria.rossi"},)

    user_repository.get_by_username.assert_not_called()


# TC-12: same email -> uniqueness check skipped
def test_update_user_same_email(service_bundle: dict[str, object],) -> None:
    service = service_bundle["service"]
    user_repository = service_bundle["user_repository"]

    user = _user()

    user_repository.get_by_id.return_value = user
    user_repository.get_by_email.return_value = None

    service.update_user(1,{"email": "maria.rossi@example.com"},)

    user_repository.get_by_email.assert_not_called()



