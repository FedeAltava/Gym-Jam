"""HTTP tests for DELETE log endpoint and PR detection on session complete."""
from __future__ import annotations

import uuid


# ── Helpers (pattern from test_sessions.py) ───────────────────────────────────


async def create_workout_with_day(client, day: str = "MONDAY") -> tuple[str, str]:
    r = await client.post("/workouts", json={"name": f"PR Workout {uuid.uuid4()}", "training_days": []})
    assert r.status_code == 201
    wid = r.json()["id"]

    r2 = await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": day})
    assert r2.status_code == 201

    r3 = await client.get(f"/workouts/{wid}")
    assert r3.status_code == 200
    return wid, r3.json()["training_days"][0]["id"]


async def add_exercise_to_day(client, wid: str, day: str, exercise_id: str) -> str:
    r = await client.post(
        f"/workouts/{wid}/training-days/{day}/exercises",
        json={"exercise_id": exercise_id, "sets": 3},
    )
    assert r.status_code == 201
    return r.json()["id"]


async def start_session_with_log(
    client, wid: str, day_id: str, ex_id: str, weight_kg: float | None, reps: int = 10
) -> tuple[str, str]:
    """Start a session and log one set. Returns (session_id, log_id)."""
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r.status_code == 201
    session_id = r.json()["id"]

    r2 = await client.post(
        f"/sessions/{session_id}/logs",
        json={
            "workout_exercise_id": ex_id,
            "set_number": 1,
            "reps_completed": reps,
            "weight_kg": weight_kg,
        },
    )
    assert r2.status_code == 201
    return session_id, r2.json()["id"]


async def pr_count_for(client, session_id: str) -> int:
    r = await client.get("/sessions", params={"page_size": 100})
    assert r.status_code == 200
    item = next(s for s in r.json()["items"] if s["id"] == session_id)
    return item["pr_count"]


# ── DELETE /sessions/{sid}/logs/{lid} ─────────────────────────────────────────


async def test_delete_log_returns_204_and_removes_log(client) -> None:
    wid, day_id = await create_workout_with_day(client)
    ex_id = await add_exercise_to_day(client, wid, "MONDAY", "bench-press")
    session_id, log_id = await start_session_with_log(client, wid, day_id, ex_id, 80.0)

    r = await client.delete(f"/sessions/{session_id}/logs/{log_id}")

    assert r.status_code == 204
    r2 = await client.get(f"/workouts/{wid}/days/{day_id}/sessions")
    assert r2.status_code == 200
    assert r2.json()[0]["logs"] == []


async def test_delete_log_of_another_user_returns_403(client, client_user2) -> None:
    wid, day_id = await create_workout_with_day(client, "TUESDAY")
    ex_id = await add_exercise_to_day(client, wid, "TUESDAY", "hack-squat")
    session_id, log_id = await start_session_with_log(client, wid, day_id, ex_id, 100.0)

    r = await client_user2.delete(f"/sessions/{session_id}/logs/{log_id}")

    assert r.status_code == 403


async def test_delete_nonexistent_log_returns_404(client) -> None:
    wid, day_id = await create_workout_with_day(client, "WEDNESDAY")
    ex_id = await add_exercise_to_day(client, wid, "WEDNESDAY", "deadlift")
    session_id, _ = await start_session_with_log(client, wid, day_id, ex_id, 120.0)

    r = await client.delete(f"/sessions/{session_id}/logs/{uuid.uuid4()}")

    assert r.status_code == 404


async def test_delete_log_in_nonexistent_session_returns_404(client) -> None:
    r = await client.delete(f"/sessions/{uuid.uuid4()}/logs/{uuid.uuid4()}")

    assert r.status_code == 404


async def test_delete_log_requires_auth(auth_client) -> None:
    r = await auth_client.delete(
        f"/sessions/{uuid.uuid4()}/logs/{uuid.uuid4()}"
    )

    assert r.status_code == 401


# ── PR detection via POST /sessions/{id}/complete ─────────────────────────────


async def test_complete_detects_first_pr_then_beat_then_tie(client) -> None:
    wid, day_id = await create_workout_with_day(client, "THURSDAY")
    ex_id = await add_exercise_to_day(client, wid, "THURSDAY", "overhead-press")

    # First ever weighted log for the exercise → PR by definition.
    s1, _ = await start_session_with_log(client, wid, day_id, ex_id, 40.0)
    assert (await client.post(f"/sessions/{s1}/complete", json={})).status_code == 200
    assert await pr_count_for(client, s1) == 1

    # Heavier at the same reps → higher estimate → new PR.
    s2, _ = await start_session_with_log(client, wid, day_id, ex_id, 45.0)
    assert (await client.post(f"/sessions/{s2}/complete", json={})).status_code == 200
    assert await pr_count_for(client, s2) == 1

    # Same set as the previous best → tie → no PR.
    s3, _ = await start_session_with_log(client, wid, day_id, ex_id, 45.0)
    assert (await client.post(f"/sessions/{s3}/complete", json={})).status_code == 200
    assert await pr_count_for(client, s3) == 0


async def test_complete_awards_pr_by_estimated_one_rep_max(client) -> None:
    wid, day_id = await create_workout_with_day(client, "THURSDAY")
    ex_id = await add_exercise_to_day(client, wid, "THURSDAY", "incline-bench-press")

    s1, _ = await start_session_with_log(client, wid, day_id, ex_id, 80.0, reps=8)
    assert (await client.post(f"/sessions/{s1}/complete", json={})).status_code == 200
    assert await pr_count_for(client, s1) == 1

    # Same weight, more reps: 80 × 12 = 112 kg beats 80 × 8 ≈ 101 kg → PR.
    s2, _ = await start_session_with_log(client, wid, day_id, ex_id, 80.0, reps=12)
    assert (await client.post(f"/sessions/{s2}/complete", json={})).status_code == 200
    assert await pr_count_for(client, s2) == 1

    # Heavier but far fewer reps: 82.5 × 3 ≈ 91 kg < 112 kg → no PR.
    s3, _ = await start_session_with_log(client, wid, day_id, ex_id, 82.5, reps=3)
    assert (await client.post(f"/sessions/{s3}/complete", json={})).status_code == 200
    assert await pr_count_for(client, s3) == 0


async def test_complete_is_idempotent_for_prs(client) -> None:
    wid, day_id = await create_workout_with_day(client, "FRIDAY")
    ex_id = await add_exercise_to_day(client, wid, "FRIDAY", "machine-row")
    session_id, _ = await start_session_with_log(client, wid, day_id, ex_id, 70.0)

    r1 = await client.post(f"/sessions/{session_id}/complete", json={})
    r2 = await client.post(f"/sessions/{session_id}/complete", json={})

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert await pr_count_for(client, session_id) == 1


async def test_bodyweight_logs_produce_no_pr(client) -> None:
    wid, day_id = await create_workout_with_day(client, "SATURDAY")
    ex_id = await add_exercise_to_day(client, wid, "SATURDAY", "lat-pulldown")
    session_id, _ = await start_session_with_log(client, wid, day_id, ex_id, None)

    r = await client.post(f"/sessions/{session_id}/complete", json={})

    assert r.status_code == 200
    assert await pr_count_for(client, session_id) == 0


async def test_completed_session_history_includes_duration_seconds(client) -> None:
    wid, day_id = await create_workout_with_day(client, "SUNDAY")
    ex_id = await add_exercise_to_day(client, wid, "SUNDAY", "lat-pulldown")
    session_id, _ = await start_session_with_log(client, wid, day_id, ex_id, 50.0)

    r = await client.post(f"/sessions/{session_id}/complete", json={})
    assert r.status_code == 200
    assert r.json()["duration_seconds"] is not None

    r2 = await client.get("/sessions", params={"page_size": 100})
    item = next(s for s in r2.json()["items"] if s["id"] == session_id)
    assert item["duration_seconds"] is not None
    assert item["duration_seconds"] >= 0

    # In-progress sessions expose null duration.
    r3 = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r3.status_code == 201
    assert r3.json()["duration_seconds"] is None


async def test_swapped_exercise_records_pr_for_the_substitute(client) -> None:
    wid, day_id = await create_workout_with_day(client, "SATURDAY")
    ex_id = await add_exercise_to_day(client, wid, "SATURDAY", "barbell-row")

    s1, _ = await start_session_with_log(client, wid, day_id, ex_id, 100.0)
    assert (await client.post(f"/sessions/{s1}/complete", json={})).status_code == 200
    assert await pr_count_for(client, s1) == 1

    # Swapped to cable crossover: 20 kg × 12 (28 kg) is far below the row's
    # 100 kg × 10, but it is the first cable crossover ever → PR for the substitute.
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    s2 = r.json()["id"]
    r = await client.put(f"/sessions/{s2}/exercises/{ex_id}/swap", json={"exercise_id": "cable-crossover"})
    assert r.status_code == 200
    r = await client.post(
        f"/sessions/{s2}/logs",
        json={"workout_exercise_id": ex_id, "set_number": 1, "reps_completed": 12, "weight_kg": 20.0},
    )
    assert r.status_code == 201
    assert (await client.post(f"/sessions/{s2}/complete", json={})).status_code == 200
    assert await pr_count_for(client, s2) == 1

    # A routine where cable crossover is planned sees the swapped session's
    # 20 kg × 12 (28 kg) as the previous best → 22.5 kg × 5 (≈ 26 kg) is
    # heavier but no PR; 20 kg × 15 (30 kg) is.
    wid2, day2 = await create_workout_with_day(client, "SATURDAY")
    ex2 = await add_exercise_to_day(client, wid2, "SATURDAY", "cable-crossover")
    s3, _ = await start_session_with_log(client, wid2, day2, ex2, 22.5, reps=5)
    assert (await client.post(f"/sessions/{s3}/complete", json={})).status_code == 200
    assert await pr_count_for(client, s3) == 0
    s4, _ = await start_session_with_log(client, wid2, day2, ex2, 20.0, reps=15)
    assert (await client.post(f"/sessions/{s4}/complete", json={})).status_code == 200
    assert await pr_count_for(client, s4) == 1
