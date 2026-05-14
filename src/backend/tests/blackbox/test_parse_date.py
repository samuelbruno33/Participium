from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from participium.core.utils import parse_date


# TC-01: None input returns None.
def test_parse_date_none_returns_none() -> None:
    assert parse_date(None) is None


# TC-02: Empty string returns None (falsy short-circuit before fromisoformat).
def test_parse_date_empty_string_returns_none() -> None:
    assert parse_date("") is None


# TC-03: ISO date-only string is parsed as midnight datetime.
def test_parse_date_iso_date_only() -> None:
    result = parse_date("2026-05-14")

    assert isinstance(result, datetime)
    assert result == datetime(2026, 5, 14, 0, 0, 0)
    assert result.tzinfo is None


# TC-04: ISO datetime string without timezone is parsed as naive datetime.
def test_parse_date_iso_datetime_no_timezone() -> None:
    result = parse_date("2026-05-14T10:30:45")

    assert isinstance(result, datetime)
    assert result == datetime(2026, 5, 14, 10, 30, 45)
    assert result.tzinfo is None


# TC-05: ISO datetime string with timezone offset preserves tzinfo.
def test_parse_date_iso_datetime_with_timezone() -> None:
    result = parse_date("2026-05-14T10:30:00+02:00")

    assert isinstance(result, datetime)
    assert result.tzinfo is not None
    assert result.utcoffset() == timedelta(hours=2)
    assert result == datetime(2026, 5, 14, 10, 30, 0, tzinfo=timezone(timedelta(hours=2)))


# TC-06: Non-ISO format raises ValueError.
def test_parse_date_invalid_format_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse_date("14/05/2026")


# TC-07: Out-of-range calendar values raise ValueError.
def test_parse_date_out_of_range_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse_date("2026-13-50")


# TC-08: Whitespace-only string is truthy, so fromisoformat is called and raises ValueError.
def test_parse_date_whitespace_only_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse_date(" ")


# TC-09: Non-string truthy input causes datetime.fromisoformat to raise TypeError.
def test_parse_date_non_string_input_raises_type_error() -> None:
    with pytest.raises(TypeError):
        parse_date(20260514)  # type: ignore[arg-type]
