"""Tests for AddExerciseToWorkoutUseCase — TDD RED phase."""
import uuid

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import AddExerciseToWorkoutCommand
from backend.src.application.dtos import WorkoutExerciseDTO
from backend.src.application.errors import (
    DomainViolationError,
    InvalidDayOfWeekError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.use_cases.add_exercise_to_workout import AddExerciseToWorkoutUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.value_objects import DayOfWeek, WorkoutId
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
def use_case(repo: InMemoryWorkoutRepository) -> AddExerciseToWorkoutUseCase:
    return AddExerciseToWorkoutUseCase(repo)


async def test_add_exercise_success_returns_dto(
    use_case: AddExerciseToWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(days=["MONDAY"])
    await repo.save(workout)
    cmd = AddExerciseToWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
        exercise_id="ex-abc",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, WorkoutExerciseDTO)
    assert dto.exercise_id == "ex-abc"
    assert dto.day == "MONDAY"


async def test_add_exercise_workout_not_found_returns_error(use_case: AddExerciseToWorkoutUseCase) -> None:
    cmd = AddExerciseToWorkoutCommand(
        workout_id=str(uuid.uuid4()),
        user_id="user-1",
        day_of_week="MONDAY",
        exercise_id="ex-abc",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_add_exercise_unauthorized_returns_error(
    use_case: AddExerciseToWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(user_id="user-1", days=["MONDAY"])
    await repo.save(workout)
    cmd = AddExerciseToWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-EVIL",
        day_of_week="MONDAY",
        exercise_id="ex-abc",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


async def test_add_exercise_invalid_day_returns_error(
    use_case: AddExerciseToWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(days=["MONDAY"])
    await repo.save(workout)
    cmd = AddExerciseToWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="FUNDAY",
        exercise_id="ex-abc",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidDayOfWeekError)


async def test_add_exercise_day_not_in_workout_returns_domain_violation(
    use_case: AddExerciseToWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(days=["MONDAY"])
    await repo.save(workout)
    cmd = AddExerciseToWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="TUESDAY",
        exercise_id="ex-abc",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)


async def test_add_exercise_duplicate_returns_domain_violation(
    use_case: AddExerciseToWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(days=["MONDAY"])
    await repo.save(workout)
    cmd = AddExerciseToWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
        exercise_id="ex-abc",
    )
    # First add succeeds
    await use_case.execute(cmd)
    # Second add is duplicate
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
