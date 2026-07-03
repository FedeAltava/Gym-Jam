"""Unit tests for StartWorkoutSessionUseCase."""
from __future__ import annotations

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import StartWorkoutSessionCommand
from backend.src.application.dtos import WorkoutSessionDTO
from backend.src.application.errors import UnauthorizedError, WorkoutNotFoundError
from backend.src.application.use_cases.start_workout_session import StartWorkoutSessionUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.value_objects import DayOfWeek, TrainingDayId, WorkoutId
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout(user_id: str = "user-1", days: list[str] | None = None) -> Workout:
    day_list = [DayOfWeek(d) for d in (days or ["MONDAY"])]
    return Workout.create(user_id=user_id, name="Test Workout", training_days=day_list).unwrap()


@pytest.fixture
def workout_repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def use_case(workout_repo: InMemoryWorkoutRepository, session_repo: InMemorySessionRepository) -> StartWorkoutSessionUseCase:
    return StartWorkoutSessionUseCase(workout_repo, session_repo)


async def test_start_session_happy_path(
    use_case: StartWorkoutSessionUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    workout = _make_workout(days=["MONDAY"])
    await workout_repo.save(workout)
    # Retrieve actual training day id
    days = workout.get_training_days()
    day_id = str(list(days.values())[0].id.value)

    cmd = StartWorkoutSessionCommand(
        user_id="user-1",
        workout_id=str(workout.id.value),
        training_day_id=day_id,
    )
    result = await use_case.execute(cmd)

    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, WorkoutSessionDTO)
    assert dto.user_id == "user-1"
    assert dto.workout_id == str(workout.id.value)
    assert dto.training_day_id == day_id
    assert dto.status == "in_progress"
    assert dto.completed_at is None


async def test_start_session_saves_to_repo(
    use_case: StartWorkoutSessionUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    workout = _make_workout(days=["MONDAY"])
    await workout_repo.save(workout)
    day_id = str(list(workout.get_training_days().values())[0].id.value)

    cmd = StartWorkoutSessionCommand(
        user_id="user-1",
        workout_id=str(workout.id.value),
        training_day_id=day_id,
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    session_id = result.unwrap().id
    loaded = await session_repo.get_by_id(
        __import__(
            "backend.src.domain.value_objects.workout_session_id",
            fromlist=["WorkoutSessionId"],
        ).WorkoutSessionId.from_string(session_id).unwrap()
    )
    assert loaded is not None


async def test_start_session_workout_not_found(
    use_case: StartWorkoutSessionUseCase,
) -> None:
    cmd = StartWorkoutSessionCommand(
        user_id="user-1",
        workout_id=str(WorkoutId.generate().value),
        training_day_id=str(TrainingDayId.generate().value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_start_session_invalid_workout_id(
    use_case: StartWorkoutSessionUseCase,
) -> None:
    cmd = StartWorkoutSessionCommand(
        user_id="user-1",
        workout_id="not-a-uuid",
        training_day_id=str(TrainingDayId.generate().value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_start_session_unauthorized(
    use_case: StartWorkoutSessionUseCase,
    workout_repo: InMemoryWorkoutRepository,
) -> None:
    workout = _make_workout(user_id="owner", days=["MONDAY"])
    await workout_repo.save(workout)
    day_id = str(list(workout.get_training_days().values())[0].id.value)

    cmd = StartWorkoutSessionCommand(
        user_id="attacker",
        workout_id=str(workout.id.value),
        training_day_id=day_id,
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


async def test_start_session_training_day_not_in_workout(
    use_case: StartWorkoutSessionUseCase,
    workout_repo: InMemoryWorkoutRepository,
) -> None:
    workout = _make_workout(days=["MONDAY"])
    await workout_repo.save(workout)
    other_day_id = str(TrainingDayId.generate().value)

    cmd = StartWorkoutSessionCommand(
        user_id="user-1",
        workout_id=str(workout.id.value),
        training_day_id=other_day_id,
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_start_session_multiple_sessions_same_day_allowed(
    use_case: StartWorkoutSessionUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    workout = _make_workout(days=["TUESDAY"])
    await workout_repo.save(workout)
    day_id = str(list(workout.get_training_days().values())[0].id.value)

    cmd = StartWorkoutSessionCommand(
        user_id="user-1",
        workout_id=str(workout.id.value),
        training_day_id=day_id,
    )
    r1 = await use_case.execute(cmd)
    r2 = await use_case.execute(cmd)

    assert isinstance(r1, Success)
    assert isinstance(r2, Success)
    assert r1.unwrap().id != r2.unwrap().id
