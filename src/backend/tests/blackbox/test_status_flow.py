from __future__ import annotations

import pytest
from participium.core.exceptions import ValidationError
from participium.core.status_flow import ensure_transition_allowed

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