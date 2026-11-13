"""HTTP tests: GET /exercises/last-sets — latest logged sets of the exact exercise done."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from backend.src.infrastructure.persistence.models import WorkoutSessionModel
from backend.tests.http.test_sessions import add_exercise_to_day, create_workout_with_day


async def _session_with_sets(client, day: str, exercise_id: str, sets: list[tuple[int, float]]) -> tuple[str, str]:
    """Start a session on a new workout and log `sets` as (reps, kg). Returns (session_id, workout_exercise_id)."""
    wid, day_id = await create_workout_with_day(client, day)
    we_id = await add_exercise_to_day(client, wid, day, exercise_id)
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r.status_code == 201
    session_id = r.json()["id"]
    for set_number, (reps, kg) in enumerate(sets, start=1):
        r = await client.post(
            f"/sessions/{session_id}/logs",
            json={"workout_exercise_id": we_id, "set_number": set_number, "reps_completed": reps, "weight_kg": kg},
        )
        assert r.status_code == 201
    return session_id, we_id


async def _started(db, session_id: str, days_ago: int) -> None:
    started_at = datetime.now(UTC) - timedelta(days=days_ago)
    await db.execute(update(WorkoutSessionModel).where(WorkoutSessionModel.id == session_id).values(started_at=started_at))
    await db.commit()


async def _last_sets(client, *exercise_ids: str) -> list[dict]:
    r = await client.get("/exercises/last-sets", params=[("exercise_id", e) for e in exercise_ids])
    assert r.status_code == 200
    return r.json()


async def test_last_sets_come_from_the_latest_session_of_each_set_in_any_routine(client, session) -> None:
    older, _ = await _session_with_sets(client, "MONDAY", "leg-press-selectorized", [(10, 100.0), (9, 100.0)])
    newer, _ = await _session_with_sets(client, "TUESDAY", "leg-press-selectorized", [(8, 110.0)])
    await _started(session, older, days_ago=2)
    await _started(session, newer, days_ago=1)

    assert await _last_sets(client, "leg-press-selectorized") == [
        {"exercise_id": "leg-press-selectorized", "set_number": 1, "reps_completed": 8, "weight_kg": 110.0},
        {"exercise_id": "leg-press-selectorized", "set_number": 2, "reps_completed": 9, "weight_kg": 100.0},
    ]


async def test_a_swapped_slot_counts_for_the_exercise_actually_done(client) -> None:
    wid, day_id = await create_workout_with_day(client, "WEDNESDAY")
    we_id = await add_exercise_to_day(client, wid, "WEDNESDAY", "chest-press-plate-loaded")
    session_id = (await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})).json()["id"]
    r = await client.put(
        f"/sessions/{session_id}/exercises/{we_id}/swap", json={"exercise_id": "chest-press-selectorized"}
    )
    assert r.status_code == 200
    r = await client.post(
        f"/sessions/{session_id}/logs",
        json={"workout_exercise_id": we_id, "set_number": 1, "reps_completed": 10, "weight_kg": 40.0},
    )
    assert r.status_code == 201

    assert await _last_sets(client, "chest-press-selectorized", "chest-press-plate-loaded") == [
        {"exercise_id": "chest-press-selectorized", "set_number": 1, "reps_completed": 10, "weight_kg": 40.0},
    ]


async def test_other_users_sets_are_not_returned(client, client_user2) -> None:
    await _session_with_sets(client_user2, "THURSDAY", "triceps-machine-selectorized", [(12, 30.0)])

    assert await _last_sets(client, "triceps-machine-selectorized") == []


async def test_without_exercise_ids_returns_no_sets(client) -> None:
    assert await _last_sets(client) == []


async def test_more_than_50_exercise_ids_is_rejected(client) -> None:
    r = await client.get("/exercises/last-sets", params=[("exercise_id", f"e{i}") for i in range(51)])

    assert r.status_code == 422


async def test_last_sets_require_auth(auth_client) -> None:
    r = await auth_client.get("/exercises/last-sets", params={"exercise_id": "leg-press"})

    assert r.status_code == 401
