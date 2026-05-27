"""Tests for DayOfWeek StrEnum — FASE 1."""
import pytest
from backend.src.domain.value_objects.day_of_week import DayOfWeek


def test_day_of_week_has_all_seven_members() -> None:
    members = list(DayOfWeek)
    assert len(members) == 7
    names = {m.name for m in members}
    assert names == {
        "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
        "FRIDAY", "SATURDAY", "SUNDAY",
    }


@pytest.mark.parametrize("member,expected_value", [
    (DayOfWeek.MONDAY, "MONDAY"),
    (DayOfWeek.TUESDAY, "TUESDAY"),
    (DayOfWeek.WEDNESDAY, "WEDNESDAY"),
    (DayOfWeek.THURSDAY, "THURSDAY"),
    (DayOfWeek.FRIDAY, "FRIDAY"),
    (DayOfWeek.SATURDAY, "SATURDAY"),
    (DayOfWeek.SUNDAY, "SUNDAY"),
])
def test_day_of_week_value_equals_name(member: DayOfWeek, expected_value: str) -> None:
    assert member.value == expected_value


def test_day_of_week_invalid_value_raises() -> None:
    with pytest.raises(ValueError):
        DayOfWeek("FUNDAY")


def test_day_of_week_identity() -> None:
    a = DayOfWeek.MONDAY
    b = DayOfWeek.MONDAY
    assert a is b


def test_day_of_week_not_int_comparable() -> None:
    assert DayOfWeek.MONDAY != 0
