from __future__ import annotations

from unittest.mock import Mock
import pytest

from participium.core import ValidationError
from werkzeug.datastructures import FileStorage
from participium.models.report import Report
from participium.models.enums import ReportStatus
from participium.services.report_service import ReportService
from participium.models.category import Category

@pytest.fixture
def mock_category_repository():
    """ Create a mock Category repository with only two categories:
        category 10 that is active and
        category 11 that is not active
    """
    def get_category(id):
        if id in (10, 11):
            category = Mock( spec=Category )
            category.id = id
            category.is_active = (id == 10)
            return category
        return None
    category_repository = Mock()
    category_repository.get_by_id.side_effect = get_category
    return category_repository

@pytest.fixture
def mock_report_service(mock_category_repository):
        session = Mock()
        report_repository = Mock()
        category_repository = mock_category_repository
        storage_service = Mock()
        notification_service = Mock()
        service = ReportService(
            session,
            report_repository,
            category_repository,
            storage_service,
            notification_service
        )
        return service



class TestCreateReport:

    def _photos_1_valid_1_none():
        one = Mock( spec = FileStorage, filename = "valid/path/one" )
        return [one, None]

    def _photos_1_invalid():
        one = Mock( spec = FileStorage, filename = None )
        return [one]

    def _photos_4_valid():
        one = Mock( spec = FileStorage, filename = "valid/path/one" )
        two = Mock( spec = FileStorage, filename = "valid/path/two" )
        three = Mock( spec = FileStorage, filename = "valid/path/three" )
        four = Mock( spec = FileStorage, filename = "valid/path/four" )
        return [one, two, three, four]

    def _photos_empty():
        return []

    def _photos_3_valid():
        one = Mock( spec = FileStorage, filename = "valid/path/one" )
        two = Mock( spec = FileStorage, filename = "valid/path/two" )
        three = Mock( spec = FileStorage, filename = "valid/path/three" )
        return [one, two, three]

    @pytest.mark.parametrize(
        "reporter, category_id, title, description, latitude, longitude, photos, is_anonymous, expected_exception, oracle",
        [
            (Mock(), None, "valid title", "valid description", 40.12, 9.34, _photos_1_valid_1_none(), True, ValidationError, None),
            (Mock(), "invalid: not an int", "valid title", "valid description", 40.12, 9.34, _photos_1_valid_1_none(), True, ValidationError, None), 
            (Mock(), 10, "valid title", "valid description", None, None, _photos_1_valid_1_none(), True, ValidationError, None),
            (Mock(), 10, "valid title", "valid description", "invalid: not a float", "invalid: not a float", _photos_1_valid_1_none(), True, ValidationError, None),
            (Mock(), 10, "valid title", "valid description", 40.12, 9.34, _photos_1_invalid(), True, ValidationError, None),
            (Mock(), 10, "valid title", "valid description", 40.12, 9.34, _photos_4_valid(), True, ValidationError, None),
            (Mock(), 10, "valid title", "valid description", 40.12, 9.34, _photos_1_valid_1_none(), True, None, Report),
            (Mock(), 11, "valid title", "valid description", 40.12, 9.34, _photos_1_valid_1_none(), True, ValidationError, None),
            (Mock(), 10, None, "valid description", 40.12, 9.34, _photos_1_valid_1_none(), True, ValidationError, None),
            (Mock(), 10, "valid title", None, 40.12, 9.34, _photos_1_valid_1_none(), True, ValidationError, None),
            (Mock(), 10, "valid title", "valid description", None, 9.34, _photos_1_valid_1_none(), True, ValidationError, None),
            (Mock(), 10, "valid title", "valid description", 40.12, None, _photos_1_valid_1_none(), True, ValidationError, None),
            (Mock(), 10, "valid title", "valid description", "invalid: not a float", 9.34, _photos_1_valid_1_none(), True, ValidationError, None),
            (Mock(), 10, "valid title", "valid description", 40.12, "invalid: not a float", _photos_1_valid_1_none(), True, ValidationError, None),
            (Mock(), 10, "valid title", "valid description", 40.12, 9.34, _photos_empty(), True, ValidationError, None),
            (Mock(), 10, "valid title", "valid description", 40.12, 9.34, _photos_3_valid(), True, None, Report),
            (Mock(), 10, "valid title", "valid description", 40.12, 9.34, _photos_3_valid(), False, None, Report),
        ]
    )
    def test_create_report_bundle(
        self,
        mock_report_service,
        reporter,
        category_id,
        title,
        description,
        latitude,
        longitude,
        photos,
        is_anonymous,
        expected_exception,
        oracle
    ):
        report_service = mock_report_service

        if expected_exception:
            with pytest.raises(expected_exception):
                report_service.create_report(reporter, category_id, title, description, latitude, longitude, photos, is_anonymous)
        else:
            
            report_service.report_repository.get_by_id.return_value = Report(
                title=title.strip(),
                description=description.strip(),
                latitude=latitude,
                longitude=longitude,
                is_anonymous=bool(is_anonymous),
                status=ReportStatus.PENDING_APPROVAL,
                reporter_id=reporter.id,
                category_id=category_id
            )
            result = report_service.create_report(reporter, category_id, title, description, latitude, longitude, photos, is_anonymous)
            
            assert isinstance(result, oracle)
            assert result.title == title.strip()
            assert result.description == description.strip()
            assert result.latitude == latitude
            assert result.longitude == longitude
            assert result.is_anonymous == bool(is_anonymous)
            assert result.status == ReportStatus.PENDING_APPROVAL
            assert result.reporter_id == reporter.id
            assert result.category_id == category_id
            report_service.report_repository.add.assert_called_once()
            report_service.session.flush.assert_called_once()
            report_service.report_repository.add_status_entry.assert_called_once()
            report_service.session.commit.assert_called_once()
            report_service.report_repository.get_by_id.assert_called_once()
