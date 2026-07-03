"""Tests for ReorderTrainingDaysUseCase."""
import uuid

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import ReorderTrainingDaysCommand
from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.application.errors import (
    DomainViolationError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.use_cases.reorder_training_days import ReorderTrainingDaysUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.value_objects import DayOfWeek
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout_with_days(user_id: str = "user-1") -> tuple[Workout, list[str]]:
    days = [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY]
    result = Workout.create(user_id=user_id, name="Test Workout", training_days=days)
    workout = result.unwrap()
    day_entities = workout.get_training_days()
    day_ids = [str(day_entities[d].id.value) for d in days]
    return workout, day_ids


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> ReorderTrainingDaysUseCase:
    return ReorderTrainingDaysUseCase(repo)


async def test_reorder_training_days_success_returns_dto(
    use_case: ReorderTrainingDaysUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout, day_ids = _make_workout_with_days()
    await repo.save(workout)
    # Reverse order
    cmd = ReorderTrainingDaysCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        ordered_day_ids=tuple(reversed(day_ids)),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, WorkoutWithDaysDTO)
    # The days should come back sorted by new order (reversed = Wed, Tue, Mon)
    assert len(dto.training_days) == 3
    assert dto.training_days[0].day_of_week == "WEDNESDAY"
    assert dto.training_days[1].day_of_week == "TUESDAY"
    assert dto.training_days[2].day_of_week == "MONDAY"


async def test_reorder_training_days_workout_not_found(
    use_case: ReorderTrainingDaysUseCase,
) -> None:
    cmd = ReorderTrainingDaysCommand(
        workout_id=str(uuid.uuid4()),
        user_id="user-1",
        ordered_day_ids=(str(uuid.uuid4()),),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_reorder_training_days_unauthorized(
    use_case: ReorderTrainingDaysUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout, day_ids = _make_workout_with_days(user_id="user-1")
    await repo.save(workout)
    cmd = ReorderTrainingDaysCommand(
        workout_id=str(workout.id.value),
        user_id="user-EVIL",
        ordered_day_ids=tuple(day_ids),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


async def test_reorder_training_days_invalid_day_id_returns_not_found(
    use_case: ReorderTrainingDaysUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout, day_ids = _make_workout_with_days()
    await repo.save(workout)
    cmd = ReorderTrainingDaysCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        ordered_day_ids=("not-a-uuid",),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_reorder_training_days_mismatch_returns_domain_violation(
    use_case: ReorderTrainingDaysUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout, day_ids = _make_workout_with_days()
    await repo.save(workout)
    # Only provide one of the three IDs → mismatch
    cmd = ReorderTrainingDaysCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        ordered_day_ids=(day_ids[0],),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
