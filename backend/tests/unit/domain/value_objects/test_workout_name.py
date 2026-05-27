"""Tests for WorkoutName VO — FASE 1."""
import pytest
from returns.result import Failure, Success

from backend.src.domain.value_objects.workout_name import WorkoutName, WorkoutNameError


def test_workout_name_valid_returns_success() -> None:
    result = WorkoutName.create("Push Day")
    assert isinstance(result, Success)
    assert result.unwrap().value == "Push Day"


def test_workout_name_value_is_preserved() -> None:
    result = WorkoutName.create("Full Body")
    assert isinstance(result, Success)
    assert result.unwrap().value == "Full Body"


@pytest.mark.parametrize("raw,expected_error", [
    ("", WorkoutNameError.EMPTY),
    ("   ", WorkoutNameError.EMPTY),
    ("A", WorkoutNameError.TOO_SHORT),
    ("x" * 101, WorkoutNameError.TOO_LONG),
    (" Push Day", WorkoutNameError.LEADING_TRAILING_WHITESPACE),
    ("Push Day ", WorkoutNameError.LEADING_TRAILING_WHITESPACE),
    ("Push  Day", WorkoutNameError.CONSECUTIVE_SPACES),
])
def test_workout_name_invalid_returns_failure(raw: str, expected_error: WorkoutNameError) -> None:
    result = WorkoutName.create(raw)
    assert isinstance(result, Failure)
    assert result.failure() == expected_error


def test_workout_name_is_immutable() -> None:
    result = WorkoutName.create("Legs")
    assert isinstance(result, Success)
    name = result.unwrap()
    with pytest.raises((AttributeError, TypeError)):
        name.value = "Other"  # type: ignore[misc]
