"""Tests for ApplicationErrors — RED phase first."""
import pytest

from backend.src.application.errors import (
    ApplicationError,
    DomainViolationError,
    InvalidDayOfWeekError,
    InvalidWorkoutNameError,
    UnauthorizedError,
    WorkoutNotFoundError,
)


def test_workout_not_found_error_stores_workout_id() -> None:
    error = WorkoutNotFoundError(workout_id="abc-123")
    assert error.workout_id == "abc-123"
    assert isinstance(error, ApplicationError)


def test_unauthorized_error_stores_user_and_workout_id() -> None:
    error = UnauthorizedError(user_id="user-1", workout_id="workout-1")
    assert error.user_id == "user-1"
    assert error.workout_id == "workout-1"
    assert isinstance(error, ApplicationError)


def test_invalid_day_of_week_error_stores_value() -> None:
    error = InvalidDayOfWeekError(value="FUNDAY")
    assert error.value == "FUNDAY"
    assert isinstance(error, ApplicationError)


def test_invalid_workout_name_error_stores_reason() -> None:
    error = InvalidWorkoutNameError(reason="Name too short")
    assert error.reason == "Name too short"
    assert isinstance(error, ApplicationError)


def test_domain_violation_error_wraps_original_exception() -> None:
    original = ValueError("domain constraint violated")
    error = DomainViolationError(domain_error=original, message="Something went wrong")
    assert error.domain_error is original
    assert error.message == "Something went wrong"
    assert isinstance(error, ApplicationError)


def test_errors_are_frozen_dataclasses() -> None:
    error = WorkoutNotFoundError(workout_id="xyz")
    with pytest.raises(Exception):
        error.workout_id = "other"  # type: ignore[misc]
