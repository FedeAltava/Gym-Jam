"""Unit tests for CompleteWorkoutSessionUseCase."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import CompleteWorkoutSessionCommand
from backend.src.application.dtos import WorkoutSessionDTO
from backend.src.application.errors import SessionNotFoundError, UnauthorizedError
from backend.src.application.use_cases.complete_workout_session import CompleteWorkoutSessionUseCase
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import TrainingDayId, WorkoutId, WorkoutSessionId
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)


def _make_session(user_id: str = "user-1") -> WorkoutSession:
    return WorkoutSession(
        id=WorkoutSessionId.generate(),
        user_id=user_id,
        workout_id=WorkoutId.generate(),
        training_day_id=TrainingDayId.generate(),
        started_at=datetime.now(UTC),
    )


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def use_case(session_repo: InMemorySessionRepository) -> CompleteWorkoutSessionUseCase:
    return CompleteWorkoutSessionUseCase(session_repo)


async def test_complete_session_happy_path(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    session = _make_session()
    await session_repo.save(session)

    cmd = CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))
    result = await use_case.execute(cmd)

    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, WorkoutSessionDTO)
    assert dto.status == "completed"
    assert dto.completed_at is not None


async def test_complete_session_idempotent(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    session = _make_session()
    await session_repo.save(session)

    cmd = CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))
    r1 = await use_case.execute(cmd)
    assert isinstance(r1, Success)
    first_completed_at = r1.unwrap().completed_at

    # Complete again — should be idempotent (completed_at unchanged)
    r2 = await use_case.execute(cmd)
    assert isinstance(r2, Success)
    assert r2.unwrap().completed_at == first_completed_at


async def test_complete_session_not_found(use_case: CompleteWorkoutSessionUseCase) -> None:
    cmd = CompleteWorkoutSessionCommand(
        user_id="user-1",
        session_id=str(WorkoutSessionId.generate().value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SessionNotFoundError)


async def test_complete_session_invalid_id(use_case: CompleteWorkoutSessionUseCase) -> None:
    cmd = CompleteWorkoutSessionCommand(user_id="user-1", session_id="not-a-uuid")
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SessionNotFoundError)


async def test_complete_session_unauthorized(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    session = _make_session(user_id="owner")
    await session_repo.save(session)

    cmd = CompleteWorkoutSessionCommand(user_id="attacker", session_id=str(session.id.value))
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)
