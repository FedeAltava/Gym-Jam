"""Tests for GetWorkoutWithDaysUseCase — TDD RED phase."""
import uuid

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import GetWorkoutWithDaysQuery
from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.application.errors import UnauthorizedError, WorkoutNotFoundError
from backend.src.application.use_cases.get_workout_with_days import GetWorkoutWithDaysUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.value_objects import DayOfWeek
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout(user_id: str = "user-1") -> Workout:
    result = Workout.create(
        user_id=user_id,
        name="Test Workout",
        training_days=[DayOfWeek("MONDAY")],
    )
    return result.unwrap()


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> GetWorkoutWithDaysUseCase:
    return GetWorkoutWithDaysUseCase(repo)


async def test_get_workout_success_returns_dto(
    use_case: GetWorkoutWithDaysUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout()
    await repo.save(workout)
    query = GetWorkoutWithDaysQuery(
        workout_id=str(workout.id.value),
        user_id="user-1",
    )
    result = await use_case.execute(query)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, WorkoutWithDaysDTO)
    assert dto.user_id == "user-1"
    assert len(dto.training_days) == 1


async def test_get_workout_not_found(use_case: GetWorkoutWithDaysUseCase) -> None:
    query = GetWorkoutWithDaysQuery(
        workout_id=str(uuid.uuid4()),
        user_id="user-1",
    )
    result = await use_case.execute(query)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_get_workout_unauthorized(
    use_case: GetWorkoutWithDaysUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(user_id="user-1")
    await repo.save(workout)
    query = GetWorkoutWithDaysQuery(
        workout_id=str(workout.id.value),
        user_id="user-EVIL",
    )
    result = await use_case.execute(query)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)
