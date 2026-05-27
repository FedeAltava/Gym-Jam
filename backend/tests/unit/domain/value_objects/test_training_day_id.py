"""Tests for TrainingDayId VO — FASE 2."""
import uuid

import pytest
from returns.result import Failure, Success

from backend.src.domain.value_objects.training_day_id import TrainingDayId, TrainingDayIdError

_NIL_UUID = "00000000-0000-0000-0000-000000000000"


def test_training_day_id_generate_returns_valid_id() -> None:
    result = TrainingDayId.generate()
    assert isinstance(result, TrainingDayId)
    assert isinstance(result.value, uuid.UUID)
    assert result.value.version == 4


def test_training_day_id_from_valid_string_returns_success() -> None:
    valid = str(uuid.uuid4())
    result = TrainingDayId.from_string(valid)
    assert isinstance(result, Success)
    assert str(result.unwrap().value) == valid


def test_training_day_id_from_invalid_string_returns_failure() -> None:
    result = TrainingDayId.from_string("not-a-uuid")
    assert isinstance(result, Failure)
    assert result.failure() == TrainingDayIdError.INVALID_FORMAT


def test_training_day_id_nil_uuid_returns_failure() -> None:
    result = TrainingDayId.from_string(_NIL_UUID)
    assert isinstance(result, Failure)
    assert result.failure() == TrainingDayIdError.NIL_UUID


def test_training_day_id_is_immutable() -> None:
    tid = TrainingDayId.generate()
    with pytest.raises((AttributeError, TypeError)):
        tid.value = uuid.uuid4()  # type: ignore[misc]
