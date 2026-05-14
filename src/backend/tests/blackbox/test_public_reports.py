from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

import pytest

from participium.models.enums import ReportStatus
from participium.services.report_service import ReportService


@pytest.fixture
def report_service():
    session = Mock()
    report_repository = Mock()
    category_repository = Mock()
    storage_service = Mock()
    notification_service = Mock()
    service = ReportService(
        session,
        report_repository,
        category_repository,
        storage_service,
        notification_service,
    )
    return service, report_repository


# TC-01: No filters, default sort. Repository receives public_only=True and all
# filter slots as None, and the service returns whatever the repository returns.
def test_list_public_reports_no_filters_default_sort(report_service) -> None:
    service, report_repo = report_service
    expected_reports = [Mock(name="report_1"), Mock(name="report_2")]
    report_repo.list_reports.return_value = expected_reports

    result = service.list_public_reports()

    assert result is expected_reports
    report_repo.list_reports.assert_called_once_with(
        public_only=True,
        category_id=None,
        status=None,
        date_from=None,
        date_to=None,
        sort="desc",
    )


# TC-02: category_id filter is forwarded.
def test_list_public_reports_filter_by_category(report_service) -> None:
    service, report_repo = report_service
    report_repo.list_reports.return_value = []

    result = service.list_public_reports(category_id=7)

    assert result == []
    report_repo.list_reports.assert_called_once_with(
        public_only=True,
        category_id=7,
        status=None,
        date_from=None,
        date_to=None,
        sort="desc",
    )


# TC-03: status filter is forwarded as-is.
def test_list_public_reports_filter_by_status(report_service) -> None:
    service, report_repo = report_service
    report_repo.list_reports.return_value = []

    service.list_public_reports(status=ReportStatus.RESOLVED)

    report_repo.list_reports.assert_called_once_with(
        public_only=True,
        category_id=None,
        status=ReportStatus.RESOLVED,
        date_from=None,
        date_to=None,
        sort="desc",
    )


# TC-04: date_from filter is forwarded.
def test_list_public_reports_filter_by_date_from(report_service) -> None:
    service, report_repo = report_service
    report_repo.list_reports.return_value = []
    date_from = datetime(2026, 1, 1, 0, 0, 0)

    service.list_public_reports(date_from=date_from)

    report_repo.list_reports.assert_called_once_with(
        public_only=True,
        category_id=None,
        status=None,
        date_from=date_from,
        date_to=None,
        sort="desc",
    )


# TC-05: date_to filter is forwarded.
def test_list_public_reports_filter_by_date_to(report_service) -> None:
    service, report_repo = report_service
    report_repo.list_reports.return_value = []
    date_to = datetime(2026, 12, 31, 23, 59, 59)

    service.list_public_reports(date_to=date_to)

    report_repo.list_reports.assert_called_once_with(
        public_only=True,
        category_id=None,
        status=None,
        date_from=None,
        date_to=date_to,
        sort="desc",
    )


# TC-06: sort="asc" overrides the default.
def test_list_public_reports_sort_ascending(report_service) -> None:
    service, report_repo = report_service
    report_repo.list_reports.return_value = []

    service.list_public_reports(sort="asc")

    report_repo.list_reports.assert_called_once_with(
        public_only=True,
        category_id=None,
        status=None,
        date_from=None,
        date_to=None,
        sort="asc",
    )


# TC-07: All filters combined are forwarded together.
def test_list_public_reports_all_filters_combined(report_service) -> None:
    service, report_repo = report_service
    report_repo.list_reports.return_value = []
    date_from = datetime(2026, 1, 1)
    date_to = datetime(2026, 6, 30)

    service.list_public_reports(
        category_id=3,
        status=ReportStatus.IN_PROGRESS,
        date_from=date_from,
        date_to=date_to,
        sort="asc",
    )

    report_repo.list_reports.assert_called_once_with(
        public_only=True,
        category_id=3,
        status=ReportStatus.IN_PROGRESS,
        date_from=date_from,
        date_to=date_to,
        sort="asc",
    )


# TC-08: Empty repository result propagates unchanged.
def test_list_public_reports_empty_result(report_service) -> None:
    service, report_repo = report_service
    report_repo.list_reports.return_value = []

    result = service.list_public_reports(category_id=99)

    assert result == []


# TC-09: Non-empty repository result is returned unchanged (no extra filtering at the service layer).
def test_list_public_reports_returns_repository_list_verbatim(report_service) -> None:
    service, report_repo = report_service
    reports = [Mock(name="r1"), Mock(name="r2"), Mock(name="r3")]
    report_repo.list_reports.return_value = reports

    result = service.list_public_reports()

    assert result is reports
    assert len(result) == 3


# TC-10: The service always passes public_only=True regardless of input.
def test_list_public_reports_always_sets_public_only_true(report_service) -> None:
    service, report_repo = report_service
    report_repo.list_reports.return_value = []

    service.list_public_reports(category_id=1, status=ReportStatus.ASSIGNED)

    _, kwargs = report_repo.list_reports.call_args
    assert kwargs["public_only"] is True
