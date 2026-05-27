"""Tests for domain error hierarchy — FASE 2."""
import pytest

from backend.src.domain.errors.base import DomainError, TrainingDayError, WorkoutExerciseError
from backend.src.domain.errors.training_day_errors import (
    CannotRemoveDayWithExercisesError,
    DayAlreadyInWorkoutError,
    DayNotInWorkoutError,
)
from backend.src.domain.errors.workout_exercise_errors import (
    DuplicateExerciseInDayError,
    ExerciseNotFoundInDayError,
    ReorderMismatchError,
)


# ── Hierarchy isinstance checks ─────────────────────────────────────────────


def test_day_not_in_workout_error_is_training_day_error() -> None:
    err = DayNotInWorkoutError(day="Monday", workout_id="abc-123")
    assert isinstance(err, TrainingDayError)
    assert isinstance(err, DomainError)
    assert isinstance(err, Exception)


def test_day_already_in_workout_error_is_training_day_error() -> None:
    err = DayAlreadyInWorkoutError(day="Tuesday", workout_id="abc-123")
    assert isinstance(err, TrainingDayError)
    assert isinstance(err, DomainError)


def test_cannot_remove_day_with_exercises_is_training_day_error() -> None:
    err = CannotRemoveDayWithExercisesError(day="Wednesday", exercise_count=3)
    assert isinstance(err, TrainingDayError)
    assert isinstance(err, DomainError)


def test_exercise_not_found_in_day_is_workout_exercise_error() -> None:
    err = ExerciseNotFoundInDayError(workout_exercise_id="we-001")
    assert isinstance(err, WorkoutExerciseError)
    assert isinstance(err, DomainError)


def test_duplicate_exercise_in_day_is_workout_exercise_error() -> None:
    err = DuplicateExerciseInDayError(exercise_id="ex-001", day="Monday")
    assert isinstance(err, WorkoutExerciseError)
    assert isinstance(err, DomainError)


def test_reorder_mismatch_is_workout_exercise_error() -> None:
    err = ReorderMismatchError(missing={"we-001"}, extra={"we-002"})
    assert isinstance(err, WorkoutExerciseError)
    assert isinstance(err, DomainError)


# ── Context fields ──────────────────────────────────────────────────────────


def test_day_not_in_workout_error_context() -> None:
    err = DayNotInWorkoutError(day="Monday", workout_id="abc-123")
    assert "Monday" in str(err)
    assert "abc-123" in str(err)


def test_cannot_remove_day_exercise_count_in_message() -> None:
    err = CannotRemoveDayWithExercisesError(day="Friday", exercise_count=5)
    assert "Friday" in str(err)
    assert "5" in str(err)


def test_reorder_mismatch_sets_in_message() -> None:
    err = ReorderMismatchError(missing={"we-001"}, extra={"we-002"})
    assert "we-001" in str(err)
    assert "we-002" in str(err)
