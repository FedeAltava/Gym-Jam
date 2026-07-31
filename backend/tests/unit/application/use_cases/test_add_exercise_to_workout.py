"""Tests for AddExerciseToWorkoutUseCase — TDD RED phase."""
import uuid
from unittest.mock import AsyncMock

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import AddExerciseToWorkoutCommand
from backend.src.application.dtos import WorkoutExerciseDTO
from backend.src.application.errors import (
    DomainViolationError,
    ExerciseNotFoundError,
    InvalidDayOfWeekError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.use_cases.add_exercise_to_workout import AddExerciseToWorkoutUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.entities.exercise import Exercise
from backend.src.domain.value_objects import DayOfWeek
from backend.tests.unit.application.use_cases.in_memory_exercise_repository import (
    InMemoryExerciseRepository,
)
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
def exercise_repo() -> InMemoryExerciseRepository:
    return InMemoryExerciseRepository(
        [Exercise(id="ex-abc", name="Press de banca", muscle_group="Pecho")]
    )


@pytest.fixture
def use_case(
    repo: InMemoryWorkoutRepository, exercise_repo: InMemoryExerciseRepository
) -> AddExerciseToWorkoutUseCase:
    return AddExerciseToWorkoutUseCase(repo, exercise_repo)


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


async def test_add_exercise_unknown_exercise_returns_not_found(
    use_case: AddExerciseToWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(days=["MONDAY"])
    await repo.save(workout)
    cmd = AddExerciseToWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
        exercise_id="not-in-catalog",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    error = result.failure()
    assert isinstance(error, ExerciseNotFoundError)
    assert error.exercise_id == "not-in-catalog"


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


# ── T1: execute() calls get_by_id_locked, not get_by_id directly ─────────────

async def test_execute_calls_get_by_id_locked_not_get_by_id(
    repo: InMemoryWorkoutRepository, exercise_repo: InMemoryExerciseRepository
) -> None:
    """T1: use case must delegate the workout load to get_by_id_locked.

    We spy on get_by_id_locked to confirm the use case calls the locked
    variant. We do not assert that get_by_id is not called because
    InMemoryWorkoutRepository.get_by_id_locked is a thin alias over
    get_by_id — that internal delegation is an implementation detail of
    the test double, not the use case.
    """
    workout = _make_workout(days=["MONDAY"])
    await repo.save(workout)

    repo.get_by_id_locked = AsyncMock(wraps=repo.get_by_id_locked)  # type: ignore[method-assign]

    use_case = AddExerciseToWorkoutUseCase(repo, exercise_repo)
    cmd = AddExerciseToWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        day_of_week="MONDAY",
        exercise_id="ex-abc",
    )
    result = await use_case.execute(cmd)

    assert isinstance(result, Success)
    repo.get_by_id_locked.assert_awaited_once()


# ── T2: get_by_id_locked returns None → WorkoutNotFoundError ─────────────────

async def test_execute_returns_workout_not_found_when_locked_load_returns_none(
    repo: InMemoryWorkoutRepository, exercise_repo: InMemoryExerciseRepository
) -> None:
    """T2: when get_by_id_locked returns None, execute must return Failure(WorkoutNotFoundError)."""
    repo.get_by_id_locked = AsyncMock(return_value=None)  # type: ignore[method-assign]

    use_case = AddExerciseToWorkoutUseCase(repo, exercise_repo)
    cmd = AddExerciseToWorkoutCommand(
        workout_id=str(uuid.uuid4()),
        user_id="user-1",
        day_of_week="MONDAY",
        exercise_id="ex-abc",
    )
    result = await use_case.execute(cmd)

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)
    repo.get_by_id_locked.assert_awaited_once()
