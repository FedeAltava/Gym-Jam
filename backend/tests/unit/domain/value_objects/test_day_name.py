"""Tests for DayName VO — FASE 1."""
import pytest
from backend.src.domain.value_objects.day_of_week import DayOfWeek
from backend.src.domain.value_objects.day_name import DayName


@pytest.mark.parametrize("day,expected", [
    (DayOfWeek.MONDAY, "Lunes"),
    (DayOfWeek.TUESDAY, "Martes"),
    (DayOfWeek.WEDNESDAY, "Miércoles"),
    (DayOfWeek.THURSDAY, "Jueves"),
    (DayOfWeek.FRIDAY, "Viernes"),
    (DayOfWeek.SATURDAY, "Sábado"),
    (DayOfWeek.SUNDAY, "Domingo"),
])
def test_day_name_for_day_spanish(day: DayOfWeek, expected: str) -> None:
    result = DayName.for_day(day)
    assert result.value == expected


def test_day_name_is_immutable() -> None:
    name = DayName.for_day(DayOfWeek.MONDAY)
    with pytest.raises((AttributeError, TypeError)):
        name.value = "Otro"  # type: ignore[misc]


def test_day_name_equality_by_value() -> None:
    a = DayName(value="Lunes")
    b = DayName(value="Lunes")
    assert a == b


def test_day_name_rejects_empty_string() -> None:
    with pytest.raises(ValueError):
        DayName(value="")


def test_day_name_rejects_whitespace_only() -> None:
    with pytest.raises(ValueError):
        DayName(value="   ")
