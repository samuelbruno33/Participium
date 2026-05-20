from __future__ import annotations

import pytest
from participium.core.exceptions import ValidationError
from participium.core.status_flow import ensure_transition_allowed
from participium.models.enums import ReportStatus

''' # Black-Box test without uploaded code function
# All valid transitions explicitly stated in the requirements
VALID_TRANSITIONS = [
    # From Pending Approval
    ("Pending Approval", "Pending Approval"),
    ("Pending Approval", "Assigned"),
    ("Pending Approval", "Rejected"),
    # From Assigned
    ("Assigned", "Assigned"),
    ("Assigned", "In Progress"),
    ("Assigned", "Suspended"),
    ("Assigned", "Resolved"),
    # From In Progress
    ("In Progress", "In Progress"),
    ("In Progress", "Suspended"),
    ("In Progress", "Resolved"),
    # From Suspended
    ("Suspended", "Suspended"),
    ("Suspended", "In Progress"),
    ("Suspended", "Resolved"),
    # Terminal states self-transitions
    ("Rejected", "Rejected"),
    ("Resolved", "Resolved")
]


@pytest.mark.parametrize("current_status, next_status", VALID_TRANSITIONS)
def test_valid_transitions(current_status, next_status):
    # Execution
    result = ensure_transition_allowed(current_status, next_status)

    # Assertion
    assert result is True


# Invalid transitions (backward flows, skipping states)
INVALID_TRANSITIONS = [
    # Skipping states forwards from Pending Approval
    ("Pending Approval", "In Progress"),
    ("Pending Approval", "Suspended"),
    ("Pending Approval", "Resolved"),

    # Backward flows to Pending Approval
    ("Assigned", "Pending Approval"),
    ("In Progress", "Pending Approval"),
    ("Suspended", "Pending Approval"),

    # Backward flows to Assigned
    ("In Progress", "Assigned"),
    ("Suspended", "Assigned"),

    # Invalid flows to Rejected (only allowed from Pending Approval)
    ("Assigned", "Rejected"),
    ("In Progress", "Rejected"),
    ("Suspended", "Rejected"),

    # Escaping terminal state: Resolved
    ("Resolved", "Pending Approval"),
    ("Resolved", "Assigned"),
    ("Resolved", "In Progress"),
    ("Resolved", "Suspended"),
    ("Resolved", "Rejected"),

    # Escaping terminal state: Rejected
    ("Rejected", "Pending Approval"),
    ("Rejected", "Assigned"),
    ("Rejected", "In Progress"),
    ("Rejected", "Suspended"),
    ("Rejected", "Resolved")
]


@pytest.mark.parametrize("current_status, next_status", INVALID_TRANSITIONS)
def test_invalid_transitions(current_status, next_status):
    with pytest.raises(ValidationError):
        ensure_transition_allowed(current_status, next_status)
'''

# All valid transitions using Enum types expected by the real implementation
VALID_TRANSITIONS = [
    # From Pending Approval
    (ReportStatus.PENDING_APPROVAL, ReportStatus.PENDING_APPROVAL),
    (ReportStatus.PENDING_APPROVAL, ReportStatus.ASSIGNED),
    (ReportStatus.PENDING_APPROVAL, ReportStatus.REJECTED),
    # From Assigned
    (ReportStatus.ASSIGNED, ReportStatus.ASSIGNED),
    (ReportStatus.ASSIGNED, ReportStatus.IN_PROGRESS),
    (ReportStatus.ASSIGNED, ReportStatus.SUSPENDED),
    (ReportStatus.ASSIGNED, ReportStatus.RESOLVED),
    # From In Progress
    (ReportStatus.IN_PROGRESS, ReportStatus.IN_PROGRESS),
    (ReportStatus.IN_PROGRESS, ReportStatus.SUSPENDED),
    (ReportStatus.IN_PROGRESS, ReportStatus.RESOLVED),
    # From Suspended
    (ReportStatus.SUSPENDED, ReportStatus.SUSPENDED),
    (ReportStatus.SUSPENDED, ReportStatus.IN_PROGRESS),
    (ReportStatus.SUSPENDED, ReportStatus.RESOLVED),
    # Terminal states self-transitions
    (ReportStatus.REJECTED, ReportStatus.REJECTED),
    (ReportStatus.RESOLVED, ReportStatus.RESOLVED)
]

@pytest.mark.parametrize("current_status, next_status", VALID_TRANSITIONS)
def test_valid_transitions(current_status, next_status):
    # Execution
    result = ensure_transition_allowed(current_status, next_status)

    # Assertion
    assert result is True


# Invalid transitions using Enum types
INVALID_TRANSITIONS = [
    # Skipping states forwards from Pending Approval
    (ReportStatus.PENDING_APPROVAL, ReportStatus.IN_PROGRESS),
    (ReportStatus.PENDING_APPROVAL, ReportStatus.SUSPENDED),
    (ReportStatus.PENDING_APPROVAL, ReportStatus.RESOLVED),

    # Backward flows to Pending Approval
    (ReportStatus.ASSIGNED, ReportStatus.PENDING_APPROVAL),
    (ReportStatus.IN_PROGRESS, ReportStatus.PENDING_APPROVAL),
    (ReportStatus.SUSPENDED, ReportStatus.PENDING_APPROVAL),

    # Backward flows to Assigned
    (ReportStatus.IN_PROGRESS, ReportStatus.ASSIGNED),
    (ReportStatus.SUSPENDED, ReportStatus.ASSIGNED),

    # Invalid flows to Rejected (only allowed from Pending Approval)
    (ReportStatus.ASSIGNED, ReportStatus.REJECTED),
    (ReportStatus.IN_PROGRESS, ReportStatus.REJECTED),
    (ReportStatus.SUSPENDED, ReportStatus.REJECTED),

    # Escaping terminal state: Resolved
    (ReportStatus.RESOLVED, ReportStatus.PENDING_APPROVAL),
    (ReportStatus.RESOLVED, ReportStatus.ASSIGNED),
    (ReportStatus.RESOLVED, ReportStatus.IN_PROGRESS),
    (ReportStatus.RESOLVED, ReportStatus.SUSPENDED),
    (ReportStatus.RESOLVED, ReportStatus.REJECTED),

    # Escaping terminal state: Rejected
    (ReportStatus.REJECTED, ReportStatus.PENDING_APPROVAL),
    (ReportStatus.REJECTED, ReportStatus.ASSIGNED),
    (ReportStatus.REJECTED, ReportStatus.IN_PROGRESS),
    (ReportStatus.REJECTED, ReportStatus.SUSPENDED),
    (ReportStatus.REJECTED, ReportStatus.RESOLVED)
]

@pytest.mark.parametrize("current_status, next_status", INVALID_TRANSITIONS)
def test_invalid_transitions(current_status, next_status):
    with pytest.raises(ValidationError):
        ensure_transition_allowed(current_status, next_status)