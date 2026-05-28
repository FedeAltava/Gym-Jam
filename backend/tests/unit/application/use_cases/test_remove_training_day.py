"""Tests for RemoveTrainingDayUseCase — TDD RED phase."""
import uuid

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import RemoveTrainingDayCommand
from backend.src.application.errors import (
    DomainViolationError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.use_cases.remove_training_day import RemoveTrainingDayUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.value_objects import DayOfWeek
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout(user_id: str = "user-1", days: list[str] | None = None) -> Workout:
    day_list = [DayOfWeek(d) for d in (days or ["MONDAY"])]
    result = Workout.create(user_id=user_id, name="Test Workout", training_days=day_list)
    return result.unwrap()


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> RemoveTrainingDayUseCase:
    return RemoveTrainingDayUseCase(repo)


async def test_remove_training_day_success(
    use_case: RemoveTrainingDayUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(days=["MONDAY"])
    await repo.save(workout)
    cmd = RemoveTrainingDayCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    assert result.unwrap() is None


async def test_remove_training_day_workout_not_found(use_case: RemoveTrainingDayUseCase) -> None:
    cmd = RemoveTrainingDayCommand(
        workout_id=str(uuid.uuid4()),
        user_id="user-1",
        day_of_week="MONDAY",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_remove_training_day_unauthorized(
    use_case: RemoveTrainingDayUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(user_id="user-1", days=["MONDAY"])
    await repo.save(workout)
    cmd = RemoveTrainingDayCommand(
        workout_id=str(workout.id.value),
        user_id="user-EVIL",
        day_of_week="MONDAY",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


async def test_remove_training_day_not_in_workout_returns_domain_violation(
    use_case: RemoveTrainingDayUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(days=["MONDAY"])
    await repo.save(workout)
    cmd = RemoveTrainingDayCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="TUESDAY",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)


async def test_remove_training_day_with_exercises_returns_domain_violation(
    use_case: RemoveTrainingDayUseCase, repo: InMemoryWorkoutRepository
) -> None:
    day = DayOfWeek("MONDAY")
    workout_result = Workout.create(user_id="user-1", name="Test", training_days=[day])
    workout = workout_result.unwrap()
    workout.add_exercise_to_day(day, "ex-abc")
    await repo.save(workout)
    cmd = RemoveTrainingDayCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
