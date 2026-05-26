from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta

import pytest
from flask.testing import FlaskClient

from participium import create_app
from participium.core.security import hash_password
from participium.database import close_connection, get_session
from participium.models.category import Category
from participium.models.enums import ReportStatus, Role
from participium.models.report import Report
from participium.models.user import User


pytestmark = pytest.mark.e2e


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    """Create a Flask app instance with an isolated in-memory SQLite database.

    Uses a shared-cache memory URI so all sessions in the test see the same DB,
    while the database is still isolated from other tests because the connection
    is opened fresh by create_app() and closed via the client fixture.
    """
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite+pysqlite:///file:test_public_browsing?mode=memory&cache=shared",
    )
    monkeypatch.setenv("AUTO_INIT_DB", "true")
    monkeypatch.setenv("BOOTSTRAP_REFERENCE_DATA", "false")
    monkeypatch.setenv("BOOTSTRAP_DEMO_DATA", "false")

    application = create_app()
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def db_session(app):
    with app.app_context():
        yield get_session()


@pytest.fixture
def client(app) -> FlaskClient:
    yield app.test_client()
    close_connection()


@pytest.fixture
def seeded_data(client, db_session) -> dict:
    """Insert two categories (one inactive), a reporter, and reports across
    every relevant status so each filter scenario has a deterministic fixture.

    Returns the inserted entity ids so tests can reference them without
    relying on autoincrement order.
    """
    roads = Category(name="Roads", is_active=True)
    waste = Category(name="Waste", is_active=True)
    archived = Category(name="Archived", is_active=False)
    db_session.add_all([roads, waste, archived])
    db_session.flush()

    reporter = User(
        username="reporter_pb",
        email="reporter_pb@test.com",
        password_hash=hash_password("Password123!"),
        role=Role.CITIZEN,
        first_name="Pb",
        last_name="Reporter",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(reporter)
    db_session.flush()

    base_time = datetime(2026, 5, 1, 12, 0, 0)

    def _report(
        title: str,
        category: Category,
        status: ReportStatus,
        offset_days: int,
    ) -> Report:
        report = Report(
            title=title,
            description=f"{title} description",
            latitude=45.0,
            longitude=9.0,
            status=status,
            reporter_id=reporter.id,
            category_id=category.id,
        )
        db_session.add(report)
        db_session.flush()
        # Overwrite the auto-set created_at so date filtering is predictable.
        report.created_at = base_time + timedelta(days=offset_days)
        return report

    public_roads_assigned = _report("Pothole on Main", roads, ReportStatus.ASSIGNED, 0)
    public_roads_resolved = _report("Pothole fixed", roads, ReportStatus.RESOLVED, 5)
    public_waste_in_progress = _report("Bin overflow", waste, ReportStatus.IN_PROGRESS, 10)
    private_pending = _report("Awaiting review", roads, ReportStatus.PENDING_APPROVAL, 1)
    private_rejected = _report("Bad report", roads, ReportStatus.REJECTED, 2)

    db_session.commit()

    return {
        "roads_id": roads.id,
        "waste_id": waste.id,
        "archived_id": archived.id,
        "public_roads_assigned_id": public_roads_assigned.id,
        "public_roads_resolved_id": public_roads_resolved.id,
        "public_waste_in_progress_id": public_waste_in_progress.id,
        "private_pending_id": private_pending.id,
        "private_rejected_id": private_rejected.id,
        "base_time": base_time,
    }


def _ids(payload: list[dict]) -> list[int]:
    return [item["id"] for item in payload]


class TestPublicCategoriesEndpoint:
    """GET /api/v1/categories should return only active categories."""

    def test_lists_only_active_categories(self, client, seeded_data) -> None:
        response = client.get("/api/v1/categories")

        assert response.status_code == 200
        names = [c["name"] for c in response.get_json()]
        assert "Roads" in names
        assert "Waste" in names
        assert "Archived" not in names

    def test_no_authentication_required(self, client, seeded_data) -> None:
        # Calling without any session cookie still works for the public endpoint.
        response = client.get("/api/v1/categories")
        assert response.status_code == 200


class TestPublicReportsListing:
    """GET /api/v1/reports lists publicly-visible reports with optional filters."""

    def test_lists_only_public_reports(self, client, seeded_data) -> None:
        response = client.get("/api/v1/reports")

        assert response.status_code == 200
        ids = _ids(response.get_json())
        # PENDING_APPROVAL and REJECTED must be excluded.
        assert seeded_data["private_pending_id"] not in ids
        assert seeded_data["private_rejected_id"] not in ids
        # All three public-status reports must be present.
        assert seeded_data["public_roads_assigned_id"] in ids
        assert seeded_data["public_roads_resolved_id"] in ids
        assert seeded_data["public_waste_in_progress_id"] in ids

    def test_default_sort_is_descending_by_created_at(self, client, seeded_data) -> None:
        response = client.get("/api/v1/reports")

        ids = _ids(response.get_json())
        # The waste report was inserted 10 days after the assigned-roads report,
        # so descending sort puts it first.
        assert ids[0] == seeded_data["public_waste_in_progress_id"]
        assert ids[-1] == seeded_data["public_roads_assigned_id"]

    def test_sort_ascending(self, client, seeded_data) -> None:
        response = client.get("/api/v1/reports?sort=asc")

        ids = _ids(response.get_json())
        assert ids[0] == seeded_data["public_roads_assigned_id"]
        assert ids[-1] == seeded_data["public_waste_in_progress_id"]

    def test_filter_by_category(self, client, seeded_data) -> None:
        response = client.get(f"/api/v1/reports?category_id={seeded_data['waste_id']}")

        ids = _ids(response.get_json())
        assert ids == [seeded_data["public_waste_in_progress_id"]]

    def test_filter_by_status(self, client, seeded_data) -> None:
        response = client.get("/api/v1/reports?status=Resolved")

        ids = _ids(response.get_json())
        assert ids == [seeded_data["public_roads_resolved_id"]]

    def test_filter_by_invalid_status_returns_400(self, client, seeded_data) -> None:
        response = client.get("/api/v1/reports?status=NotAStatus")
        assert response.status_code == 400

    def test_filter_by_date_range_inclusive(self, client, seeded_data) -> None:
        # Reports occur at base_time + {0, 5, 10} days. Window [day 3, day 8]
        # should match only the day-5 (resolved) report.
        base = seeded_data["base_time"]
        date_from = (base + timedelta(days=3)).isoformat()
        date_to = (base + timedelta(days=8)).isoformat()

        response = client.get(f"/api/v1/reports?date_from={date_from}&date_to={date_to}")

        ids = _ids(response.get_json())
        assert ids == [seeded_data["public_roads_resolved_id"]]

    def test_filter_by_date_from_only(self, client, seeded_data) -> None:
        base = seeded_data["base_time"]
        date_from = (base + timedelta(days=7)).isoformat()

        response = client.get(f"/api/v1/reports?date_from={date_from}")

        ids = _ids(response.get_json())
        assert ids == [seeded_data["public_waste_in_progress_id"]]

    def test_filter_combination_returns_empty_when_no_match(
        self, client, seeded_data
    ) -> None:
        # waste category + Resolved status: no such report in the fixture.
        response = client.get(
            f"/api/v1/reports?category_id={seeded_data['waste_id']}&status=Resolved"
        )

        assert response.get_json() == []


class TestPublicReportDetail:
    """GET /api/v1/reports/<id> grants anonymous access to public reports only."""

    def test_anonymous_can_view_public_report(self, client, seeded_data) -> None:
        response = client.get(f"/api/v1/reports/{seeded_data['public_roads_assigned_id']}")

        assert response.status_code == 200
        body = response.get_json()
        assert body["id"] == seeded_data["public_roads_assigned_id"]
        assert body["status"] == ReportStatus.ASSIGNED.value

    def test_anonymous_cannot_view_private_pending_report(
        self, client, seeded_data
    ) -> None:
        response = client.get(f"/api/v1/reports/{seeded_data['private_pending_id']}")
        # AuthorizationError -> 403
        assert response.status_code == 403

    def test_anonymous_cannot_view_private_rejected_report(
        self, client, seeded_data
    ) -> None:
        response = client.get(f"/api/v1/reports/{seeded_data['private_rejected_id']}")
        assert response.status_code == 403

    def test_unknown_report_id_returns_404(self, client, seeded_data) -> None:
        response = client.get("/api/v1/reports/999999")
        assert response.status_code == 404


class TestPublicReportsCsvExport:
    """GET /api/v1/reports/export returns a CSV mirroring the filtered list."""

    EXPECTED_HEADERS = [
        "id", "title", "category", "status", "created_at", "latitude", "longitude",
    ]

    def _parse_csv(self, response) -> tuple[list[str], list[dict]]:
        text = response.get_data(as_text=True)
        reader = csv.DictReader(io.StringIO(text))
        return reader.fieldnames, list(reader)

    def test_export_uses_csv_mimetype_and_attachment_filename(
        self, client, seeded_data
    ) -> None:
        response = client.get("/api/v1/reports/export")

        assert response.status_code == 200
        assert response.mimetype == "text/csv"
        assert "attachment" in response.headers.get("Content-Disposition", "")
        assert "participium_reports.csv" in response.headers.get(
            "Content-Disposition", ""
        )

    def test_export_header_row_matches_expected_fields(self, client, seeded_data) -> None:
        response = client.get("/api/v1/reports/export")
        headers, _ = self._parse_csv(response)
        assert headers == self.EXPECTED_HEADERS

    def test_export_contains_only_public_reports(self, client, seeded_data) -> None:
        response = client.get("/api/v1/reports/export")
        _, rows = self._parse_csv(response)

        exported_ids = {int(row["id"]) for row in rows}
        public_ids = {
            seeded_data["public_roads_assigned_id"],
            seeded_data["public_roads_resolved_id"],
            seeded_data["public_waste_in_progress_id"],
        }
        assert exported_ids == public_ids

    def test_export_row_content_matches_report(self, client, seeded_data) -> None:
        response = client.get("/api/v1/reports/export")
        _, rows = self._parse_csv(response)

        # The Roads/Resolved row is the easiest to identify by its title.
        resolved_row = next(
            r for r in rows if int(r["id"]) == seeded_data["public_roads_resolved_id"]
        )
        assert resolved_row["title"] == "Pothole fixed"
        assert resolved_row["category"] == "Roads"
        assert resolved_row["status"] == ReportStatus.RESOLVED.value
        assert float(resolved_row["latitude"]) == 45.0
        assert float(resolved_row["longitude"]) == 9.0
        # created_at is ISO-8601 — parsing should succeed.
        assert datetime.fromisoformat(resolved_row["created_at"]) is not None

    def test_export_respects_category_filter(self, client, seeded_data) -> None:
        response = client.get(
            f"/api/v1/reports/export?category_id={seeded_data['waste_id']}"
        )
        _, rows = self._parse_csv(response)

        assert len(rows) == 1
        assert int(rows[0]["id"]) == seeded_data["public_waste_in_progress_id"]

    def test_export_empty_result_still_returns_header_row(
        self, client, seeded_data
    ) -> None:
        # No report exists for the archived (inactive) category.
        response = client.get(
            f"/api/v1/reports/export?category_id={seeded_data['archived_id']}"
        )
        headers, rows = self._parse_csv(response)

        assert headers == self.EXPECTED_HEADERS
        assert rows == []
