from __future__ import annotations

import pytest
from unittest.mock import Mock

from participium.core import ValidationError
from participium.models.report import Report
from participium.models.enums import ReportStatus
from participium.services.report_service import ReportService


@pytest.fixture()
def mock_report_service() -> ReportService:
    session = Mock()
    report_repository = Mock()
    storage_service = Mock()
    notification_service = Mock()

    # category_repository contains the categories 10 and 11, only the category 10 is active
    category_active = Mock()
    category_active.is_active = True
    category_inactive = Mock()
    category_inactive.is_active = False
    def get_category(id):
        if id == 10: return category_active
        elif id == 11: return category_inactive
        else: return False
    category_repository = Mock()
    category_repository.get_by_id.side_effect = get_category

    service = ReportService(
        session,
        report_repository,
        category_repository,
        storage_service,
        notification_service,
    )
    return service, report_repository


@pytest.mark.parametrize(
    "reporter, category_id, title, description, latitude, longitude, photos, is_anonymous, expected_exception, oracle",
    [
        # valid test cases
        (Mock(), 10, " valid title ", " valid description ", 45.12, 9.34, [Mock(), None], False, None, Report),
        (Mock(), 10, " valid title ", " valid description ", 45.12, 9.34, [Mock(), Mock(), Mock(), None], False, None, Report),
        (Mock(), 10, " valid title ", " valid description ", 45.12, 9.34, [Mock(), None], True, None, Report),
        (Mock(), 10, " valid title ", " valid description ", 45.12, 9.34, [Mock(), Mock(), Mock(), None], True, None, Report),
        # invalid test cases
        (Mock(), 12, " valid title ", " valid description ", 45.12, 9.34, [Mock(), None], False, ValidationError, None),
        (Mock(), 11, " valid title ", " valid description ", 45.12, 9.34, [Mock(), None], False, ValidationError, None),
        (Mock(), None, " valid title ", " valid description ", 45.12, 9.34, [Mock(), None], False, ValidationError, None),
        (Mock(), 10, "", " valid description ", 45.12, 9.34, [Mock(), None], False, ValidationError, None),
        (Mock(), 10, None, " valid description ", 45.12, 9.34, [Mock(), None], False, ValidationError, None),
        (Mock(), 10, " valid title ", "", 45.12, 9.34, [Mock(), None], False, ValidationError, None),
        (Mock(), 10, " valid title ", None, 45.12, 9.34, [Mock(), None], False, ValidationError, None),
        (Mock(), 10, " valid title ", " valid description ", "invalid latitude", 9.34, [Mock(), None], False, ValidationError, None),
        (Mock(), 10, " valid title ", " valid description ", "", 9.34, [Mock(), None], False, ValidationError, None),
        (Mock(), 10, " valid title ", " valid description ", None, 9.34, [Mock(), None], False, ValidationError, None),
        (Mock(), 10, " valid title ", " valid description ", 45.12, "invalid longitude", [Mock(), None], False, ValidationError, None),
        (Mock(), 10, " valid title ", " valid description ", 45.12, "", [Mock(), None], False, ValidationError, None),
        (Mock(), 10, " valid title ", " valid description ", 45.12, None, [Mock(), None], False, ValidationError, None),
        (Mock(), 10, " valid title ", " valid description ", 45.12, 9.34, [], False, ValidationError, None),
        (Mock(), 10, " valid title ", " valid description ", 45.12, 9.34, [None], False, ValidationError, None),
        (Mock(), 10, " valid title ", " valid description ", 45.12, 9.34, [Mock(), Mock(), Mock(), Mock()], False, ValidationError, None),
        (Mock(), 10, " valid title ", " valid description ", 45.12, 9.34, None, False, ValidationError, None)
    ]
)
def test_suite_create_report(mock_report_service, reporter, category_id, title, description, latitude, longitude, photos, is_anonymous, expected_exception, oracle):
    service, repo = mock_report_service
    if expected_exception :
        with pytest.raises(expected_exception) :
            service.create_report( reporter, category_id, title, description, latitude, longitude, photos, is_anonymous)
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
        
        assert isinstance( result, oracle )
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

