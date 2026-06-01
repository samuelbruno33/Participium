from __future__ import annotations

import pytest
from datetime import datetime

from participium.database import close_connection, create_all, get_session, open_connection
from participium.models.report import Report, ReportFollower, ReportPhoto, ReportStatusHistory
from participium.repositories.report_repository import ReportRepository
from participium.models.enums import ReportStatus, Role
from tests.conftest import create_report, create_report_photo, create_report_status_history, create_report_follower

pytestmark = pytest.mark.integration


@pytest.fixture
def set_session(db):
    session = db
    report_repo = ReportRepository(session)
    return (session, report_repo)


def test_report_repo_add_and_get_by_id(set_session):
    session, report_repo = set_session
    report = create_report()

    report_repo.add( report )
    session.commit()
    result_report = report_repo.get_by_id(report.id)

    assert report.id is not None
    assert result_report.id == report.id


def test_report_add_photo(set_session):
    session, report_repo = set_session

    report = create_report()
    report_repo.add( report )
    session.flush()
    assert len(report.photos) == 0
    photo = create_report_photo( report_id=report.id )
    report_repo.add_photo( photo )
    session.commit()

    session.refresh(report)
    assert len(report.photos) == 1
    assert report.photos[0].id == photo.id


def test_report_add_status_entry(set_session):
    session, report_repo = set_session

    report = create_report( status=ReportStatus.PENDING_APPROVAL )
    report_repo.add( report )
    session.flush()
    assert len(report.status_history) == 0
    status_history = create_report_status_history( 
        report_id=report.id,
        previous_status=ReportStatus.PENDING_APPROVAL,
        new_status = ReportStatus.ASSIGNED,
    )
    report_repo.add_status_entry( status_history )
    session.commit()

    session.refresh(report)
    assert len(report.status_history) == 1
    assert report.status_history[0].id == status_history.id


def test_report_add_and_remove_follower(set_session):
    session, report_repo = set_session

    report = create_report()
    report_repo.add( report )
    session.flush()
    assert len(report.followers) == 0

    follower = create_report_follower( report_id=report.id )
    report_repo.add_follower( follower )
    session.flush()
    session.refresh(report)
    assert len(report.followers) == 1
    assert report.followers[0].id == follower.id

    report_repo.remove_follower( follower )
    session.commit()
    session.refresh(report)
    assert len(report.followers) == 0


def test_report_get_follower(set_session):
    session, report_repo = set_session

    follower = create_report_follower()
    report_repo.add_follower( follower )
    session.commit()

    returned_follower = report_repo.get_follower( 
        report_id=follower.report_id,
        user_id=follower.user_id,
     )
    assert returned_follower.id == follower.id


def test_report_get_follower_non_existent(set_session):
    session, report_repo = set_session

    returned_follower = report_repo.get_follower( 
        report_id=10,
        user_id=10,
     )
    assert returned_follower is None

def test_list_reports(set_session):
    session, report_repo = set_session

    report = create_report(
        status=ReportStatus.ASSIGNED,
        category_id=10
    )
    report_repo.add( report )
    session.commit()
    session.refresh(report)
    list = report_repo.list_reports(
        public_only=False,
        category_id=report.category_id,
        date_from=datetime.fromisoformat("1020-10-25"),
        date_to=datetime.fromisoformat("3020-10-25"),
    )

    assert len(list) == 1
    assert list[0].id == report.id


def test_list_user_reports(set_session):
    session, report_repo = set_session

    report = create_report(
        reporter_id=10,
        status=ReportStatus.PENDING_APPROVAL,
    )
    report_repo.add( report )
    session.commit()
    session.refresh(report)
    list = report_repo.list_user_reports(
        user_id=report.reporter_id
    )

    assert len(list) == 1
    assert list[0].id == report.id


def test_list_pending_all(set_session):
    session, report_repo = set_session

    report = create_report(
        category_id=42,
        status=ReportStatus.PENDING_APPROVAL,
    )
    report_repo.add( report )
    session.commit()
    session.refresh(report)
    list = report_repo.list_pending()

    assert len(list) == 1
    assert list[0].id == report.id


def test_list_pending_filter(set_session):
    session, report_repo = set_session

    report = create_report(
        category_id=42,
        status=ReportStatus.PENDING_APPROVAL,
    )
    report_repo.add( report )
    session.commit()
    session.refresh(report)
    list = report_repo.list_pending(
        category_id=report.category_id,
        date_from=datetime.fromisoformat("1020-10-25"),
        date_to=datetime.fromisoformat("3020-10-25"),
    )

    assert len(list) == 1
    assert list[0].id == report.id


def test_list_for_category(set_session):
    session, report_repo = set_session

    report = create_report(
        category_id=42,
        status=ReportStatus.ASSIGNED,
    )
    report_repo.add( report )
    session.commit()
    session.refresh(report)
    list = report_repo.list_for_category(
        category_id=report.category_id,
    )

    assert len(list) == 1
    assert list[0].id == report.id


def test_list_operator_reports(set_session):
    session, report_repo = set_session

    report = create_report(
        category_id=42,
        status=ReportStatus.ASSIGNED,
    )
    report_repo.add( report )
    session.commit()
    session.refresh(report)
    list = report_repo.list_operator_reports(
        role=Role.OPERATOR,
        category_id=report.category_id,
    )

    assert len(list) == 1
    assert list[0].id == report.id


def test_list_operator_reports_other_role(set_session):
    session, report_repo = set_session

    report = create_report(
        category_id=42,
        status=ReportStatus.ASSIGNED,
    )
    report_repo.add( report )
    session.commit()
    session.refresh(report)
    list = report_repo.list_operator_reports(
        role=Role.ADMIN,
        category_id=report.category_id,
    )

    assert len(list) == 1
    assert list[0].id == report.id



def test_list_followers(set_session):
    session, report_repo = set_session

    follower = create_report_follower(
        report_id=42
    )
    report_repo.add_follower( follower )
    session.commit()
    list = report_repo.list_followers(
        report_id=follower.report_id
    )

    assert len(list) == 1
    assert list[0].id == follower.id


def test_list_all(set_session):
    session, report_repo = set_session

    report = create_report()
    report_repo.add( report )
    session.commit()
    session.refresh(report)
    list = report_repo.list_all()

    assert len(list) == 1
    assert list[0].id == report.id

