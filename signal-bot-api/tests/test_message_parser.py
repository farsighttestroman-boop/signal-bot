import pytest
from message_parser import ParsedTarget, parse_message


def test_parse_hostile_keyword() -> None:
    result = parse_message("48.5 39.8 tank")
    assert result is not None
    assert result.lat == pytest.approx(48.5)
    assert result.lon == pytest.approx(39.8)
    assert result.description == "tank"
    assert result.cot_type == "a-h-G-U-C"


def test_parse_hostile_mixed_case() -> None:
    result = parse_message("48.5 39.8 Enemy position")
    assert result is not None
    assert result.cot_type == "a-h-G-U-C"


def test_parse_friendly_keyword() -> None:
    result = parse_message("50.1 30.5 friendly patrol")
    assert result is not None
    assert result.lat == pytest.approx(50.1)
    assert result.lon == pytest.approx(30.5)
    assert result.description == "friendly patrol"
    assert result.cot_type == "a-f-G-U-C"


def test_parse_unknown() -> None:
    result = parse_message("51.0 32.0 checkpoint")
    assert result is not None
    assert result.cot_type == "a-u-G"
    assert result.description == "checkpoint"


def test_parse_negative_coords() -> None:
    result = parse_message("-48.5 -39.8 tank")
    assert result is not None
    assert result.lat == pytest.approx(-48.5)
    assert result.lon == pytest.approx(-39.8)
    assert result.cot_type == "a-h-G-U-C"


def test_parse_invalid_returns_none() -> None:
    assert parse_message("not a valid message") is None


def test_parse_missing_description_returns_none() -> None:
    assert parse_message("48.5 39.8") is None


def test_parse_returns_dataclass() -> None:
    result = parse_message("10.0 20.0 ally")
    assert isinstance(result, ParsedTarget)
    assert result.cot_type == "a-f-G-U-C"
