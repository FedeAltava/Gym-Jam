"""Unit tests for CompleteIdleSessionsUseCase."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.src.application.use_cases.complete_idle_sessions import CompleteIdleSessionsUseCase
from backend.src.application.use_cases.complete_workout_session import CompleteWorkoutSessionUseCase
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import (
    DayOfWeek,
    TrainingDayId,
    WorkoutExerciseId,
    WorkoutId,
    WorkoutSessionId,
)
from backend.tests.unit.application.use_cases.in_memory_personal_record_repository import (
    InMemoryPersonalRecordRepository,
)
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)

NOW = datetime(2026, 11, 13, 9, 0, tzinfo=UTC)


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def pr_repo() -> InMemoryPersonalRecordRepository:
    return InMemoryPersonalRecordRepository()


@pytest.fixture
def use_case(
    session_repo: InMemorySessionRepository, pr_repo: InMemoryPersonalRecordRepository
) -> CompleteIdleSessionsUseCase:
    return CompleteIdleSessionsUseCase(session_repo, CompleteWorkoutSessionUseCase(session_repo, pr_repo))


async def _seed_session(
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
    last_activity: datetime,
    user_id: str = "user-1",
) -> WorkoutSession:
    session = WorkoutSession(
        id=WorkoutSessionId.generate(),
        user_id=user_id,
        workout_id=WorkoutId.generate(),
        training_day_id=TrainingDayId.generate(),
        started_at=NOW - timedelta(hours=3),
    )
    exercise = WorkoutExercise(
        id=WorkoutExerciseId.generate(),
        workout_id=session.workout_id,
        day=DayOfWeek("MONDAY"),
        exercise_id="bench-press",
        order=1,
    )
    pr_repo.catalog_map[str(exercise.id.value)] = "bench-press"
    session.log_set(exercise, set_number=1, reps_completed=10, weight_kg=60.0)
    await session_repo.save(session)
    session_repo.last_activity[str(session.id.value)] = last_activity
    return session


async def test_idle_session_is_completed_at_its_last_activity_with_records(
    use_case: CompleteIdleSessionsUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    last_activity = NOW - timedelta(hours=1, minutes=1)
    session = await _seed_session(session_repo, pr_repo, last_activity)

    completed = await use_case.execute(user_id="user-1", now=NOW)

    assert completed == 1
    stored = await session_repo.get_by_id(session.id)
    assert stored is not None
    assert stored.completed_at == last_activity
    assert pr_repo.records[("user-1", "bench-press")]["weight_kg"] == 60.0


async def test_session_active_within_the_hour_stays_in_progress(
    use_case: CompleteIdleSessionsUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    session = await _seed_session(session_repo, pr_repo, NOW - timedelta(minutes=59))

    completed = await use_case.execute(user_id="user-1", now=NOW)

    assert completed == 0
    stored = await session_repo.get_by_id(session.id)
    assert stored is not None
    assert stored.completed_at is None
    assert pr_repo.records == {}



async def test_exactly_one_hour_of_inactivity_is_not_idle_yet(
    use_case: CompleteIdleSessionsUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    session = await _seed_session(session_repo, pr_repo, NOW - timedelta(hours=1))

    assert await use_case.execute(user_id="user-1", now=NOW) == 0
    stored = await session_repo.get_by_id(session.id)
    assert stored is not None
    assert stored.completed_at is None


async def test_all_idle_sessions_of_the_user_are_completed_in_one_sweep(
    use_case: CompleteIdleSessionsUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    first = await _seed_session(session_repo, pr_repo, NOW - timedelta(hours=2))
    second = await _seed_session(session_repo, pr_repo, NOW - timedelta(hours=5))
    other_user = await _seed_session(session_repo, pr_repo, NOW - timedelta(hours=5), user_id="user-2")

    assert await use_case.execute(user_id="user-1", now=NOW) == 2
    assert (await session_repo.get_by_id(first.id)).completed_at == NOW - timedelta(hours=2)  # type: ignore[union-attr]
    assert (await session_repo.get_by_id(second.id)).completed_at == NOW - timedelta(hours=5)  # type: ignore[union-attr]
    assert (await session_repo.get_by_id(other_user.id)).completed_at is None  # type: ignore[union-attr]


async def test_failed_record_detection_still_completes_the_session(
    use_case: CompleteIdleSessionsUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    pr_repo.raise_always = True
    last_activity = NOW - timedelta(hours=2)
    session = await _seed_session(session_repo, pr_repo, last_activity)

    assert await use_case.execute(user_id="user-1", now=NOW) == 1
    stored = await session_repo.get_by_id(session.id)
    assert stored is not None
    assert stored.completed_at == last_activity
    assert pr_repo.records == {}


async def test_a_second_sweep_leaves_a_completed_session_untouched(
    use_case: CompleteIdleSessionsUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    last_activity = NOW - timedelta(hours=2)
    session = await _seed_session(session_repo, pr_repo, last_activity)
    await use_case.execute(user_id="user-1", now=NOW)

    assert await use_case.execute(user_id="user-1", now=NOW + timedelta(hours=1)) == 0
    stored = await session_repo.get_by_id(session.id)
    assert stored is not None
    assert stored.completed_at == last_activity
    assert len(pr_repo.upsert_calls) == 1
    assert pr_repo.records[("user-1", "bench-press")]["achieved_at"] == last_activity
