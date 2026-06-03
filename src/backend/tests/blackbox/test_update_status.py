from __future__ import annotations

import pytest
from unittest.mock import Mock

from participium.core import NotFoundError, AuthorizationError, ValidationError

from participium.models.user import User
from participium.models.report import Report
from participium.models.enums import Role, ReportStatus
from participium.services.report_service import ReportService


user_admin = User(
    id = 1,
    role = Role.ADMIN,
)

user_operator_valid = User(
    id = 1,
    role = Role.OPERATOR,
    category_id = 10
)

user_operator_invalid = User(
    id = 1,
    role = Role.OPERATOR,
    category_id = 11
)

user_citizen = User(
    id = 1,
    role = Role.CITIZEN,
    category_id = 10
)



@pytest.fixture()
def mock_service():
    session = Mock()
    category_repository = Mock()
    storage_service = Mock()
    notification_service = Mock()
    
    # define a mock report_repository with only a report
    report_repository = Mock()
    def mock_get_by_id(id):
        if id == 10:
            return Report( id = 10, status = ReportStatus.PENDING_APPROVAL, category_id = 10 )
        else:
            raise NotFoundError("Report not found.")
    report_repository.get_by_id.side_effect = mock_get_by_id
    
    service = ReportService(
        session,
        report_repository,
        category_repository,
        storage_service,
        notification_service,
    )
    return service


@pytest.mark.parametrize(
    "report_id, operator, next_status_value, note, expected_exception, oracle",
    [
         # valid test cases
         ( 10, user_admin, ReportStatus.ASSIGNED, "valid note", None, Report ),
         ( 10, user_operator_valid, ReportStatus.ASSIGNED, "valid note", None, Report ),
         ( 10, user_admin, ReportStatus.ASSIGNED, None, None, Report ),
         ( 10, user_operator_valid, ReportStatus.ASSIGNED, None, None, Report ),
         # invalid test cases
         ( 11, user_admin, ReportStatus.ASSIGNED, "valid note", NotFoundError, None ),
         ( None, user_admin, ReportStatus.ASSIGNED, "valid note", NotFoundError, None ),
         ( 10, user_operator_invalid, ReportStatus.ASSIGNED, "valid note", AuthorizationError, None ),
         ( 10, user_citizen, ReportStatus.ASSIGNED, "valid note", AuthorizationError, None ),
         ( 10, user_admin, ReportStatus.SUSPENDED, "valid note", ValidationError, None ),
         ( 10, user_admin, ReportStatus.SUSPENDED, "valid note", ValidationError, None ),
         ( 10, user_admin, ReportStatus.REJECTED, None, ValidationError, None ),
    ]    
)
def test_suite_update_status(mock_service, report_id, operator, next_status_value, note, expected_exception, oracle):
    service = mock_service
    
    if expected_exception:
        with pytest.raises(expected_exception):
            service.update_status(report_id, operator, next_status_value, note)
    else:
        result = service.update_status(report_id, operator, next_status_value, note)
        assert isinstance(result, oracle)
        service.report_repository.add_status_entry.assert_called_once()
        service.notification_service.notify_status_change.assert_called_once()
        service.session.commit.assert_called_once()
        service.report_repository.get_by_id.assert_called_with(report_id)

    