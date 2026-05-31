from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from participium.core.security import hash_password
from participium.core.utils import utcnow
from participium.database import close_connection, create_all, get_session, open_connection
from participium.models.enums import Role
from participium.models.user import User
from participium.models.category import Category
from participium.models.token import EmailVerificationToken
from participium.models.report import Report
from participium.models.enums import Role, ReportStatus

@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    open_connection()
    create_all()
    session = get_session()
    yield session
    close_connection()

@pytest.fixture
def create_user():
    def _create(
        *,
        user_id: int | None = None,
        username: str = "maria.rossi",
        first_name: str = "Maria",
        last_name: str = "Rossi",
        email: str = "maria.rossi@example.com",
        password: str = "Password1!",
        role: Role = Role.CITIZEN,
        category_id: int | None = None,
        is_active: bool = True,
        is_email_verified: bool = True,
        email_notifications_enabled: bool = True,
    ) -> User:
        fields = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password_hash": hash_password(password),  
            "role": role,
            "category_id": category_id,
            "is_active": is_active,
            "is_email_verified": is_email_verified,
            "email_notifications_enabled": email_notifications_enabled,
        }
        if user_id is not None:
            fields["id"] = user_id
        return User(**fields)
    return _create

@pytest.fixture
def create_category():
    def _create(*, category_id: int, is_active: bool = True) -> Category:
        return Category(
            id=category_id,
            name=f"Category {category_id}",
            is_active=is_active
        )
    return _create

@pytest.fixture
def create_token():
    def _create(*, user_id: int, token: str, expires_at: datetime, is_used: bool = False) -> EmailVerificationToken:
        return EmailVerificationToken(user_id=user_id, token=token, expires_at=expires_at, is_used=is_used)
    return _create

def create_report(
    *,
    id: id = 10,
    title: str = "valid_title",
    description: str = "valid_description",
    latitude: float = 42.12,
    longitude: float = 9.34,
    is_anonymous: bool = False,
    status: ReportStatus = ReportStatus.PENDING_APPROVAL,
    reporter_id: int | None = 10,
    category_id: int = 10,
):
    return Report(
        id = id,
        title=title.strip(),
        description=description.strip(),
        latitude=latitude,
        longitude=longitude,
        is_anonymous=bool(is_anonymous),
        status=ReportStatus.PENDING_APPROVAL,
        reporter_id=reporter.id,
        category_id=category_id
    )

def user(
    *,
    user_id: int = 1,
    username: str = "maria.rossi",
    first_name: str = "Maria",
    last_name: str = "Rossi",
    email: str = "maria.rossi@example.com",
    password: str = "Password1!",
    role: Role = Role.CITIZEN,
    category_id: int | None = None,
    is_active: bool = True,
    is_email_verified: bool = True,
    email_notifications_enabled: bool = True,
) -> User:
    return User(
        id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        category_id=category_id,
        is_active=is_active,
        is_email_verified=is_email_verified,
        email_notifications_enabled=email_notifications_enabled,
    )

def category(*, category_id: int = 1, is_active: bool = True) -> Category:
    return Category(id=category_id, name=f"Category {category_id}", is_active=is_active)

def token(
    *,
    user_id: int = 1,
    token_str: str = "abc-token",
    is_used: bool = False,
    expired: bool = False,
) -> EmailVerificationToken:
    expires_at = utcnow() + (timedelta(hours=-1) if expired else timedelta(hours=48))
    tok = EmailVerificationToken(
        user_id=user_id,
        token=token_str,
        expires_at=expires_at,
        is_used=is_used,
    )
    tok.user = user(user_id=user_id, is_email_verified=False)
    return tok



@pytest.fixture
def user_payload():
    return {
        "username": "new.user",
        "first_name": "New",
        "last_name": "User",
        "email": "New.User@Example.com",
        "password": "Password1!",
        "role": "citizen",
    }



