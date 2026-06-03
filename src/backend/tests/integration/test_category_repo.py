from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import scoped_session, sessionmaker

from participium.models.base import Base
from participium.models.category import Category
from participium.repositories.category_repository import CategoryRepository


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def db_engine():
    """Create a module-scoped in-memory SQLite engine with the project schema."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Per-test session bound to a transaction that is rolled back at teardown.

    Each test sees an empty `categories` table, which keeps test order irrelevant
    and avoids cross-contamination from previously inserted rows.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def category_repo(db_session):
    return CategoryRepository(db_session)


def _persist(repo: CategoryRepository, session, *categories: Category) -> list[Category]:
    for category in categories:
        repo.add(category)
    session.commit()
    return list(categories)


class TestAddAndGetById:
    def test_add_assigns_id_after_commit(self, category_repo, db_session) -> None:
        category = Category(name="Roads", is_active=True)

        returned = category_repo.add(category)
        db_session.commit()

        assert returned is category
        assert category.id is not None

    def test_get_by_id_returns_persisted_category(self, category_repo, db_session) -> None:
        [stored] = _persist(category_repo, db_session, Category(name="Waste", is_active=True))

        fetched = category_repo.get_by_id(stored.id)

        assert fetched is not None
        assert fetched.id == stored.id
        assert fetched.name == "Waste"
        assert fetched.is_active is True

    def test_get_by_id_missing_returns_none(self, category_repo) -> None:
        assert category_repo.get_by_id(999) is None


class TestGetByName:
    def test_returns_matching_category(self, category_repo, db_session) -> None:
        _persist(category_repo, db_session, Category(name="Lighting", is_active=True))

        fetched = category_repo.get_by_name("Lighting")

        assert fetched is not None
        assert fetched.name == "Lighting"

    def test_returns_none_when_name_not_found(self, category_repo) -> None:
        assert category_repo.get_by_name("Nonexistent") is None

    def test_lookup_is_case_sensitive(self, category_repo, db_session) -> None:
        # Documents the current behavior: name matching uses the database's
        # default collation, which on SQLite is case-sensitive for == comparisons.
        _persist(category_repo, db_session, Category(name="Sewerage", is_active=True))

        assert category_repo.get_by_name("Sewerage") is not None
        assert category_repo.get_by_name("sewerage") is None


class TestListAll:
    def test_returns_empty_list_when_no_categories(self, category_repo) -> None:
        assert category_repo.list_all() == []

    def test_returns_all_categories_ordered_by_name(self, category_repo, db_session) -> None:
        _persist(
            category_repo,
            db_session,
            Category(name="Waste", is_active=True),
            Category(name="Architectural Barriers", is_active=True),
            Category(name="Roads", is_active=False),
        )

        names = [c.name for c in category_repo.list_all()]

        assert names == ["Architectural Barriers", "Roads", "Waste"]

    def test_active_only_excludes_inactive(self, category_repo, db_session) -> None:
        _persist(
            category_repo,
            db_session,
            Category(name="Active A", is_active=True),
            Category(name="Inactive B", is_active=False),
            Category(name="Active C", is_active=True),
        )

        names = [c.name for c in category_repo.list_all(active_only=True)]

        assert names == ["Active A", "Active C"]

    def test_active_only_false_includes_all(self, category_repo, db_session) -> None:
        _persist(
            category_repo,
            db_session,
            Category(name="A", is_active=True),
            Category(name="B", is_active=False),
        )

        result = category_repo.list_all(active_only=False)

        assert len(result) == 2
        assert {c.name for c in result} == {"A", "B"}

    def test_active_only_returns_empty_when_all_inactive(
        self, category_repo, db_session
    ) -> None:
        _persist(
            category_repo,
            db_session,
            Category(name="X", is_active=False),
            Category(name="Y", is_active=False),
        )

        assert category_repo.list_all(active_only=True) == []


class TestUniqueNameConstraint:
    def test_duplicate_name_violates_unique_constraint(
        self, category_repo, db_session
    ) -> None:
        # The Category model declares `name` as unique. Attempting to commit
        # two rows with the same name must raise an IntegrityError.
        _persist(category_repo, db_session, Category(name="Duplicate", is_active=True))

        category_repo.add(Category(name="Duplicate", is_active=True))

        with pytest.raises(IntegrityError):
            db_session.commit()
