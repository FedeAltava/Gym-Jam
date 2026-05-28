"""Tests for ReorderExercisesUseCase — TDD RED phase."""
import uuid

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import ReorderExercisesCommand
from backend.src.application.dtos import TrainingDayDTO
from backend.src.application.errors import (
    DomainViolationError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.use_cases.reorder_exercises import ReorderExercisesUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.value_objects import DayOfWeek
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout_with_exercises(user_id: str = "user-1") -> tuple[Workout, list[str]]:
    day = DayOfWeek("MONDAY")
    result = Workout.create(user_id=user_id, name="Test Workout", training_days=[day])
    workout = result.unwrap()
    ex1 = workout.add_exercise_to_day(day, "ex-1")
    ex2 = workout.add_exercise_to_day(day, "ex-2")
    return workout, [str(ex1.id.value), str(ex2.id.value)]


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> ReorderExercisesUseCase:
    return ReorderExercisesUseCase(repo)


def test_reorder_exercises_success_returns_dto(
    use_case: ReorderExercisesUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout, exercise_ids = _make_workout_with_exercises()
    repo.save(workout)
    # Reverse order
    cmd = ReorderExercisesCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
        ordered_exercise_ids=tuple(reversed(exercise_ids)),
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, TrainingDayDTO)
    assert dto.day_of_week == "MONDAY"
    assert len(dto.exercises) == 2


def test_reorder_exercises_workout_not_found(use_case: ReorderExercisesUseCase) -> None:
    cmd = ReorderExercisesCommand(
        workout_id=str(uuid.uuid4()),
        user_id="user-1",
        day_of_week="MONDAY",
        ordered_exercise_ids=(str(uuid.uuid4()),),
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


def test_reorder_exercises_unauthorized(
    use_case: ReorderExercisesUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout, exercise_ids = _make_workout_with_exercises(user_id="user-1")
    repo.save(workout)
    cmd = ReorderExercisesCommand(
        workout_id=str(workout.id.value),
        user_id="user-EVIL",
        day_of_week="MONDAY",
        ordered_exercise_ids=tuple(exercise_ids),
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


def test_reorder_exercises_mismatch_returns_domain_violation(
    use_case: ReorderExercisesUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout, exercise_ids = _make_workout_with_exercises()
    repo.save(workout)
    # Only provide one of the two IDs → mismatch
    cmd = ReorderExercisesCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
        ordered_exercise_ids=(exercise_ids[0],),
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
