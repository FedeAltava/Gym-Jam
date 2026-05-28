"""Tests for application validators."""
from returns.result import Failure, Success

from backend.src.application.errors import InvalidDayOfWeekError, InvalidWorkoutNameError
from backend.src.application.validators import CreateWorkoutValidator, DayOfWeekValidator
from backend.src.domain.value_objects import DayOfWeek


def test_validate_valid_day_of_week_returns_success() -> None:
    result = DayOfWeekValidator.validate("monday")
    assert isinstance(result, Success)
    assert result.unwrap() == DayOfWeek.MONDAY


def test_validate_invalid_day_of_week_returns_failure() -> None:
    result = DayOfWeekValidator.validate("funday")
    assert isinstance(result, Failure)
    error = result.failure()
    assert isinstance(error, InvalidDayOfWeekError)
    assert error.value == "funday"


def test_validate_uppercase_day_of_week_returns_success() -> None:
    result = DayOfWeekValidator.validate("FRIDAY")
    assert isinstance(result, Success)
    assert result.unwrap() == DayOfWeek.FRIDAY


def test_validate_mixed_case_day_of_week_returns_success() -> None:
    result = DayOfWeekValidator.validate("Wednesday")
    assert isinstance(result, Success)
    assert result.unwrap() == DayOfWeek.WEDNESDAY


def test_create_workout_validator_valid_name_returns_success() -> None:
    result = CreateWorkoutValidator.validate_name("My Workout")
    assert isinstance(result, Success)
    assert result.unwrap() == "My Workout"


def test_create_workout_validator_empty_name_returns_failure() -> None:
    result = CreateWorkoutValidator.validate_name("")
    assert isinstance(result, Failure)
    error = result.failure()
    assert isinstance(error, InvalidWorkoutNameError)
    assert error.reason == "EMPTY"
