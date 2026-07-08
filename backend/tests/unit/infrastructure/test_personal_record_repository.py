"""Tests for SqlAlchemyPersonalRecordRepository (SQLite in-memory)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
import sqlalchemy
from sqlalchemy import select
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
from backend.src.infrastructure.persistence.personal_record_repository import (
    SqlAlchemyPersonalRecordRepository,
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
def repo(session: AsyncSession) -> SqlAlchemyPersonalRecordRepository:
    return SqlAlchemyPersonalRecordRepository(session)


NOW = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def _ids() -> tuple[str, str, str]:
    return str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())


async def _select_record(
    session: AsyncSession, user_id: str, exercise_id: str
) -> PersonalRecordModel | None:
    stmt = select(PersonalRecordModel).where(
        PersonalRecordModel.user_id == user_id,
        PersonalRecordModel.exercise_id == exercise_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


# ── upsert_if_higher ──────────────────────────────────────────────────────────


async def test_upsert_first_record_inserts_and_returns_true(
    repo: SqlAlchemyPersonalRecordRepository, session: AsyncSession
) -> None:
    user_id, session_id, _ = _ids()

    created = await repo.upsert_if_higher(
        user_id=user_id, exercise_id="bench-press", weight_kg=80.0,
        session_id=session_id, achieved_at=NOW,
    )

    assert created is True
    record = await _select_record(session, user_id, "bench-press")
    assert record is not None
    assert record.weight_kg == 80.0
    assert record.session_id == session_id


async def test_upsert_heavier_updates_in_place_and_returns_true(
    repo: SqlAlchemyPersonalRecordRepository, session: AsyncSession
) -> None:
    user_id, first_session, second_session = _ids()
    await repo.upsert_if_higher(
        user_id=user_id, exercise_id="squat", weight_kg=100.0,
        session_id=first_session, achieved_at=NOW,
    )

    updated = await repo.upsert_if_higher(
        user_id=user_id, exercise_id="squat", weight_kg=110.0,
        session_id=second_session, achieved_at=NOW,
    )

    assert updated is True
    record = await _select_record(session, user_id, "squat")
    assert record is not None
    assert record.weight_kg == 110.0
    assert record.session_id == second_session
    # Still exactly one row per (user, exercise) — update, not insert.
    count = (
        await session.execute(
            select(sqlalchemy.func.count()).select_from(PersonalRecordModel).where(
                PersonalRecordModel.user_id == user_id,
                PersonalRecordModel.exercise_id == "squat",
            )
        )
    ).scalar_one()
    assert count == 1


async def test_upsert_lighter_or_equal_returns_false(
    repo: SqlAlchemyPersonalRecordRepository, session: AsyncSession
) -> None:
    user_id, first_session, second_session = _ids()
    await repo.upsert_if_higher(
        user_id=user_id, exercise_id="deadlift", weight_kg=140.0,
        session_id=first_session, achieved_at=NOW,
    )

    lighter = await repo.upsert_if_higher(
        user_id=user_id, exercise_id="deadlift", weight_kg=130.0,
        session_id=second_session, achieved_at=NOW,
    )
    equal = await repo.upsert_if_higher(
        user_id=user_id, exercise_id="deadlift", weight_kg=140.0,
        session_id=second_session, achieved_at=NOW,
    )

    assert lighter is False
    assert equal is False
    record = await _select_record(session, user_id, "deadlift")
    assert record is not None
    assert record.weight_kg == 140.0
    assert record.session_id == first_session


# ── get_previous_max_weights / get_catalog_exercise_ids ──────────────────────


async def test_previous_max_from_completed_history_excluding_current_session(
    repo: SqlAlchemyPersonalRecordRepository, session: AsyncSession
) -> None:
    user_id = str(uuid.uuid4())
    workout_id, day_id, we_id = _ids()
    session.add(UserModel(id=user_id, email=f"{user_id}@example.com", hashed_password="$stub$"))
    session.add(WorkoutModel(id=workout_id, user_id=user_id, name="Push"))
    session.add(TrainingDayModel(id=day_id, workout_id=workout_id, day_of_week="MONDAY"))
    session.add(
        WorkoutExerciseModel(
            id=we_id, workout_id=workout_id, training_day_id=day_id,
            exercise_id="bench-press", order_in_day=1,
        )
    )
    prior_completed, prior_in_progress, current = _ids()
    for sid, completed_at, weight in (
        (prior_completed, NOW, 80.0),       # counts: prior + completed
        (prior_in_progress, None, 999.0),   # ignored: never completed
        (current, NOW, 200.0),              # ignored: the session being completed
    ):
        session.add(
            WorkoutSessionModel(
                id=sid, user_id=user_id, workout_id=workout_id,
                training_day_id=day_id, started_at=NOW, completed_at=completed_at,
            )
        )
        session.add(
            WorkoutLogModel(
                id=str(uuid.uuid4()), session_id=sid, workout_exercise_id=we_id,
                set_number=1, reps_completed=10, weight_kg=weight,
            )
        )
    await session.flush()

    result = await repo.get_previous_max_weights(
        user_id=user_id, exclude_session_id=current, exercise_ids=["bench-press"]
    )
    catalog = await repo.get_catalog_exercise_ids([we_id, "unknown-id"])

    assert result == {"bench-press": 80.0}
    assert catalog == {we_id: "bench-press"}
