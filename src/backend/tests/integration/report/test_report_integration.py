from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import Mock
from werkzeug.datastructures import FileStorage
from tests.conftest import *

from participium.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from participium.models.report import Report, ReportFollower, ReportPhoto, ReportStatusHistory
from participium.repositories.report_repository import ReportRepository
from participium.repositories.category_repository import CategoryRepository
from participium.repositories.notification_repository import NotificationRepository
from participium.repositories.user_repository import UserRepository
from participium.models.enums import ReportStatus, Role
from participium.services.report_service import ReportService
from participium.services.storage_service import StorageService
from participium.services.notification_service import NotificationService

pytestmark = pytest.mark.integration

@pytest.fixture
def set_session(db):
    return db

@pytest.fixture
def set_category_repo(set_session, create_category):
    session = set_session
    cat_repo = CategoryRepository(session)
    category = create_category(
        category_id = 10,
        is_active = True,
    )
    cat_repo.add(category)
    session.flush()
    category = create_category(
        category_id = 11,
        is_active = False,
    )
    cat_repo.add(category)
    session.commit()

    return cat_repo

@pytest.fixture
def set_report_service(set_session, set_category_repo):
    """ Test report service with the db and all its dependencies
        except email_gateway
    """
    session = set_session
    report_repository = ReportRepository(session)
    category_repository = set_category_repo
    storage_service = StorageService()
    notification_repository = NotificationRepository(session)
    user_repository = UserRepository(session)
    email_gateway = Mock()
    notification_service = NotificationService(
        session=session,
        notification_repository=notification_repository,
        email_gateway=email_gateway
    )
    report_service = ReportService(
        session=session,
        report_repository=ReportRepository(session),
        category_repository=CategoryRepository(session),
        storage_service=storage_service,
        notification_service=notification_service,
    )
    return {
        "report_service": report_service,
        "session": session,
        "report_repository": report_repository,
        "category_repository": category_repository,
        "user_repository": user_repository,
        "storage_service": storage_service,
        "notification_service": notification_service,
    }
    
def test_integration_create_report(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    cat_repo = set_report_service["category_repository"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user()
    user_repo.add(user)
    session.flush()

    report = report_service.create_report(
        reporter=user,
        category_id=10,
        title="the title",
        description="a description",
        latitude=45.12,
        longitude=9.34,
        photos=[ FileStorage(filename="asd"), None, FileStorage() ],
        is_anonymous=True
    )

    assert isinstance(report, Report)
    assert report.title == "the title"
    assert report.description == "a description"
    assert report.latitude == 45.12
    assert report.longitude == 9.34
    assert report.is_anonymous == True
    assert report.status is ReportStatus.PENDING_APPROVAL
    assert report.rejection_reason == None
    assert report.reporter_id == user.id
    assert report.category_id == 10
    assert report.reporter == user
    assert report.category == cat_repo.get_by_id(10)
    assert len(report.photos) == 1
    assert report.photos[0].original_filename == "asd"
    assert len(report.status_history) == 1
    assert len(report.followers) == 0
    assert len(report.messages) == 0

def test_integration_list_public_reports(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]

    report_1 = create_report( status=ReportStatus.IN_PROGRESS )
    report_repo.add( report_1 )
    report_2 = create_report( status=ReportStatus.PENDING_APPROVAL )
    report_repo.add( report_2 )
    session.commit()

    list = report_service.list_public_reports()
    assert len(list) == 1
    assert isinstance(list[0], Report)
    assert list[0].id == report_1.id


def test_integration_list_user_reports(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    cat_repo = set_report_service["category_repository"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user()
    user_repo.add(user)
    session.flush()

    report = create_report( reporter_id=user.id )
    report_repo.add( report )
    session.commit()
    
    list = report_service.list_user_reports(user)

    assert len(list) == 1
    assert isinstance(list[0], Report)
    assert list[0].id == report.id


def test_integration_list_get_report(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]

    report = create_report()
    report_repo.add( report )
    session.commit()
    
    result_report = report_service.get_report( report.id )

    assert isinstance(result_report, Report)
    assert result_report.id == report.id


def test_integration_get_accessible_report_public(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user(
        role=Role.CITIZEN
    )
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.ASSIGNED # the report is publicly visible
    )
    report_repo.add( report )
    session.commit()
    
    result_report = report_service.get_accessible_report(
        report_id=report.id,
        user=user
    )

    assert isinstance(result_report, Report)
    assert result_report.id == report.id

def test_integration_get_accessible_report_no_user(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    report = create_report(
        status=ReportStatus.REJECTED # the report is not publicly visible
    )
    report_repo.add( report )
    session.commit()
    
    with pytest.raises(AuthorizationError):
        report_service.get_accessible_report(
            report_id=report.id,
            user=None
        )


def test_integration_get_accessible_report_user_reporter(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user(
        role=Role.CITIZEN
    )
    user_repo.add(user)
    session.flush()

    report = create_report(
        reporter_id=user.id, # this user can see the report
        status=ReportStatus.REJECTED # the report is not publicly visible
    )
    report_repo.add( report )
    session.commit()
    
    result_report = report_service.get_accessible_report(
        report_id=report.id,
        user=user
    )

    assert isinstance(result_report, Report)
    assert result_report.id == report.id


def test_integration_get_accessible_report_admin(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user(
        role=Role.ADMIN
    )
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.REJECTED # the report is not publicly visible
    )
    report_repo.add( report )
    session.commit()
    
    result_report = report_service.get_accessible_report(
        report_id=report.id,
        user=user
    )

    assert result_report is not None
    assert result_report.id == report.id


def test_integration_get_accessible_report_operator_assigned(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user(
        role=Role.OPERATOR,
        category_id=42,
    )
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.REJECTED, # the report is not publicly visible
        category_id=user.category_id, # same category of the user
    )
    report_repo.add( report )
    session.commit()
    
    result_report = report_service.get_accessible_report(
        report_id=report.id,
        user=user
    )

    assert isinstance(result_report, Report)
    assert result_report.id == report.id

def test_integration_get_accessible_report_no_access_allowed(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user(
        role=Role.OPERATOR,
    )
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.REJECTED, # the report is not publicly visible
    )
    report_repo.add( report )
    session.commit()
    
    with pytest.raises(AuthorizationError):
        report_service.get_accessible_report(
            report_id=report.id,
            user=user
        )


def test_integration_follow_report_non_public(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user()
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.REJECTED, # the report is not publicly visible
    )
    report_repo.add( report )
    session.commit()
    
    with pytest.raises(ValidationError):
        report_service.follow_report(
            report_id=report.id,
            user=user
        )


def test_integration_follow_report_new_follower(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user()
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.IN_PROGRESS, # the report is not publicly visible
    )
    report_repo.add( report )
    session.commit()
    
    result_report = report_service.follow_report(
        report_id=report.id,
        user=user
    )
    
    assert isinstance(result_report, Report)
    assert result_report.id == report.id

def test_integration_follow_report_already_follower(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user()
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.IN_PROGRESS, # the report is not publicly visible
    )
    report_repo.add( report )
    session.flush()

    follower = create_report_follower(
        report_id=report.id,
        user_id=user.id
    )
    report_repo.add_follower( follower )
    session.flush()
    session.refresh(report)

    session.commit()
    result_report = report_service.follow_report(
        report_id=report.id,
        user=user
    )
    
    assert isinstance(result_report, Report)
    assert result_report.id == report.id


def test_integration_unfollow_report(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user()
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.IN_PROGRESS, # the report is not publicly visible
    )
    report_repo.add( report )
    session.flush()
    
    follower = create_report_follower(
        report_id=report.id,
        user_id=user.id
    )
    report_repo.add_follower( follower )
    session.refresh(report)
    session.commit()
    assert len(report.followers) == 1

    result_report = report_service.unfollow_report(
        report_id=report.id,
        user=user
    )
    session.refresh(report)

    assert isinstance(result_report, Report)
    assert result_report.id == report.id
    assert len(result_report.followers) == 0


def test_integration_unfollow_report_do_nothing(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user()
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.IN_PROGRESS, # the report is not publicly visible
    )
    report_repo.add( report )
    session.flush()
    
    result_report = report_service.unfollow_report(
        report_id=report.id,
        user=user
    )
    session.refresh(report)

    assert isinstance(result_report, Report)
    assert result_report.id == report.id
    assert len(result_report.followers) == 0


def test_integration_list_pending_reports(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    report_1 = create_report(
        status=ReportStatus.PENDING_APPROVAL,
        category_id=10,
    )
    report_repo.add( report_1 )
    session.flush()
    
    report_2 = create_report(
        status=ReportStatus.ASSIGNED,
        category_id=10,
    )
    report_repo.add( report_2 )
    session.commit()
    
    list = report_service.list_pending_reports(
        filters={
            "category_id": 10,
            "date_from": datetime.fromisoformat("2020-02-20"),
            "date_to": datetime.fromisoformat("3020-02-20"),
        }
    )

    assert list is not None
    assert len(list) == 1
    assert list[0].id == report_1.id


def test_integration_list_for_category_not_operator(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user(
        role=Role.CITIZEN,
        category_id=10
    )
    user_repo.add(user)
    session.flush()

    # report with wrong status
    report_1 = create_report(
        status=ReportStatus.PENDING_APPROVAL,
        category_id=10,
    )
    report_repo.add( report_1 )
    session.flush()
    
    # report with wrong category but since the user is not
    # an operator is ok
    report_2 = create_report(
        status=ReportStatus.ASSIGNED,
        category_id=11,
    )
    report_repo.add( report_2 )
    session.flush()
    
    # ok
    report_3 = create_report(
        status=ReportStatus.ASSIGNED,
        category_id=10,
    )
    report_repo.add( report_3 )
    session.commit()
    
    list = report_service.list_operator_reports( user )

    assert list is not None
    assert len(list) == 2

def test_integration_list_for_category_operator(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user(
        role=Role.OPERATOR,
        category_id=10
    )
    user_repo.add(user)
    session.flush()

    # report with wrong status
    report_1 = create_report(
        status=ReportStatus.PENDING_APPROVAL,
        category_id=10,
    )
    report_repo.add( report_1 )
    session.flush()
    
    # report with wrong category but since the user is not
    # an operator is ok
    report_2 = create_report(
        status=ReportStatus.ASSIGNED,
        category_id=11,
    )
    report_repo.add( report_2 )
    session.flush()
    
    # ok
    report_3 = create_report(
        status=ReportStatus.ASSIGNED,
        category_id=10,
    )
    report_repo.add( report_3 )
    session.commit()
    
    list = report_service.list_operator_reports( user )

    assert list is not None
    assert len(list) == 1


def test_integration_assign_report(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user(
        role=Role.OPERATOR,
        category_id=10
    )
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.PENDING_APPROVAL,
        category_id=10,
    )
    report_repo.add( report )
    session.commit()
    
    result_report = report_service.assign_report(
        report_id=report.id,
        operator=user
    )

    session.refresh(result_report)
    assert isinstance(result_report, Report)
    assert result_report.status == ReportStatus.ASSIGNED
    assert len(result_report.status_history) == 1


def test_integration_update_status(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user(
        role=Role.OPERATOR,
        category_id=10
    )
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.PENDING_APPROVAL,
        category_id=10,
    )
    report_repo.add( report )
    session.commit()
    
    result_report = report_service.update_status(
        report_id=report.id,
        operator=user,
        next_status_value=ReportStatus.REJECTED,
        note="testing around"
    )

    session.refresh(result_report)
    assert isinstance(result_report, Report)
    assert result_report.status == ReportStatus.REJECTED
    assert len(result_report.status_history) == 1
    assert result_report.status_history[0].previous_status == ReportStatus.PENDING_APPROVAL

def test_integration_export_rows(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]

    # wrong report status
    report_3 = create_report(
        status=ReportStatus.PENDING_APPROVAL,
        category_id=10,
    )
    report_repo.add( report_3 )
    session.commit()
    
    # wrong gategory
    report_2 = create_report(
        status=ReportStatus.ASSIGNED,
        category_id=11,
    )
    report_repo.add( report_2 )
    session.commit()
    
    # ok
    report_1 = create_report(
        status=ReportStatus.ASSIGNED,
        category_id=10,
    )
    report_repo.add( report_1 )
    session.commit()
    
    rows = report_service.export_rows(
        category_id=10,
        status=ReportStatus.ASSIGNED,
        date_from=datetime.fromisoformat("2020-05-14"),
        date_to=datetime.fromisoformat("3020-05-14"),
        sort="asc",
    )

    assert type(rows) is list
    assert len(rows) == 1
    assert rows[0]["status"] == report_1.status


def test_integration_ensure_operator_category_access_wrong_role(set_report_service, create_user):
    report_service = set_report_service["report_service"]
    session = set_report_service["session"]
    report_repo = set_report_service["report_repository"]
    user_repo = set_report_service["user_repository"]

    user = create_user(
        role=Role.CITIZEN,
        category_id=10
    )
    user_repo.add(user)
    session.flush()

    report = create_report(
        status=ReportStatus.PENDING_APPROVAL,
        category_id=10,
    )
    report_repo.add( report )
    session.commit()
    
    with pytest.raises(AuthorizationError):
        report_service._ensure_operator_category_access(
            operator=user,
            report=report
        )
