"""Unit tests for GetSessionsForDayUseCase."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import GetSessionsForDayCommand
from backend.src.application.dtos import WorkoutSessionDTO
from backend.src.application.errors import UnauthorizedError, WorkoutNotFoundError
from backend.src.application.use_cases.get_sessions_for_day import GetSessionsForDayUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import DayOfWeek, TrainingDayId, WorkoutId, WorkoutSessionId
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout(user_id: str = "user-1", days: list[str] | None = None) -> Workout:
    day_list = [DayOfWeek(d) for d in (days or ["MONDAY"])]
    return Workout.create(user_id=user_id, name="Test Workout", training_days=day_list).unwrap()


def _make_session(
    user_id: str = "user-1",
    workout_id: WorkoutId | None = None,
    training_day_id: TrainingDayId | None = None,
    started_at: datetime | None = None,
) -> WorkoutSession:
    return WorkoutSession(
        id=WorkoutSessionId.generate(),
        user_id=user_id,
        workout_id=workout_id or WorkoutId.generate(),
        training_day_id=training_day_id or TrainingDayId.generate(),
        started_at=started_at or datetime.now(UTC),
    )


@pytest.fixture
def workout_repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def use_case(
    workout_repo: InMemoryWorkoutRepository, session_repo: InMemorySessionRepository
) -> GetSessionsForDayUseCase:
    return GetSessionsForDayUseCase(session_repo, workout_repo)


async def test_get_sessions_empty(
    use_case: GetSessionsForDayUseCase,
    workout_repo: InMemoryWorkoutRepository,
) -> None:
    workout = _make_workout(user_id="user-1", days=["MONDAY"])
    await workout_repo.save(workout)
    day = list(workout.get_training_days().values())[0]

    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(workout.id.value),
        training_day_id=str(day.id.value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    assert result.unwrap() == []


async def test_get_sessions_returns_matching(
    use_case: GetSessionsForDayUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    workout = _make_workout(user_id="user-1", days=["MONDAY"])
    await workout_repo.save(workout)
    day = list(workout.get_training_days().values())[0]

    s1 = _make_session(user_id="user-1", workout_id=workout.id, training_day_id=day.id)
    s2 = _make_session(user_id="user-1", workout_id=workout.id, training_day_id=day.id)
    await session_repo.save(s1)
    await session_repo.save(s2)

    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(workout.id.value),
        training_day_id=str(day.id.value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    dtos = result.unwrap()
    assert len(dtos) == 2
    assert all(isinstance(d, WorkoutSessionDTO) for d in dtos)


async def test_get_sessions_newest_first(
    use_case: GetSessionsForDayUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    workout = _make_workout(user_id="user-1", days=["MONDAY"])
    await workout_repo.save(workout)
    day = list(workout.get_training_days().values())[0]
    base = datetime(2026, 1, 1, tzinfo=UTC)

    older = _make_session(user_id="user-1", workout_id=workout.id, training_day_id=day.id, started_at=base)
    newer = _make_session(
        user_id="user-1", workout_id=workout.id, training_day_id=day.id, started_at=base + timedelta(hours=1)
    )
    await session_repo.save(older)
    await session_repo.save(newer)

    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(workout.id.value),
        training_day_id=str(day.id.value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    dtos = result.unwrap()
    assert dtos[0].id == str(newer.id.value)
    assert dtos[1].id == str(older.id.value)


async def test_get_sessions_unauthorized_for_other_user_workout(
    use_case: GetSessionsForDayUseCase,
    workout_repo: InMemoryWorkoutRepository,
) -> None:
    workout = _make_workout(user_id="user-2", days=["MONDAY"])
    await workout_repo.save(workout)
    day = list(workout.get_training_days().values())[0]

    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(workout.id.value),
        training_day_id=str(day.id.value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


async def test_get_sessions_day_not_in_workout(
    use_case: GetSessionsForDayUseCase,
    workout_repo: InMemoryWorkoutRepository,
) -> None:
    workout = _make_workout(user_id="user-1", days=["MONDAY"])
    await workout_repo.save(workout)
    unrelated_day_id = TrainingDayId.generate()

    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(workout.id.value),
        training_day_id=str(unrelated_day_id.value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_get_sessions_invalid_workout_id(use_case: GetSessionsForDayUseCase) -> None:
    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id="not-a-uuid",
        training_day_id=str(TrainingDayId.generate().value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_get_sessions_workout_not_found(use_case: GetSessionsForDayUseCase) -> None:
    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(WorkoutId.generate().value),
        training_day_id=str(TrainingDayId.generate().value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)
