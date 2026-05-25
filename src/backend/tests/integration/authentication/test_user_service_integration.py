from __future__ import annotations

import pytest
from participium.core.exceptions import NotFoundError, ValidationError
from participium.models.enums import Role
from participium.repositories.user_repository import UserRepository
from participium.repositories.category_repository import CategoryRepository
from participium.services.user_service import UserService

pytestmark = pytest.mark.integration

@pytest.fixture
def service(db):
    user_repository = UserRepository(db)
    category_repository = CategoryRepository(db)
    return UserService(
        session=db,
        user_repository=user_repository,
        category_repository=category_repository,
    ), db


def test_update_user_persists_changes_db(service, create_user) -> None:
    user_service, db = service
    user = create_user()
    db.add(user)
    db.commit()

    result = user_service.update_user(user.id, {
        "username": "giulia.verdi",
        "first_name": "Giulia",
        "last_name": "Verdi",
        "email": "giulia.verdi@example.com",
    })

    assert result.username == "giulia.verdi"
    assert result.first_name == "Giulia"    
    assert result.last_name == "Verdi"
    assert result.email == "giulia.verdi@example.com"

    user_from_db = UserRepository(db).get_by_id(user.id)
    assert user_from_db is not None
    assert user_from_db.username == "giulia.verdi"
    assert user_from_db.first_name == "Giulia"
    assert user_from_db.last_name == "Verdi"
    assert user_from_db.email == "giulia.verdi@example.com"

def test_update_user_not_found(service) -> None:
    user_service, _ = service
    with pytest.raises(NotFoundError):
        user_service.update_user(999, {})


def test_update_user_username_conflict(service, create_user) -> None:
    user_service, db = service
    user1 = create_user(user_id=1, username="maria.rossi")
    user2 = create_user(user_id=2, username="giulia.verdi", email="giulia.verdi@example.com")
    
    db.add_all([user1, user2])
    db.commit()

    with pytest.raises(ValidationError):
        user_service.update_user(user1.id, {"username": "giulia.verdi"})



def test_update_user_raises_on_email_conflict(service, create_user) -> None:
    svc, db = service
    user1 = create_user(user_id=1, username="maria.rossi", email="maria.rossi@example.com")
    user2 = create_user(user_id=2, username="mario.rossi", email="mario.rossi@example.com")
    db.add_all([user1, user2])
    db.commit()

    with pytest.raises(ValidationError):
        svc.update_user(user1.id, {"email": "mario.rossi@example.com"})


def test_update_user_role_to_operator_without_category(service, create_user, create_category) -> None:
    user_service, db = service
    category = create_category(category_id=1, is_active=True)
    user = create_user(user_id=1)    
    db.add(category)
    db.add(user)
    db.commit()

    result = user_service.update_user(user.id, {"role": "operator", "category_id": category.id})

    assert result.role == Role.OPERATOR
    assert result.category_id == category.id


def test_update_user_operator_invalid_category_id(service, create_user, create_category) -> None:
    user_service, db = service
    user = create_user()
    category = create_category(category_id=999) 
    db.add(category)
    db.add(user)
    db.commit() 
    with pytest.raises(ValidationError):
        user_service.update_user(user.id, {"role": "operator", "category_id": "abc"})


def test_update_user_operator_inactive_category(service, create_user, create_category) -> None:
    user_service, db = service
    category = create_category(category_id=1, is_active=False)
    user = create_user()
    db.add(category)
    db.add(user)
    db.commit()

    with pytest.raises(ValidationError):
        user_service.update_user(user.id, {"role": "operator", "category_id": category.id})


def test_update_user_same_username_or_email_no_conflict(service, create_user) -> None:
    user_service, db = service
    user = create_user(username="maria.rossi", email="maria.rossi@example.com")
    db.add(user)
    db.commit()

    result_user = user_service.update_user(user.id, {"username": "maria.rossi", "email": "maria.rossi@example.com"})
    assert result_user.username == "maria.rossi"
    assert result_user.email == "maria.rossi@example.com"



def test_update_user_empty_payload(service, create_user) -> None:
    user_service, db = service
    user = create_user()
    db.add(user)
    db.commit()

    user_service.update_user(user.id, {})
    user_from_db = UserRepository(db).get_by_id(user.id)

    assert user_from_db.username == user.username


def test_create_then_update_user_flow(service, create_user) -> None:
    user_service, db = service
    user = create_user(username="created_user", email="created_user@example.com")
    db.add(user)
    db.commit()

    updated = user_service.update_user(user.id, {"username": "updated_user", "email": "updated_user@example.com", "is_active": False})
    assert updated.username == "updated_user"
    assert updated.is_active is False