"""Unit tests for GetSessionsForDayUseCase."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import GetSessionsForDayCommand
from backend.src.application.dtos import WorkoutSessionDTO
from backend.src.application.errors import WorkoutNotFoundError
from backend.src.application.use_cases.get_sessions_for_day import GetSessionsForDayUseCase
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import TrainingDayId, WorkoutId, WorkoutSessionId
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)


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
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def use_case(session_repo: InMemorySessionRepository) -> GetSessionsForDayUseCase:
    return GetSessionsForDayUseCase(session_repo)


async def test_get_sessions_empty(use_case: GetSessionsForDayUseCase) -> None:
    wid = WorkoutId.generate()
    td_id = TrainingDayId.generate()
    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(wid.value),
        training_day_id=str(td_id.value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    assert result.unwrap() == []


async def test_get_sessions_returns_matching(
    use_case: GetSessionsForDayUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    wid = WorkoutId.generate()
    td_id = TrainingDayId.generate()

    s1 = _make_session(user_id="user-1", workout_id=wid, training_day_id=td_id)
    s2 = _make_session(user_id="user-1", workout_id=wid, training_day_id=td_id)
    await session_repo.save(s1)
    await session_repo.save(s2)

    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(wid.value),
        training_day_id=str(td_id.value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    dtos = result.unwrap()
    assert len(dtos) == 2
    assert all(isinstance(d, WorkoutSessionDTO) for d in dtos)


async def test_get_sessions_newest_first(
    use_case: GetSessionsForDayUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    wid = WorkoutId.generate()
    td_id = TrainingDayId.generate()
    base = datetime(2026, 1, 1, tzinfo=UTC)

    older = _make_session(user_id="user-1", workout_id=wid, training_day_id=td_id, started_at=base)
    newer = _make_session(
        user_id="user-1", workout_id=wid, training_day_id=td_id, started_at=base + timedelta(hours=1)
    )
    await session_repo.save(older)
    await session_repo.save(newer)

    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(wid.value),
        training_day_id=str(td_id.value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    dtos = result.unwrap()
    assert dtos[0].id == str(newer.id.value)
    assert dtos[1].id == str(older.id.value)


async def test_get_sessions_user_isolation(
    use_case: GetSessionsForDayUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    wid = WorkoutId.generate()
    td_id = TrainingDayId.generate()

    other_user_session = _make_session(user_id="user-2", workout_id=wid, training_day_id=td_id)
    await session_repo.save(other_user_session)

    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(wid.value),
        training_day_id=str(td_id.value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    assert result.unwrap() == []


async def test_get_sessions_invalid_workout_id(use_case: GetSessionsForDayUseCase) -> None:
    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id="not-a-uuid",
        training_day_id=str(TrainingDayId.generate().value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_get_sessions_invalid_training_day_id(use_case: GetSessionsForDayUseCase) -> None:
    cmd = GetSessionsForDayCommand(
        user_id="user-1",
        workout_id=str(WorkoutId.generate().value),
        training_day_id="not-a-uuid",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)
