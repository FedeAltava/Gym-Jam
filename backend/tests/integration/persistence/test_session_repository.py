"""Integration tests for SqlAlchemySessionRepository — 8 tests."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta


from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import TrainingDayId, WorkoutId, WorkoutSessionId
from backend.src.infrastructure.persistence.models import TrainingDayModel, WorkoutModel
from backend.src.infrastructure.persistence.session_repository import SqlAlchemySessionRepository


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


async def _insert_workout_and_day(session, user_id: str = "user-1") -> tuple[WorkoutId, TrainingDayId]:
    """Insert minimal WorkoutModel + TrainingDayModel rows so FK constraints pass."""
    wid = WorkoutId.generate()
    td_id = TrainingDayId.generate()
    session.add(
        WorkoutModel(
            id=str(wid.value),
            user_id=user_id,
            name="Test",
            description=None,
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    session.add(
        TrainingDayModel(
            id=str(td_id.value),
            workout_id=str(wid.value),
            day_of_week="MONDAY",
            created_at=datetime.now(UTC),
        )
    )
    await session.flush()
    return wid, td_id


# ─── 1. save + get_by_id round-trip ────────────────────────────────────────

async def test_save_and_get_by_id(session) -> None:
    repo = SqlAlchemySessionRepository(session)
    wid, td_id = await _insert_workout_and_day(session)
    s = _make_session(workout_id=wid, training_day_id=td_id)
    await repo.save(s)

    loaded = await repo.get_by_id(s.id)

    assert loaded is not None
    assert loaded.id == s.id
    assert loaded.user_id == "user-1"
    assert loaded.logs == []


# ─── 2. get_by_id unknown → None ────────────────────────────────────────────

async def test_get_by_id_unknown_returns_none(session) -> None:
    repo = SqlAlchemySessionRepository(session)

    result = await repo.get_by_id(WorkoutSessionId.generate())

    assert result is None


# ─── 3. logs round-trip ─────────────────────────────────────────────────────

async def test_save_session_with_logs_round_trips(session) -> None:
    from backend.src.infrastructure.persistence.models import WorkoutExerciseModel

    repo = SqlAlchemySessionRepository(session)
    wid, td_id = await _insert_workout_and_day(session)

    from backend.src.domain.value_objects import WorkoutExerciseId

    # Insert a workout exercise so FK passes
    ex_id = WorkoutExerciseId.generate()
    session.add(
        WorkoutExerciseModel(
            id=str(ex_id.value),
            workout_id=str(wid.value),
            training_day_id=str(td_id.value),
            exercise_id="bench-press",
            order_in_day=1,
            sets=3,
            reps_per_set=10,
            weight_kg=None,
        )
    )
    await session.flush()

    s = _make_session(workout_id=wid, training_day_id=td_id)

    from backend.src.domain.entities.workout_exercise import WorkoutExercise
    from backend.src.domain.value_objects import DayOfWeek

    exercise = WorkoutExercise(
        id=ex_id,
        workout_id=wid,
        day=DayOfWeek.MONDAY,
        exercise_id="bench-press",
        order=1,
        sets=3,
    )
    s.log_set(exercise, set_number=1, reps_completed=10, weight_kg=60.0)
    await repo.save(s)

    loaded = await repo.get_by_id(s.id)

    assert loaded is not None
    assert len(loaded.logs) == 1
    log = loaded.logs[0]
    assert log.set_number == 1
    assert log.reps_completed == 10
    assert log.weight_kg == 60.0


# ─── 4. logs replaced on re-save ────────────────────────────────────────────

async def test_logs_replaced_on_resave(session) -> None:
    from backend.src.infrastructure.persistence.models import WorkoutExerciseModel

    repo = SqlAlchemySessionRepository(session)
    wid, td_id = await _insert_workout_and_day(session)

    from backend.src.domain.value_objects import WorkoutExerciseId

    ex_id = WorkoutExerciseId.generate()
    session.add(
        WorkoutExerciseModel(
            id=str(ex_id.value),
            workout_id=str(wid.value),
            training_day_id=str(td_id.value),
            exercise_id="squat",
            order_in_day=1,
            sets=3,
            reps_per_set=10,
            weight_kg=None,
        )
    )
    await session.flush()

    from backend.src.domain.entities.workout_exercise import WorkoutExercise
    from backend.src.domain.value_objects import DayOfWeek

    s = _make_session(workout_id=wid, training_day_id=td_id)
    exercise = WorkoutExercise(
        id=ex_id,
        workout_id=wid,
        day=DayOfWeek.MONDAY,
        exercise_id="squat",
        order=1,
        sets=3,
    )
    s.log_set(exercise, set_number=1, reps_completed=8, weight_kg=None)
    await repo.save(s)

    # Add another log and re-save
    s.log_set(exercise, set_number=2, reps_completed=9, weight_kg=None)
    await repo.save(s)

    loaded = await repo.get_by_id(s.id)
    assert loaded is not None
    assert len(loaded.logs) == 2


# ─── 5. get_sessions_for_day filtering ──────────────────────────────────────

async def test_get_sessions_for_day_filtering(session) -> None:
    repo = SqlAlchemySessionRepository(session)
    wid, td_id = await _insert_workout_and_day(session, user_id="user-filter")
    wid2, td_id2 = await _insert_workout_and_day(session, user_id="user-filter")

    s1 = _make_session(user_id="user-filter", workout_id=wid, training_day_id=td_id)
    s2 = _make_session(user_id="user-filter", workout_id=wid2, training_day_id=td_id2)
    await repo.save(s1)
    await repo.save(s2)

    results = await repo.get_sessions_for_day("user-filter", wid, td_id)

    assert len(results) == 1
    assert results[0].id == s1.id


# ─── 6. get_sessions_for_day user isolation ─────────────────────────────────

async def test_get_sessions_for_day_user_isolation(session) -> None:
    repo = SqlAlchemySessionRepository(session)
    wid, td_id = await _insert_workout_and_day(session, user_id="user-a")

    s_a = _make_session(user_id="user-a", workout_id=wid, training_day_id=td_id)
    s_b = _make_session(user_id="user-b", workout_id=wid, training_day_id=td_id)
    await repo.save(s_a)
    await repo.save(s_b)

    results = await repo.get_sessions_for_day("user-a", wid, td_id)

    assert len(results) == 1
    assert results[0].user_id == "user-a"


# ─── 7. get_sessions_for_day orders newest first ────────────────────────────

async def test_get_sessions_for_day_newest_first(session) -> None:
    repo = SqlAlchemySessionRepository(session)
    wid, td_id = await _insert_workout_and_day(session, user_id="user-order")
    base = datetime(2026, 1, 1, tzinfo=UTC)

    older = _make_session(user_id="user-order", workout_id=wid, training_day_id=td_id, started_at=base)
    newer = _make_session(
        user_id="user-order", workout_id=wid, training_day_id=td_id, started_at=base + timedelta(hours=2)
    )
    await repo.save(older)
    await repo.save(newer)

    results = await repo.get_sessions_for_day("user-order", wid, td_id)

    assert len(results) == 2
    assert results[0].id == newer.id


# ─── 8. completed_at round-trips ────────────────────────────────────────────

async def test_completed_at_round_trips(session) -> None:
    repo = SqlAlchemySessionRepository(session)
    wid, td_id = await _insert_workout_and_day(session, user_id="user-complete")

    s = _make_session(user_id="user-complete", workout_id=wid, training_day_id=td_id)
    s.complete()
    await repo.save(s)

    loaded = await repo.get_by_id(s.id)

    assert loaded is not None
    assert loaded.completed_at is not None
    assert loaded.status == "completed"
