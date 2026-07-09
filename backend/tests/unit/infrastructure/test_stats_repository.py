"""Tests for SqlAlchemyStatsRepository (SQLite in-memory)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.infrastructure.persistence.models import (
    Base,
    PersonalRecordModel,
    TrainingDayModel,
    UserModel,
    WorkoutExerciseModel,
    WorkoutLogModel,
    WorkoutModel,
    WorkoutSessionModel,
)
from backend.src.infrastructure.persistence.stats_repository import (
    SqlAlchemyStatsRepository,
)

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
def engine():
    return create_async_engine(TEST_DB_URL, echo=False)


@pytest.fixture(scope="module")
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(engine, create_tables) -> AsyncSession:
    async with engine.connect() as conn:
        await conn.execute(sqlalchemy.text("PRAGMA foreign_keys=OFF"))
        async with async_sessionmaker(conn, class_=AsyncSession, expire_on_commit=False)() as s:
            yield s


@pytest.fixture
def repo(session: AsyncSession) -> SqlAlchemyStatsRepository:
    return SqlAlchemyStatsRepository(session)


NOW = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
WEEK_START = datetime(2026, 7, 6, 0, 0, tzinfo=UTC)  # Monday of NOW's week
LAST_WEEK = NOW - timedelta(days=7)


async def _seed_user(session: AsyncSession) -> str:
    user_id = str(uuid.uuid4())
    session.add(
        UserModel(id=user_id, email=f"{user_id}@example.com", hashed_password="$stub$")
    )
    return user_id


async def _seed_workout_day(
    session: AsyncSession, user_id: str, day: str, is_active: bool
) -> tuple[str, str, str]:
    """Create workout + training day + one plan exercise. Returns ids."""
    workout_id, day_id, we_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    session.add(
        WorkoutModel(id=workout_id, user_id=user_id, name=f"W {workout_id[:8]}", is_active=is_active)
    )
    session.add(TrainingDayModel(id=day_id, workout_id=workout_id, day_of_week=day))
    session.add(
        WorkoutExerciseModel(
            id=we_id, workout_id=workout_id, training_day_id=day_id,
            exercise_id="bench-press", order_in_day=1,
        )
    )
    return workout_id, day_id, we_id


def _session_model(
    user_id: str, workout_id: str, day_id: str,
    started_at: datetime, completed: bool,
) -> WorkoutSessionModel:
    return WorkoutSessionModel(
        id=str(uuid.uuid4()), user_id=user_id, workout_id=workout_id,
        training_day_id=day_id, started_at=started_at,
        completed_at=started_at + timedelta(hours=1) if completed else None,
    )


# ── get_active_plan_days ─────────────────────────────────────────────────────


async def test_active_plan_days_only_from_active_workouts(
    repo: SqlAlchemyStatsRepository, session: AsyncSession
) -> None:
    user_id = await _seed_user(session)
    await _seed_workout_day(session, user_id, "MONDAY", is_active=True)
    await _seed_workout_day(session, user_id, "FRIDAY", is_active=False)
    await session.flush()

    days = await repo.get_active_plan_days(user_id)

    assert days == ["MONDAY"]


async def test_active_plan_days_empty_for_new_user(
    repo: SqlAlchemyStatsRepository, session: AsyncSession
) -> None:
    user_id = await _seed_user(session)
    await session.flush()

    assert await repo.get_active_plan_days(user_id) == []


# ── get_completed_session_dates ──────────────────────────────────────────────


async def test_completed_session_dates_filters_status_user_and_since(
    repo: SqlAlchemyStatsRepository, session: AsyncSession
) -> None:
    user_id = await _seed_user(session)
    other_id = await _seed_user(session)
    workout_id, day_id, _ = await _seed_workout_day(session, user_id, "MONDAY", True)
    ow_id, od_id, _ = await _seed_workout_day(session, other_id, "MONDAY", True)

    session.add(_session_model(user_id, workout_id, day_id, NOW, completed=True))
    session.add(_session_model(user_id, workout_id, day_id, NOW - timedelta(days=1), completed=False))
    session.add(_session_model(user_id, workout_id, day_id, NOW - timedelta(days=30), completed=True))
    session.add(_session_model(other_id, ow_id, od_id, NOW, completed=True))
    await session.flush()

    dates = await repo.get_completed_session_dates(user_id, since=NOW.date() - timedelta(days=10))

    # In-progress, out-of-window, and other users' sessions are excluded.
    assert dates == {NOW.date()}


# ── get_aggregates ───────────────────────────────────────────────────────────


async def test_aggregates_volume_excludes_null_weight(
    repo: SqlAlchemyStatsRepository, session: AsyncSession
) -> None:
    user_id = await _seed_user(session)
    workout_id, day_id, we_id = await _seed_workout_day(session, user_id, "MONDAY", True)
    completed = _session_model(user_id, workout_id, day_id, NOW, completed=True)
    session.add(completed)
    session.add(
        WorkoutLogModel(
            id=str(uuid.uuid4()), session_id=completed.id, workout_exercise_id=we_id,
            set_number=1, reps_completed=10, weight_kg=80.0,
        )
    )
    session.add(
        WorkoutLogModel(
            id=str(uuid.uuid4()), session_id=completed.id, workout_exercise_id=we_id,
            set_number=2, reps_completed=12, weight_kg=None,  # bodyweight → 0
        )
    )
    await session.flush()

    agg = await repo.get_aggregates(user_id, weekly_start=WEEK_START)

    assert agg.weekly_volume_kg == 800.0
    assert agg.weekly_sessions == 1
    assert agg.total_sessions == 1


async def test_aggregates_weekly_window_and_pr_counts(
    repo: SqlAlchemyStatsRepository, session: AsyncSession
) -> None:
    user_id = await _seed_user(session)
    workout_id, day_id, we_id = await _seed_workout_day(session, user_id, "MONDAY", True)

    this_week = _session_model(user_id, workout_id, day_id, NOW, completed=True)
    last_week = _session_model(user_id, workout_id, day_id, LAST_WEEK, completed=True)
    in_progress = _session_model(user_id, workout_id, day_id, NOW, completed=False)
    session.add_all([this_week, last_week, in_progress])
    session.add(
        WorkoutLogModel(
            id=str(uuid.uuid4()), session_id=last_week.id, workout_exercise_id=we_id,
            set_number=1, reps_completed=10, weight_kg=100.0,  # outside weekly window
        )
    )
    session.add(
        PersonalRecordModel(
            id=str(uuid.uuid4()), user_id=user_id, exercise_id="bench-press",
            weight_kg=80.0, achieved_at=NOW, session_id=this_week.id,
        )
    )
    session.add(
        PersonalRecordModel(
            id=str(uuid.uuid4()), user_id=user_id, exercise_id="squat",
            weight_kg=120.0, achieved_at=LAST_WEEK, session_id=last_week.id,
        )
    )
    await session.flush()

    agg = await repo.get_aggregates(user_id, weekly_start=WEEK_START)

    assert agg.total_sessions == 2  # completed only — in-progress excluded
    assert agg.weekly_sessions == 1
    assert agg.weekly_volume_kg == 0.0  # last week's log is out of window
    assert agg.total_prs == 2
    assert agg.weekly_prs == 1


async def test_aggregates_zero_state_new_user(
    repo: SqlAlchemyStatsRepository, session: AsyncSession
) -> None:
    user_id = await _seed_user(session)
    await session.flush()

    agg = await repo.get_aggregates(user_id, weekly_start=WEEK_START)

    assert agg.total_sessions == 0
    assert agg.total_prs == 0
    assert agg.weekly_volume_kg == 0.0
    assert agg.weekly_sessions == 0
    assert agg.weekly_prs == 0
