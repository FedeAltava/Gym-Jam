"""Tests for RemoveExerciseFromWorkoutUseCase — TDD RED phase."""
import uuid

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import RemoveExerciseFromWorkoutCommand
from backend.src.application.errors import (
    DomainViolationError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.use_cases.remove_exercise_from_workout import (
    RemoveExerciseFromWorkoutUseCase,
)
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.value_objects import DayOfWeek, WorkoutId
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout_with_exercise(
    user_id: str = "user-1",
) -> tuple[Workout, str]:
    day = DayOfWeek("MONDAY")
    result = Workout.create(user_id=user_id, name="Test Workout", training_days=[day])
    workout = result.unwrap()
    exercise = workout.add_exercise_to_day(day, "ex-abc")
    return workout, str(exercise.id.value)


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> RemoveExerciseFromWorkoutUseCase:
    return RemoveExerciseFromWorkoutUseCase(repo)


async def test_remove_exercise_success_returns_none(
    use_case: RemoveExerciseFromWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout, exercise_id = _make_workout_with_exercise()
    await repo.save(workout)
    cmd = RemoveExerciseFromWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
        workout_exercise_id=exercise_id,
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    assert result.unwrap() is None


async def test_remove_exercise_workout_not_found(use_case: RemoveExerciseFromWorkoutUseCase) -> None:
    cmd = RemoveExerciseFromWorkoutCommand(
        workout_id=str(uuid.uuid4()),
        user_id="user-1",
        day_of_week="MONDAY",
        workout_exercise_id=str(uuid.uuid4()),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_remove_exercise_unauthorized(
    use_case: RemoveExerciseFromWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout, exercise_id = _make_workout_with_exercise(user_id="user-1")
    await repo.save(workout)
    cmd = RemoveExerciseFromWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-EVIL",
        day_of_week="MONDAY",
        workout_exercise_id=exercise_id,
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


async def test_remove_exercise_not_in_day_returns_domain_violation(
    use_case: RemoveExerciseFromWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    day = DayOfWeek("MONDAY")
    workout_result = Workout.create(user_id="user-1", name="Test Workout", training_days=[day])
    workout = workout_result.unwrap()
    await repo.save(workout)
    cmd = RemoveExerciseFromWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
        workout_exercise_id=str(uuid.uuid4()),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
