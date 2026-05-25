from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.core import ValidationError
from werkzeug.datastructures import FileStorage
from participium.models.category import Category
from participium.models.report import Report
from participium.models.enums import ReportStatus
from participium.services.report_service import ReportService


pytestmark = pytest.mark.whitebox

# Structural tests for ReportService.create_report belong here.
# The current runnable smoke check is kept in test_wb_task06_smoke.py.

@pytest.fixture
def mock_service():
    session = Mock()
    report_repository = Mock()
    storage_service = Mock()
    notification_service = Mock()

    def get_category(id):
        if id in (10, 11):
            category = Mock( spec = Category )
            category.id = id
            category.is_active = (id == 10)
            return category

        return None
    category_repository = Mock()
    category_repository.get_by_id.side_effect = get_category

    service = ReportService(
        session,
        report_repository,
        category_repository,
        storage_service,
        notification_service
    )
    return service, report_repository

def photos_1_valid_1_none():
    one = Mock( spec = FileStorage, filename = "valid/path/one" )
    return [one, None]

def photos_1_invalid():
    one = Mock( spec = FileStorage, filename = None )
    return [one]

def photos_4_valid():
    one = Mock( spec = FileStorage, filename = "valid/path/one" )
    two = Mock( spec = FileStorage, filename = "valid/path/two" )
    three = Mock( spec = FileStorage, filename = "valid/path/three" )
    four = Mock( spec = FileStorage, filename = "valid/path/four" )
    return [one, two, three, four]

def photos_empty():
    return []

def photos_3_valid():
    one = Mock( spec = FileStorage, filename = "valid/path/one" )
    two = Mock( spec = FileStorage, filename = "valid/path/two" )
    three = Mock( spec = FileStorage, filename = "valid/path/three" )
    return [one, two, three]


@pytest.mark.parametrize(
    "reporter, category_id, title, description, latitude, longitude, photos, is_anonymous, expected_exception, oracle",
    [
        (Mock(), None, "valid title", "valid description", 40.12, 9.34, photos_1_valid_1_none(), True, ValidationError, None), #TC-01
        (Mock(), "invalid: not an int", "valid title", "valid description", 40.12, 9.34, photos_1_valid_1_none(), True, ValidationError, None), #TC-02
        (Mock(), 10, None, None, 40.12, 9.34, photos_1_valid_1_none(), True, ValidationError, None), #TC-03
        (Mock(), 10, "valid title", "valid description", None, None, photos_1_valid_1_none(), True, ValidationError, None), #TC-04
        (Mock(), 10, "valid title", "valid description", "invalid: not a float", "invalid: not a float", photos_1_valid_1_none(), True, ValidationError, None), #TC-05
        (Mock(), 10, "valid title", "valid description", 40.12, 9.34, photos_1_invalid(), True, ValidationError, None), #TC-06
        (Mock(), 10, "valid title", "valid description", 40.12, 9.34, photos_4_valid(), True, ValidationError, None), #TC-07
        (Mock(), 10, "valid title", "valid description", 40.12, 9.34, photos_1_valid_1_none(), True, None, Report), #TC-08
        (Mock(), 11, "valid title", "valid description", 40.12, 9.34, photos_1_valid_1_none(), True, ValidationError, None), #TC-09
        (Mock(), 10, None, "valid description", 40.12, 9.34, photos_1_valid_1_none(), True, ValidationError, None), #TC-10
        (Mock(), 10, "valid title", None, 40.12, 9.34, photos_1_valid_1_none(), True, ValidationError, None), #TC-11
        (Mock(), 10, "valid title", "valid description", None, 9.34, photos_1_valid_1_none(), True, ValidationError, None), #TC-12
        (Mock(), 10, "valid title", "valid description", 40.12, None, photos_1_valid_1_none(), True, ValidationError, None), #TC-13
        (Mock(), 10, "valid title", "valid description", "invalid: not a float", 9.34, photos_1_valid_1_none(), True, ValidationError, None), #TC-14
        (Mock(), 10, "valid title", "valid description", 40.12, "invalid: not a float", photos_1_valid_1_none(), True, ValidationError, None), #TC-15
        (Mock(), 10, "valid title", "valid description", 40.12, 9.34, photos_empty(), True, ValidationError, None), #TC-16
        (Mock(), 10, "valid title", "valid description", 40.12, 9.34, photos_3_valid(), True, None, Report), #TC-17
    ]
)
def test_suite_create_report(mock_service, reporter, category_id, title, description, latitude, longitude, photos, is_anonymous, expected_exception, oracle):
    service, repo = mock_service
    if expected_exception:
        with pytest.raises(expected_exception):
            service.create_report(reporter, category_id, title, description, latitude, longitude, photos, is_anonymous)
    else:
        repo.get_by_id.return_value = Report(
            title=title.strip(),
            description=description.strip(),
            latitude=latitude,
            longitude=longitude,
            is_anonymous=bool(is_anonymous),
            status=ReportStatus.PENDING_APPROVAL,
            reporter_id=reporter.id,
            category_id=category_id
        )
        result = service.create_report(reporter, category_id, title, description, latitude, longitude, photos, is_anonymous)
        
        assert isinstance(result, oracle)
        assert result.title == title.strip()
        assert result.description == description.strip()
        assert result.latitude == latitude
        assert result.longitude == longitude
        assert result.is_anonymous == bool(is_anonymous)
        assert result.status == ReportStatus.PENDING_APPROVAL
        assert result.reporter_id == reporter.id
        assert result.category_id == category_id
        service.report_repository.add.assert_called_once()
        service.session.flush.assert_called_once()
        service.report_repository.add_status_entry.assert_called_once()
        service.session.commit.assert_called_once()
        service.report_repository.get_by_id.assert_called_once()
