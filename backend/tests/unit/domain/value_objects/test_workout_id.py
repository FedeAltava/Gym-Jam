"""Tests for WorkoutId VO — FASE 1."""
import uuid

import pytest
from returns.result import Failure, Success

from backend.src.domain.value_objects.workout_id import WorkoutId, WorkoutIdError

_NIL_UUID = "00000000-0000-0000-0000-000000000000"


def test_workout_id_generate_returns_valid_id() -> None:
    result = WorkoutId.generate()
    assert isinstance(result, WorkoutId)
    assert isinstance(result.value, uuid.UUID)
    assert result.value.version == 4


def test_workout_id_from_valid_string_returns_success() -> None:
    valid = str(uuid.uuid4())
    result = WorkoutId.from_string(valid)
    assert isinstance(result, Success)
    assert str(result.unwrap().value) == valid


def test_workout_id_from_invalid_string_returns_failure() -> None:
    result = WorkoutId.from_string("not-a-uuid")
    assert isinstance(result, Failure)
    assert result.failure() == WorkoutIdError.INVALID_FORMAT


def test_workout_id_nil_uuid_returns_failure() -> None:
    result = WorkoutId.from_string(_NIL_UUID)
    assert isinstance(result, Failure)
    assert result.failure() == WorkoutIdError.NIL_UUID


def test_workout_id_is_immutable() -> None:
    wid = WorkoutId.generate()
    with pytest.raises((AttributeError, TypeError)):
        wid.value = uuid.uuid4()  # type: ignore[misc]
