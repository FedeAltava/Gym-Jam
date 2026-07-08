"""Unit tests for DeleteExerciseLogUseCase."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import DeleteExerciseLogCommand
from backend.src.application.errors import (
    LogNotFoundError,
    SessionNotFoundError,
    UnauthorizedError,
)
from backend.src.application.use_cases.delete_exercise_log import DeleteExerciseLogUseCase
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import (
    DayOfWeek,
    ExerciseLogId,
    TrainingDayId,
    WorkoutExerciseId,
    WorkoutId,
    WorkoutSessionId,
)
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)


def _make_session_with_log(user_id: str = "user-1") -> tuple[WorkoutSession, str]:
    session = WorkoutSession(
        id=WorkoutSessionId.generate(),
        user_id=user_id,
        workout_id=WorkoutId.generate(),
        training_day_id=TrainingDayId.generate(),
        started_at=datetime.now(UTC),
    )
    exercise = WorkoutExercise(
        id=WorkoutExerciseId.generate(),
        workout_id=session.workout_id,
        day=DayOfWeek("MONDAY"),
        exercise_id="bench-press",
        order=1,
    )
    log = session.log_set(exercise, set_number=1, reps_completed=10, weight_kg=80.0)
    return session, str(log.id.value)


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def use_case(session_repo: InMemorySessionRepository) -> DeleteExerciseLogUseCase:
    return DeleteExerciseLogUseCase(session_repo)


async def test_delete_log_happy_path(
    use_case: DeleteExerciseLogUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    session, log_id = _make_session_with_log()
    await session_repo.save(session)

    cmd = DeleteExerciseLogCommand(user_id="user-1", session_id=str(session.id.value), log_id=log_id)
    result = await use_case.execute(cmd)

    assert isinstance(result, Success)
    stored = await session_repo.get_by_id(session.id)
    assert stored is not None
    assert stored.logs == []


async def test_delete_log_unauthorized(
    use_case: DeleteExerciseLogUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    session, log_id = _make_session_with_log(user_id="owner")
    await session_repo.save(session)

    cmd = DeleteExerciseLogCommand(user_id="attacker", session_id=str(session.id.value), log_id=log_id)
    result = await use_case.execute(cmd)

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)
    stored = await session_repo.get_by_id(session.id)
    assert stored is not None
    assert len(stored.logs) == 1


async def test_delete_log_not_in_session(
    use_case: DeleteExerciseLogUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    session, _ = _make_session_with_log()
    await session_repo.save(session)

    cmd = DeleteExerciseLogCommand(
        user_id="user-1",
        session_id=str(session.id.value),
        log_id=str(ExerciseLogId.generate().value),
    )
    result = await use_case.execute(cmd)

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), LogNotFoundError)


async def test_delete_log_invalid_log_id(
    use_case: DeleteExerciseLogUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    session, _ = _make_session_with_log()
    await session_repo.save(session)

    cmd = DeleteExerciseLogCommand(user_id="user-1", session_id=str(session.id.value), log_id="not-a-uuid")
    result = await use_case.execute(cmd)

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), LogNotFoundError)


async def test_delete_log_session_not_found(use_case: DeleteExerciseLogUseCase) -> None:
    cmd = DeleteExerciseLogCommand(
        user_id="user-1",
        session_id=str(WorkoutSessionId.generate().value),
        log_id=str(ExerciseLogId.generate().value),
    )
    result = await use_case.execute(cmd)

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SessionNotFoundError)
