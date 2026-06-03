from __future__ import annotations

from unittest.mock import Mock
import pytest
 
from participium.core.status_flow import ensure_transition_allowed
from participium.core.exceptions import ValidationError
from participium.models.enums import ReportStatus as rs

"""
Try every permutation of statuses. The only allowed ones are the following:

    Pending Approval -> Pending Approval, Assigned, Rejected
    Assigned -> Assigned, In Progress, Suspended, Resolved
    In Progress -> In Progress, Suspended, Resolved
    Suspended -> Suspended, In Progress, Resolved
    Rejected -> Rejected
    Resolved -> Resolved
"""

@pytest.mark.parametrize(
    "current_status, next_status, expected_exception",
    [
        ( rs.PENDING_APPROVAL, rs.PENDING_APPROVAL, None),
        ( rs.PENDING_APPROVAL, rs.ASSIGNED, None),
        ( rs.PENDING_APPROVAL, rs.IN_PROGRESS, ValidationError),
        ( rs.PENDING_APPROVAL, rs.SUSPENDED, ValidationError),
        ( rs.PENDING_APPROVAL, rs.REJECTED, None),
        ( rs.PENDING_APPROVAL, rs.RESOLVED, ValidationError),
        ( rs.ASSIGNED, rs.PENDING_APPROVAL, ValidationError),
        ( rs.ASSIGNED, rs.ASSIGNED, None),
        ( rs.ASSIGNED, rs.IN_PROGRESS, None),
        ( rs.ASSIGNED, rs.SUSPENDED, None),
        ( rs.ASSIGNED, rs.REJECTED, ValidationError),
        ( rs.ASSIGNED, rs.RESOLVED, None),
        ( rs.IN_PROGRESS, rs.PENDING_APPROVAL, ValidationError),
        ( rs.IN_PROGRESS, rs.ASSIGNED, ValidationError),
        ( rs.IN_PROGRESS, rs.IN_PROGRESS, None),
        ( rs.IN_PROGRESS, rs.SUSPENDED, None),
        ( rs.IN_PROGRESS, rs.REJECTED, ValidationError),
        ( rs.IN_PROGRESS, rs.RESOLVED, None),
        ( rs.SUSPENDED, rs.PENDING_APPROVAL, ValidationError),
        ( rs.SUSPENDED, rs.ASSIGNED, ValidationError),
        ( rs.SUSPENDED, rs.IN_PROGRESS, None),
        ( rs.SUSPENDED, rs.SUSPENDED, None),
        ( rs.SUSPENDED, rs.REJECTED, ValidationError),
        ( rs.SUSPENDED, rs.RESOLVED, None),
        ( rs.REJECTED, rs.PENDING_APPROVAL, ValidationError),
        ( rs.REJECTED, rs.ASSIGNED, ValidationError),
        ( rs.REJECTED, rs.IN_PROGRESS, ValidationError),
        ( rs.REJECTED, rs.SUSPENDED, ValidationError),
        ( rs.REJECTED, rs.REJECTED, None),
        ( rs.REJECTED, rs.RESOLVED, ValidationError),
        ( rs.RESOLVED, rs.PENDING_APPROVAL, ValidationError),
        ( rs.RESOLVED, rs.ASSIGNED, ValidationError),
        ( rs.RESOLVED, rs.IN_PROGRESS, ValidationError),
        ( rs.RESOLVED, rs.SUSPENDED, ValidationError),
        ( rs.RESOLVED, rs.REJECTED, ValidationError),
        ( rs.RESOLVED, rs.RESOLVED, None),
    ]
)
def test_assign_report_wrong_role_and_no_report(current_status, next_status, expected_exception ):
    if expected_exception:
        with pytest.raises(ValidationError):
            ensure_transition_allowed(current_status, next_status)
    else:
            result = ensure_transition_allowed(current_status, next_status)
            assert result == True



