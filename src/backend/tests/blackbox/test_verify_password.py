from __future__ import annotations

import pytest

from participium.core.security import hash_password, verify_password

CORRECT_PASSWORD = "CorrectPassword1!"

@pytest.fixture
def correct_hash():
    return hash_password(CORRECT_PASSWORD)

def test_verify_password_success(correct_hash) -> None:
    result = verify_password(CORRECT_PASSWORD,correct_hash)
    assert result is True


def test_verify_password_failure(correct_hash) -> None:
    password = "WrongPassword"
    result = verify_password(password,correct_hash)
    assert result is False


def test_verify_password_invalid_hash() -> None:
    result = verify_password(CORRECT_PASSWORD, "not_a_valid_hash")
    assert result is False


def test_verify_password_case_sensitive(correct_hash) -> None:
    password = "correctpassword1!"
    result = verify_password(password, correct_hash)
    assert result is False


def test_verify_password_empty_password(correct_hash) -> None:
    result = verify_password("", correct_hash)
    assert result is False
    
def test_verify_password_with_initial_space(correct_hash) -> None:
    result = verify_password(" " + CORRECT_PASSWORD, correct_hash)
    assert result is False


def test_verify_password_with_ending_space(correct_hash) -> None:
    result = verify_password(CORRECT_PASSWORD + " ", correct_hash)
    assert result is False

def test_verify_password_none_password(correct_hash) -> None:
    with pytest.raises(AttributeError):
        verify_password(None, correct_hash)


def test_verify_password_empty_hash() -> None:
    result = verify_password(CORRECT_PASSWORD, "")
    assert result is False