"""HTTP tests: sessions idle for an hour are completed automatically."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text, update

from backend.src.application.use_cases.complete_idle_sessions import CompleteIdleSessionsUseCase
from backend.src.infrastructure.persistence.models import (
    PersonalRecordModel,
    WorkoutLogModel,
    WorkoutSessionModel,
)
from backend.tests.http.test_sessions import add_exercise_to_day, create_workout_with_day


def _ago(**delta: float) -> datetime:
    return (datetime.now(UTC) - timedelta(**delta)).replace(microsecond=0)


async def _start(client, day: str) -> tuple[str, str, str, str]:
    """Start a session on a new workout. Returns (workout_id, day_id, workout_exercise_id, session_id)."""
    wid, day_id = await create_workout_with_day(client, day)
    ex_id = await add_exercise_to_day(client, wid, day, "bench-press")
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r.status_code == 201
    return wid, day_id, ex_id, r.json()["id"]


async def _log_set(client, session_id: str, ex_id: str) -> str:
    r = await client.post(
        f"/sessions/{session_id}/logs",
        json={"workout_exercise_id": ex_id, "set_number": 1, "reps_completed": 10, "weight_kg": 80.0},
    )
    assert r.status_code == 201
    return r.json()["id"]


async def _backdate(db, session_id: str, started_at: datetime, log_id: str | None = None, logged_at: datetime | None = None) -> None:
    await db.execute(update(WorkoutSessionModel).where(WorkoutSessionModel.id == session_id).values(started_at=started_at))
    if log_id is not None:
        await db.execute(update(WorkoutLogModel).where(WorkoutLogModel.id == log_id).values(created_at=logged_at))
    await db.commit()


async def _day_session(client, wid: str, day_id: str, session_id: str) -> dict:
    r = await client.get(f"/workouts/{wid}/days/{day_id}/sessions")
    assert r.status_code == 200
    return next(s for s in r.json() if s["id"] == session_id)


async def test_idle_session_is_completed_at_its_last_set(client, session) -> None:
    wid, day_id, ex_id, session_id = await _start(client, "MONDAY")
    log_id = await _log_set(client, session_id, ex_id)
    last_set_at = _ago(hours=2)
    await _backdate(session, session_id, _ago(hours=3), log_id, last_set_at)

    item = await _day_session(client, wid, day_id, session_id)

    assert item["status"] == "completed"
    assert datetime.fromisoformat(item["completed_at"]) == last_set_at


async def test_idle_session_without_sets_is_completed_at_its_start(client, session) -> None:
    wid, day_id, _, session_id = await _start(client, "TUESDAY")
    started_at = _ago(minutes=61)
    await _backdate(session, session_id, started_at)

    item = await _day_session(client, wid, day_id, session_id)

    assert item["status"] == "completed"
    assert datetime.fromisoformat(item["completed_at"]) == started_at


async def test_session_with_a_set_in_the_last_hour_stays_in_progress(client, session) -> None:
    wid, day_id, ex_id, session_id = await _start(client, "WEDNESDAY")
    log_id = await _log_set(client, session_id, ex_id)
    await _backdate(session, session_id, _ago(hours=3), log_id, _ago(minutes=50))

    item = await _day_session(client, wid, day_id, session_id)

    assert item["status"] == "in_progress"
    assert item["completed_at"] is None


async def test_starting_a_day_with_an_idle_session_starts_a_new_one(client, session) -> None:
    wid, day_id, _, session_id = await _start(client, "THURSDAY")
    await _backdate(session, session_id, _ago(hours=2))

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})

    assert r.status_code == 201
    assert r.json()["id"] != session_id
    assert (await _day_session(client, wid, day_id, session_id))["status"] == "completed"


async def test_history_shows_an_idle_session_as_completed(client, session) -> None:
    wid, _, _, session_id = await _start(client, "FRIDAY")
    await _backdate(session, session_id, _ago(hours=2))

    r = await client.get("/sessions", params={"workout_id": wid})

    assert r.status_code == 200
    item = next(s for s in r.json()["items"] if s["id"] == session_id)
    assert item["status"] == "completed"


async def test_other_users_requests_leave_an_idle_session_alone(client, client_user2, session) -> None:
    _, _, _, session_id = await _start(client, "SATURDAY")
    await _backdate(session, session_id, _ago(hours=2))

    r = await client_user2.get("/sessions")

    assert r.status_code == 200
    completed_at = (
        await session.execute(select(WorkoutSessionModel.completed_at).where(WorkoutSessionModel.id == session_id))
    ).scalar_one()
    assert completed_at is None
    # Sweep it as its owner so later tests sharing the database see no idle session.
    await client.get("/sessions")


async def _data_hash(db) -> str:
    digest = hashlib.sha256()
    for table in ("workout_sessions", "workout_logs", "personal_records"):
        rows = (await db.execute(text(f"SELECT * FROM {table} ORDER BY id"))).all()
        digest.update(repr(rows).encode())
    return digest.hexdigest()


async def test_requests_with_nothing_idle_change_no_data(client, session) -> None:
    wid, day_id, ex_id, session_id = await _start(client, "SUNDAY")
    log_id = await _log_set(client, session_id, ex_id)
    await _backdate(session, session_id, _ago(hours=3), log_id, _ago(minutes=59))
    before = await _data_hash(session)

    assert (await client.get(f"/workouts/{wid}/days/{day_id}/sessions")).status_code == 200
    assert (await client.get("/sessions")).status_code == 200
    assert (await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})).status_code == 409

    assert await _data_hash(session) == before


async def test_idle_session_keeps_its_duration_and_personal_record(client, session) -> None:
    wid, _, ex_id, session_id = await _start(client, "MONDAY")
    log_id = await _log_set(client, session_id, ex_id)
    last_set_at = _ago(hours=2)
    await _backdate(session, session_id, last_set_at - timedelta(hours=1), log_id, last_set_at)

    r = await client.get("/sessions", params={"workout_id": wid})

    item = next(s for s in r.json()["items"] if s["id"] == session_id)
    assert item["duration_seconds"] == 3600
    records = (
        await session.execute(select(PersonalRecordModel).where(PersonalRecordModel.session_id == session_id))
    ).scalars().all()
    assert [record.weight_kg for record in records] == [80.0]
    achieved_at = records[0].achieved_at
    assert achieved_at.replace(tzinfo=achieved_at.tzinfo or UTC) == last_set_at


async def test_a_failed_sweep_still_serves_the_listing(client, monkeypatch) -> None:
    async def failing_sweep(self, user_id, now):  # noqa: ANN001, ANN202
        raise RuntimeError("simulated sweep failure")

    monkeypatch.setattr(CompleteIdleSessionsUseCase, "execute", failing_sweep)
    wid, day_id, _, session_id = await _start(client, "TUESDAY")

    r = await client.get(f"/workouts/{wid}/days/{day_id}/sessions")

    assert r.status_code == 200
    assert [s["id"] for s in r.json()] == [session_id]
