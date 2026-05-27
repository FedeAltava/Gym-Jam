"""Tests for WorkoutExerciseId VO — FASE 1."""
import uuid

import pytest
from returns.result import Failure, Success

from backend.src.domain.value_objects.workout_exercise_id import (
    WorkoutExerciseId,
    WorkoutExerciseIdError,
)
from backend.src.domain.value_objects.workout_id import WorkoutId

_NIL_UUID = "00000000-0000-0000-0000-000000000000"


def test_workout_exercise_id_generate_returns_valid_id() -> None:
    result = WorkoutExerciseId.generate()
    assert isinstance(result, WorkoutExerciseId)
    assert isinstance(result.value, uuid.UUID)
    assert result.value.version == 4


def test_workout_exercise_id_from_valid_string_returns_success() -> None:
    valid = str(uuid.uuid4())
    result = WorkoutExerciseId.from_string(valid)
    assert isinstance(result, Success)
    assert str(result.unwrap().value) == valid


def test_workout_exercise_id_from_invalid_string_returns_failure() -> None:
    result = WorkoutExerciseId.from_string("not-a-uuid")
    assert isinstance(result, Failure)
    assert result.failure() == WorkoutExerciseIdError.INVALID_FORMAT


def test_workout_exercise_id_nil_uuid_returns_failure() -> None:
    result = WorkoutExerciseId.from_string(_NIL_UUID)
    assert isinstance(result, Failure)
    assert result.failure() == WorkoutExerciseIdError.NIL_UUID


def test_workout_exercise_id_is_not_workout_id() -> None:
    exercise_id = WorkoutExerciseId.generate()
    assert not isinstance(exercise_id, WorkoutId)
