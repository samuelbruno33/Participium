from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.core.exceptions import NotFoundError, ValidationError
from participium.models.category import Category
from participium.services.category_service import CategoryService


pytestmark = pytest.mark.unit


@pytest.fixture
def service_bundle() -> dict[str, object]:
    """Build a CategoryService with mocked session and repository."""
    session = Mock()
    repository = Mock()
    service = CategoryService(session=session, category_repository=repository)
    return {"service": service, "session": session, "repository": repository}


def _category(category_id: int = 1, name: str = "Roads", is_active: bool = True) -> Category:
    return Category(id=category_id, name=name, is_active=is_active)


class TestListCategories:
    """list_categories simply forwards to the repository."""

    def test_list_default_forwards_active_only_false(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        expected = [_category(1, "A"), _category(2, "B")]
        repository.list_all.return_value = expected

        result = service.list_categories()

        assert result is expected
        repository.list_all.assert_called_once_with(active_only=False)

    def test_list_active_only_true_is_forwarded(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        repository.list_all.return_value = []

        result = service.list_categories(active_only=True)

        assert result == []
        repository.list_all.assert_called_once_with(active_only=True)

    def test_list_empty_repository_returns_empty_list(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        repository.list_all.return_value = []

        assert service.list_categories(active_only=False) == []


class TestGetCategory:
    """get_category returns the entity or raises NotFoundError."""

    def test_get_existing_returns_category(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        category = _category(7, "Lighting")
        repository.get_by_id.return_value = category

        assert service.get_category(7) is category
        repository.get_by_id.assert_called_once_with(7)

    def test_get_missing_raises_not_found(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Category not found."):
            service.get_category(404)


class TestCreateCategory:
    """create_category validates the name and persists a new active category."""

    def test_create_success_persists_and_commits(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]
        repository.get_by_name.return_value = None
        repository.add.side_effect = lambda c: c

        result = service.create_category("Waste")

        assert isinstance(result, Category)
        assert result.name == "Waste"
        assert result.is_active is True
        repository.get_by_name.assert_called_once_with("Waste")
        repository.add.assert_called_once()
        session.commit.assert_called_once()

    def test_create_trims_surrounding_whitespace(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        repository.get_by_name.return_value = None
        repository.add.side_effect = lambda c: c

        result = service.create_category("  Sewerage  ")

        assert result.name == "Sewerage"
        repository.get_by_name.assert_called_once_with("Sewerage")

    @pytest.mark.parametrize("name", ["", "   ", "\t\n"])
    def test_create_rejects_blank_name(self, service_bundle, name: str) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]

        with pytest.raises(ValidationError, match="Category name is required."):
            service.create_category(name)

        repository.get_by_name.assert_not_called()
        repository.add.assert_not_called()
        session.commit.assert_not_called()

    def test_create_rejects_duplicate_name(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]
        repository.get_by_name.return_value = _category(1, "Waste")

        with pytest.raises(ValidationError, match="Category name already exists."):
            service.create_category("Waste")

        repository.add.assert_not_called()
        session.commit.assert_not_called()


class TestUpdateCategory:
    """update_category supports renaming and (de)activating with uniqueness checks."""

    def test_update_name_only(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]
        category = _category(1, "Old Name", is_active=True)
        repository.get_by_id.return_value = category
        repository.get_by_name.return_value = None

        result = service.update_category(1, name="New Name")

        assert result is category
        assert category.name == "New Name"
        assert category.is_active is True
        session.commit.assert_called_once()

    def test_update_trims_new_name(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        category = _category(1, "Old", is_active=True)
        repository.get_by_id.return_value = category
        repository.get_by_name.return_value = None

        service.update_category(1, name="  Trimmed  ")

        assert category.name == "Trimmed"
        repository.get_by_name.assert_called_once_with("Trimmed")

    def test_update_is_active_only(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]
        category = _category(1, "Roads", is_active=True)
        repository.get_by_id.return_value = category

        result = service.update_category(1, is_active=False)

        assert result is category
        assert category.is_active is False
        assert category.name == "Roads"
        repository.get_by_name.assert_not_called()
        session.commit.assert_called_once()

    def test_update_can_reactivate(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        category = _category(1, "Roads", is_active=False)
        repository.get_by_id.return_value = category

        service.update_category(1, is_active=True)

        assert category.is_active is True

    def test_update_both_fields(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]
        category = _category(1, "Old", is_active=True)
        repository.get_by_id.return_value = category
        repository.get_by_name.return_value = None

        service.update_category(1, name="New", is_active=False)

        assert category.name == "New"
        assert category.is_active is False
        session.commit.assert_called_once()

    def test_update_rename_to_same_name_on_same_category_is_allowed(
        self, service_bundle
    ) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        category = _category(1, "Roads", is_active=True)
        repository.get_by_id.return_value = category
        # get_by_name returns the same entity (same id) -> not a duplicate
        repository.get_by_name.return_value = category

        result = service.update_category(1, name="Roads")

        assert result is category
        assert category.name == "Roads"

    def test_update_rename_to_existing_other_category_is_rejected(
        self, service_bundle
    ) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]
        category = _category(1, "Roads", is_active=True)
        other = _category(2, "Waste", is_active=True)
        repository.get_by_id.return_value = category
        repository.get_by_name.return_value = other

        with pytest.raises(ValidationError, match="Category name already exists."):
            service.update_category(1, name="Waste")

        assert category.name == "Roads"
        session.commit.assert_not_called()

    def test_update_missing_category_raises_not_found(self, service_bundle) -> None:
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]
        repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Category not found."):
            service.update_category(999, name="Whatever")

        session.commit.assert_not_called()

    def test_update_with_no_changes_still_commits(self, service_bundle) -> None:
        # Calling update with both None still triggers commit (no changes applied).
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        session = service_bundle["session"]
        category = _category(1, "Roads", is_active=True)
        repository.get_by_id.return_value = category

        result = service.update_category(1)

        assert result is category
        assert category.name == "Roads"
        assert category.is_active is True
        repository.get_by_name.assert_not_called()
        session.commit.assert_called_once()

    def test_update_empty_name_is_ignored(self, service_bundle) -> None:
        # name="" is falsy -> name branch is skipped, no rename, no uniqueness check.
        service = service_bundle["service"]
        repository = service_bundle["repository"]
        category = _category(1, "Roads", is_active=True)
        repository.get_by_id.return_value = category

        service.update_category(1, name="")

        assert category.name == "Roads"
        repository.get_by_name.assert_not_called()
