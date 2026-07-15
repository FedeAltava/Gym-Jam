"""HTTP tests for GET /sessions — cross-workout session history."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import event


# ── Helpers ──────────────────────────────────────────────────────────────────


async def create_workout_with_day(client, day: str = "MONDAY") -> tuple[str, str]:
    """Create workout + training day. Returns (workout_id, day_id)."""
    r = await client.post("/workouts", json={"name": "History Workout", "training_days": []})
    assert r.status_code == 201
    wid = r.json()["id"]

    r2 = await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": day})
    assert r2.status_code == 201

    r3 = await client.get(f"/workouts/{wid}")
    assert r3.status_code == 200
    days = r3.json()["training_days"]
    assert len(days) == 1
    return wid, days[0]["id"]


async def add_exercise_to_day(
    client, wid: str, day: str = "MONDAY", exercise_id: str = "bench-press"
) -> str:
    r = await client.post(
        f"/workouts/{wid}/training-days/{day}/exercises",
        json={"exercise_id": exercise_id, "sets": 3},
    )
    assert r.status_code == 201
    return r.json()["id"]


async def start_session(client, wid: str, day_id: str) -> str:
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r.status_code == 201
    return r.json()["id"]


async def complete_session(client, session_id: str) -> None:
    r = await client.post(f"/sessions/{session_id}/complete", json={})
    assert r.status_code == 200


# ── 1. Auth required ──────────────────────────────────────────────────────────


async def test_history_requires_auth(auth_client) -> None:
    r = await auth_client.get("/sessions")
    assert r.status_code == 401


# ── 2. Happy path — response shape ────────────────────────────────────────────


async def test_history_returns_session_with_resolved_names(client) -> None:
    wid, day_id = await create_workout_with_day(client, "MONDAY")
    ex_id = await add_exercise_to_day(client, wid, "MONDAY", "hack-squat")
    session_id = await start_session(client, wid, day_id)

    r = await client.post(
        f"/sessions/{session_id}/logs",
        json={"workout_exercise_id": ex_id, "set_number": 1, "reps_completed": 8, "weight_kg": 100.0},
    )
    assert r.status_code == 201
    r = await client.post(
        f"/sessions/{session_id}/logs",
        json={"workout_exercise_id": ex_id, "set_number": 2, "reps_completed": 6, "weight_kg": 100.0},
    )
    assert r.status_code == 201
    await complete_session(client, session_id)

    r = await client.get("/sessions")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)  # bare array, no pagination envelope
    matches = [s for s in body if s["id"] == session_id]
    assert len(matches) == 1
    item = matches[0]
    assert item["workout_id"] == wid
    assert item["training_day_id"] == day_id
    assert item["workout_name"] == "History Workout"
    assert item["day_of_week"] == "MONDAY"
    assert item["status"] == "completed"
    assert item["completed_at"] is not None
    assert item["started_at"] is not None
    assert len(item["logs"]) == 2
    # Logs ordered by set_number, exercise name resolved server-side
    assert [log["set_number"] for log in item["logs"]] == [1, 2]
    log = item["logs"][0]
    # Catalog seed name for "hack-squat" (EXERCISE_SEED ships Spanish names)
    assert log["exercise_name"] == "Sentadilla hack"
    assert log["workout_exercise_id"] == ex_id
    assert log["reps_completed"] == 8
    assert log["weight_kg"] == 100.0


# ── 3. Status filter ──────────────────────────────────────────────────────────


async def test_history_filters_by_status(client) -> None:
    wid, day_id = await create_workout_with_day(client, "TUESDAY")
    completed_id = await start_session(client, wid, day_id)
    await complete_session(client, completed_id)
    in_progress_id = await start_session(client, wid, day_id)

    # Scope by workout_id so data from other tests never leaks in.
    r = await client.get(f"/sessions?workout_id={wid}&status=completed")
    assert r.status_code == 200
    assert [s["id"] for s in r.json()] == [completed_id]
    assert all(s["status"] == "completed" for s in r.json())

    r = await client.get(f"/sessions?workout_id={wid}&status=in_progress")
    assert r.status_code == 200
    assert [s["id"] for s in r.json()] == [in_progress_id]
    assert r.json()[0]["completed_at"] is None

    # No status filter → both, newest first
    r = await client.get(f"/sessions?workout_id={wid}")
    assert r.status_code == 200
    assert {s["id"] for s in r.json()} == {completed_id, in_progress_id}


# ── 4. Day filter ─────────────────────────────────────────────────────────────


async def test_history_filters_by_day(client) -> None:
    wid, day_id = await create_workout_with_day(client, "WEDNESDAY")
    r = await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": "FRIDAY"})
    assert r.status_code == 201
    r = await client.get(f"/workouts/{wid}")
    other_day_id = next(d["id"] for d in r.json()["training_days"] if d["id"] != day_id)

    sid_wed = await start_session(client, wid, day_id)
    sid_fri = await start_session(client, wid, other_day_id)

    r = await client.get(f"/sessions?workout_id={wid}&day_id={day_id}")
    assert r.status_code == 200
    assert [s["id"] for s in r.json()] == [sid_wed]

    r = await client.get(f"/sessions?workout_id={wid}&day_id={other_day_id}")
    assert r.status_code == 200
    assert [s["id"] for s in r.json()] == [sid_fri]


# ── 5. Cross-user scoping — silently empty, not 403 ──────────────────────────


async def test_history_other_users_workout_returns_empty(client, client_user2) -> None:
    wid, day_id = await create_workout_with_day(client_user2, "THURSDAY")
    await start_session(client_user2, wid, day_id)

    # user-1 asks for user-2's workout: 200 with empty page (user_id scoping)
    r = await client.get(f"/sessions?workout_id={wid}")
    assert r.status_code == 200
    assert r.json() == []

    # user-2 sees their own session
    r = await client_user2.get(f"/sessions?workout_id={wid}")
    assert r.status_code == 200
    assert len(r.json()) == 1


# ── 6. Date range filters ─────────────────────────────────────────────────────


async def test_history_filters_by_date_range(client) -> None:
    wid, day_id = await create_workout_with_day(client, "SATURDAY")
    sid = await start_session(client, wid, day_id)

    today = datetime.now(UTC).date()
    tomorrow = today + timedelta(days=1)

    r = await client.get(f"/sessions?workout_id={wid}&date_from={today}&date_to={today}")
    assert r.status_code == 200
    assert [s["id"] for s in r.json()] == [sid]

    r = await client.get(f"/sessions?workout_id={wid}&date_from={tomorrow}")
    assert r.status_code == 200
    assert r.json() == []

    yesterday = today - timedelta(days=1)
    r = await client.get(f"/sessions?workout_id={wid}&date_to={yesterday}")
    assert r.status_code == 200
    assert r.json() == []


# ── 7. Pagination ─────────────────────────────────────────────────────────────


async def test_history_pagination(client) -> None:
    wid, day_id = await create_workout_with_day(client, "SUNDAY")
    # Complete each session before starting the next: only one in-progress
    # session per day is allowed.
    ids = set()
    for _ in range(3):
        sid = await start_session(client, wid, day_id)
        await complete_session(client, sid)
        ids.add(sid)

    r = await client.get(f"/sessions?workout_id={wid}&limit=2")
    assert r.status_code == 200
    first_page = r.json()
    assert len(first_page) == 2

    r = await client.get(f"/sessions?workout_id={wid}&limit=2&offset=2")
    assert r.status_code == 200
    second_page = r.json()
    assert len(second_page) == 1

    assert {s["id"] for s in first_page + second_page} == ids


# ── 8. Validation — 422 ───────────────────────────────────────────────────────


async def test_history_invalid_limit_returns_422(client) -> None:
    r = await client.get("/sessions?limit=invalid")
    assert r.status_code == 422


async def test_history_limit_out_of_bounds_returns_422(client) -> None:
    assert (await client.get("/sessions?limit=0")).status_code == 422
    assert (await client.get("/sessions?limit=101")).status_code == 422
    assert (await client.get("/sessions?offset=-1")).status_code == 422


async def test_history_invalid_status_returns_422(client) -> None:
    r = await client.get("/sessions?status=bogus")
    assert r.status_code == 422


# ── 9. Query count guard — exactly 2 queries, zero N+1 ───────────────────────


async def test_history_fires_exactly_two_queries(client, engine) -> None:
    """Design constraint: sessions page + one IN query for logs.

    Guards against reintroducing the lazy="selectin" relationship load
    (a third query per page) or per-session log queries (N+1).
    """
    wid, day_id = await create_workout_with_day(client, "MONDAY")
    ex_id = await add_exercise_to_day(client, wid, "MONDAY", "deadlift")
    for _ in range(2):
        session_id = await start_session(client, wid, day_id)
        r = await client.post(
            f"/sessions/{session_id}/logs",
            json={"workout_exercise_id": ex_id, "set_number": 1, "reps_completed": 5},
        )
        assert r.status_code == 201
        # Complete before the next iteration: only one in-progress session per
        # day is allowed.
        await complete_session(client, session_id)

    statements: list[str] = []

    def _track(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", _track)
    try:
        r = await client.get(f"/sessions?workout_id={wid}")
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", _track)

    assert r.status_code == 200
    assert len(r.json()) == 2
    assert all(len(s["logs"]) == 1 for s in r.json())
    assert len(statements) == 2, f"expected 2 SELECTs, got {len(statements)}: {statements}"
