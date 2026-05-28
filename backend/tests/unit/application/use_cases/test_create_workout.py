"""Tests for CreateWorkoutUseCase — TDD RED phase."""
import pytest
from returns.result import Failure, Success

from backend.src.application.commands import CreateWorkoutCommand
from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.application.errors import InvalidDayOfWeekError, InvalidWorkoutNameError
from backend.src.application.use_cases.create_workout import CreateWorkoutUseCase
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> CreateWorkoutUseCase:
    return CreateWorkoutUseCase(repo)


def test_create_workout_success_returns_dto(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="Push Day",
        description="Chest and triceps",
        training_days=("MONDAY", "THURSDAY"),
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, WorkoutWithDaysDTO)
    assert dto.name == "Push Day"
    assert dto.user_id == "user-1"
    assert len(dto.training_days) == 2


def test_create_workout_empty_name_returns_invalid_name_error(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="",
        description=None,
        training_days=(),
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidWorkoutNameError)


def test_create_workout_whitespace_name_returns_invalid_name_error(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="   ",
        description=None,
        training_days=(),
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidWorkoutNameError)


def test_create_workout_invalid_day_string_returns_invalid_day_error(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="Push Day",
        description=None,
        training_days=("NOT_A_DAY",),
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidDayOfWeekError)


def test_create_workout_with_multiple_days_creates_training_days(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="Full Body",
        description=None,
        training_days=("MONDAY", "WEDNESDAY", "FRIDAY"),
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert len(dto.training_days) == 3
    days = {td.day_of_week for td in dto.training_days}
    assert "MONDAY" in days
    assert "WEDNESDAY" in days
    assert "FRIDAY" in days


def test_create_workout_with_no_days_creates_empty_workout(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="Rest Week",
        description=None,
        training_days=(),
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert len(dto.training_days) == 0
