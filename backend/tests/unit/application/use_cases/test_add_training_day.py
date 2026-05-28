"""Tests for AddTrainingDayUseCase — TDD RED phase."""
import uuid

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import AddTrainingDayCommand
from backend.src.application.dtos import TrainingDayDTO
from backend.src.application.errors import (
    DomainViolationError,
    InvalidDayOfWeekError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.use_cases.add_training_day import AddTrainingDayUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.value_objects import DayOfWeek
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout(user_id: str = "user-1", days: list[str] | None = None) -> Workout:
    day_list = [DayOfWeek(d) for d in (days or [])]
    result = Workout.create(user_id=user_id, name="Test Workout", training_days=day_list)
    return result.unwrap()


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> AddTrainingDayUseCase:
    return AddTrainingDayUseCase(repo)


def test_add_training_day_success_returns_dto(
    use_case: AddTrainingDayUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout()
    repo.save(workout)
    cmd = AddTrainingDayCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="TUESDAY",
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, TrainingDayDTO)
    assert dto.day_of_week == "TUESDAY"


def test_add_training_day_workout_not_found(use_case: AddTrainingDayUseCase) -> None:
    cmd = AddTrainingDayCommand(
        workout_id=str(uuid.uuid4()),
        user_id="user-1",
        day_of_week="TUESDAY",
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


def test_add_training_day_unauthorized(
    use_case: AddTrainingDayUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(user_id="user-1")
    repo.save(workout)
    cmd = AddTrainingDayCommand(
        workout_id=str(workout.id.value),
        user_id="user-EVIL",
        day_of_week="TUESDAY",
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


def test_add_training_day_invalid_day_string(
    use_case: AddTrainingDayUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout()
    repo.save(workout)
    cmd = AddTrainingDayCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="FUNDAY",
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidDayOfWeekError)


def test_add_training_day_duplicate_returns_domain_violation(
    use_case: AddTrainingDayUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(days=["MONDAY"])
    repo.save(workout)
    cmd = AddTrainingDayCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
    )
    result = use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
