"""Unit tests for DietPlanId value object — RED phase."""
from __future__ import annotations

import uuid

import pytest
from returns.result import Failure, Success

from backend.src.domain.value_objects.diet_plan_id import DietPlanId, DietPlanIdError

_NIL_UUID = "00000000-0000-0000-0000-000000000000"


def test_diet_plan_id_generate_returns_valid_uuid4() -> None:
    result = DietPlanId.generate()
    assert isinstance(result, DietPlanId)
    assert isinstance(result.value, uuid.UUID)
    assert result.value.version == 4


def test_diet_plan_id_from_valid_string_returns_success() -> None:
    valid = str(uuid.uuid4())
    result = DietPlanId.from_string(valid)
    assert isinstance(result, Success)
    assert str(result.unwrap().value) == valid


def test_diet_plan_id_from_invalid_string_returns_failure() -> None:
    result = DietPlanId.from_string("not-a-uuid")
    assert isinstance(result, Failure)
    assert result.failure() == DietPlanIdError.INVALID_FORMAT


def test_diet_plan_id_nil_uuid_returns_failure() -> None:
    result = DietPlanId.from_string(_NIL_UUID)
    assert isinstance(result, Failure)
    assert result.failure() == DietPlanIdError.NIL_UUID


def test_diet_plan_id_is_frozen() -> None:
    did = DietPlanId.generate()
    with pytest.raises((AttributeError, TypeError)):
        did.value = uuid.uuid4()  # type: ignore[misc]


def test_diet_plan_id_equality_by_value() -> None:
    raw = str(uuid.uuid4())
    id1 = DietPlanId.from_string(raw).unwrap()
    id2 = DietPlanId.from_string(raw).unwrap()
    assert id1 == id2
