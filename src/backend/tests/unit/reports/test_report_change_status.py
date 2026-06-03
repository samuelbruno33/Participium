from __future__ import annotations

from unittest.mock import Mock
import pytest

from participium.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from werkzeug.datastructures import FileStorage
from participium.models.report import Report
from participium.models.enums import ReportStatus
from participium.services.report_service import ReportService
from participium.models.category import Category
from participium.models.enums import ReportStatus, Role
from tests.conftest import user

def _user_citizen():
    return user(role=Role.CITIZEN)

def _user_admin():
    return user(role=Role.ADMIN)

def _user_operator_correct_category():
    return user(role=Role.OPERATOR, category_id=100)

def _user_operator_wrong_category():
    return user(role=Role.OPERATOR)

@pytest.fixture
def mock_category_repository():
    """ Create a mock Category repository with only two categories:
        category 100 that is active and
        category 101 that is not active
    """
    def get_category(id):
        if id in (100, 101):
            category = Mock( spec=Category )
            category.id = id
            category.is_active = (id == 100)
            return category
        return None
    category_repository = Mock()
    category_repository.get_by_id.side_effect = get_category
    return category_repository

@pytest.fixture
def mock_report_repository():
    """ Create a mock Report repository containing only three reports:
        report 10 with status PENDING_APPROVAL (correct) and category_id 100 (correct)
        report 11 with status PENDING_APPROVAL (correct) and category_id 101 (wrong)
        report 12 with status ASSIGNED (wrong) and category_id 100 (correct)
        """
    def get_report(id):
        if id in (10, 11, 12):
            report = Mock( spec=Report )
            report.id = id
            report.followers = [Mock(), Mock(), Mock()]
            if id == 10:
                report.status = ReportStatus.PENDING_APPROVAL
                report.category_id = 100
            elif id == 11:
                report.status = ReportStatus.PENDING_APPROVAL
                report.category_id = 101
            elif id == 12:
                report.status = ReportStatus.ASSIGNED
                report.category_id = 100
            return report
        return None
    report_repository = Mock()
    report_repository.get_by_id.side_effect = get_report
    return report_repository
 
@pytest.fixture
def mock_report_service(mock_category_repository, mock_report_repository):
        session = Mock()
        report_repository = mock_report_repository
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


class TestAssignReport:

    @pytest.mark.parametrize(
        "report_id, operator, expected_exception",
        [
            ( 10, _user_citizen(), AuthorizationError ), # citezens con not access reports
            ( 9, _user_admin(), NotFoundError ), # non existent report
        ]
    )
    def test_assign_report_wrong_role_and_no_report( self, mock_report_service, report_id, operator, expected_exception ):
        report_service = mock_report_service

        with pytest.raises(expected_exception):
            report_service.assign_report( report_id=report_id, operator=operator )


    @pytest.mark.parametrize(
        "report_id, operator, expected_exception, oracle",
        [
            ( 11, _user_operator_wrong_category(), AuthorizationError, None ), # mismatching category
            ( 12, _user_admin(), ValidationError, None ), # wrong status
            ( 10, _user_admin(), None, Report ), # admin has access with any category_id
            ( 10, _user_operator_correct_category(), None, Report ), # operator has access only if category_id matches
        ]
    )
    def test_assign_report( self, mock_report_service, report_id, operator, expected_exception, oracle ):
        report_service = mock_report_service


        if expected_exception:
            with pytest.raises(expected_exception):
                report_service.assign_report(report_id=report_id, operator=operator)
                report_service.report_repository.get_by_id.assert_called_once()
        else:
            result = report_service.assign_report(report_id=report_id, operator=operator)
            
            assert isinstance(result, oracle)
            report_service.report_repository.add_status_entry.assert_called_once()
            report_service.notification_service.notify_status_change.assert_called_once()
            report_service.session.commit.assert_called_once()
            report_service.report_repository.get_by_id.assert_called()



class TestUpdateStatus:

    @pytest.mark.parametrize(
        "report_id, operator, next_status_value, note ,expected_exception",
        [
            ( 10, _user_citizen(), None, None, AuthorizationError ), # citezens con not update status
            ( 9, _user_admin(), None, None, NotFoundError ), # non existent report
        ]
    )
    def test_update_status_wrong_role_and_no_report( self, mock_report_service, report_id, operator, next_status_value, note, expected_exception ):
        report_service = mock_report_service

        with pytest.raises(expected_exception):
            report_service.update_status( report_id=report_id, operator=operator, next_status_value=next_status_value, note=note )


    @pytest.mark.parametrize(
        "report_id, operator, next_status_value, note, expected_exception, oracle",
        [
            ( 11, _user_operator_wrong_category(), ReportStatus.ASSIGNED, "a note", AuthorizationError, None ), # mismatching category
            ( 10, _user_admin(), None, "a note", ValidationError, None ), # next status non existent
            ( 10, _user_admin(), ReportStatus.REJECTED, None, ValidationError, None ), # status REJECTED needs a note
            ( 10, _user_admin(), ReportStatus.REJECTED, "a note", None , Report ), # ok
            ( 10, _user_operator_correct_category(), ReportStatus.ASSIGNED, None, None, Report ), # ok
        ]
    )
    def test_update_status( self, mock_report_service, report_id, operator, next_status_value, note, expected_exception, oracle ):
        report_service = mock_report_service

        if expected_exception:
            with pytest.raises(expected_exception):
                report_service.update_status( report_id=report_id, operator=operator, next_status_value=next_status_value, note=note )
                report_service.report_repository.get_by_id.assert_called_once()
        else:
            result = report_service.update_status( report_id=report_id, operator=operator, next_status_value=next_status_value, note=note )

            assert isinstance(result, oracle)
            report_service.report_repository.add_status_entry.assert_called_once()
            report_service.notification_service.notify_status_change.assert_called_once()
            report_service.session.commit.assert_called_once()
            report_service.report_repository.get_by_id.assert_called()
