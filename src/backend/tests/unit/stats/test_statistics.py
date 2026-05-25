import pytest
from datetime import datetime
from unittest.mock import MagicMock
from participium.services.statistics_service import StatisticsService
from participium.models.enums import ReportStatus


# Mock classes to simulate SQLAlchemy models without DB dependencies
class MockCategory:
    def __init__(self, name: str):
        self.name = name


class MockUser:
    def __init__(self, user_id: int, username: str):
        self.id = user_id
        self.username = username


class MockReport:
    def __init__(self, category_name: str, status_enum: ReportStatus, reporter: MockUser | None, created_at: datetime):
        self.category = MockCategory(category_name)
        self.status = status_enum
        self.reporter = reporter
        self.created_at = created_at


@pytest.fixture
def mock_reports():
    u1 = MockUser(1, "alice")
    u2 = MockUser(2, "bob")

    return [
        MockReport("Roads", ReportStatus.RESOLVED, u1, datetime(2023, 1, 1, 10, 0)),
        MockReport("Roads", ReportStatus.PENDING_APPROVAL, u2, datetime(2023, 1, 2, 10, 0)),
        # Deleted citizen simulation
        MockReport("Lighting", ReportStatus.IN_PROGRESS, None, datetime(2023, 1, 15, 10, 0)),
        # Bob created multiple reports to dominate the top % lists
        MockReport("Roads", ReportStatus.ASSIGNED, u2, datetime(2023, 2, 1, 10, 0)),
        MockReport("Lighting", ReportStatus.RESOLVED, u2, datetime(2023, 2, 1, 10, 0)),
    ]


@pytest.fixture
def mock_repo(mock_reports):
    repo = MagicMock()
    repo.list_reports.return_value = mock_reports
    repo.list_all.return_value = mock_reports
    return repo


def test_public_statistics_default_day(mock_repo):
    service = StatisticsService(report_repository=mock_repo)

    result = service.public_statistics()

    mock_repo.list_reports.assert_called_once_with(public_only=True)
    assert result["total_reports"] == 5
    assert result["reports_by_category"] == {"Roads": 3, "Lighting": 2}

    # Check default granularity ("day")
    assert "2023-01-01" in result["trends"]
    assert result["trends"]["2023-02-01"] == 2


def test_public_statistics_trends_month(mock_repo):
    service = StatisticsService(report_repository=mock_repo)
    result = service.public_statistics(granularity="month")

    assert result["trends"]["2023-01"] == 3
    assert result["trends"]["2023-02"] == 2


def test_public_statistics_trends_week(mock_repo):
    service = StatisticsService(report_repository=mock_repo)
    result = service.public_statistics(granularity="week")

    # Ensure ISO week format is applied correctly (e.g., 2023-W05)
    assert any("-W" in key for key in result["trends"].keys())


def test_admin_statistics_full_breakdown(mock_repo):
    service = StatisticsService(report_repository=mock_repo)
    result = service.admin_statistics()

    mock_repo.list_all.assert_called_once()

    assert result["reports_by_status"][ReportStatus.RESOLVED.value] == 2
    assert result["reports_by_type"]["Roads"] == 3

    # Check reporter labelling (Valid user vs None)
    assert result["reports_by_reporter"]["Deleted Citizen"] == 1
    assert result["reports_by_reporter"]["bob (2)"] == 3

    # Check complex counters
    assert result["reports_by_reporter_and_type"]["bob (2) | Roads"] == 2
    assert result["reports_by_type_and_status"][f"Lighting | {ReportStatus.RESOLVED.value}"] == 1


def test_admin_statistics_top_percent(mock_repo):
    service = StatisticsService(report_repository=mock_repo)
    result = service.admin_statistics()

    # There are 3 unique reporters: alice, bob, Deleted Citizen.
    # 1% of 3 = 0.03 -> ceil(0.03) = 1.
    # Top 1 reporter is bob (3 reports).
    # Breakdown of bob's reports: Roads (2), Lighting (1).
    assert result["top_1_percent_by_type"] == {"Roads": 2, "Lighting": 1}
    assert result["top_5_percent_by_type"] == {"Roads": 2, "Lighting": 1}


def test_admin_statistics_empty_repository():
    empty_repo = MagicMock()
    empty_repo.list_all.return_value = []
    service = StatisticsService(report_repository=empty_repo)

    result = service.admin_statistics()

    # Ensure no division by zero or errors occur when percent breakdown runs on empty list
    assert result["top_1_percent_by_type"] == {}
    assert result["reports_by_status"] == {}
    assert result["reports_by_reporter"] == {}