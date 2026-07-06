"""HTTP tests for session endpoints (T25)."""
from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from backend.src.infrastructure.database import get_session
from backend.src.main import create_app
from backend.src.presentation.dependencies import get_current_user_id


# ── Helpers ──────────────────────────────────────────────────────────────────


async def create_workout_with_day(client, day: str = "MONDAY") -> tuple[str, str]:
    """Create workout + training day. Returns (workout_id, day_id)."""
    r = await client.post("/workouts", json={"name": "Session Workout", "training_days": []})
    assert r.status_code == 201
    wid = r.json()["id"]

    r2 = await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": day})
    assert r2.status_code == 201

    # GET the workout to retrieve the training day id
    r3 = await client.get(f"/workouts/{wid}")
    assert r3.status_code == 200
    days = r3.json()["training_days"]
    assert len(days) == 1
    day_id = days[0]["id"]
    return wid, day_id


async def add_exercise_to_day(client, wid: str, day: str = "MONDAY", exercise_id: str = "bench-press") -> str:
    """Add exercise to training day. Returns workout_exercise_id."""
    r = await client.post(
        f"/workouts/{wid}/training-days/{day}/exercises",
        json={"exercise_id": exercise_id, "sets": 3},
    )
    assert r.status_code == 201
    return r.json()["id"]


# ── 1. POST /api/workouts/{wid}/days/{day_id}/sessions — happy path ──────────

async def test_start_session_returns_201(client) -> None:
    wid, day_id = await create_workout_with_day(client)

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})

    assert r.status_code == 201
    data = r.json()
    assert data["workout_id"] == wid
    assert data["training_day_id"] == day_id
    assert data["status"] == "in_progress"
    assert data["completed_at"] is None
    assert data["logs"] == []


# ── 2. GET /api/workouts/{wid}/days/{day_id}/sessions — empty list ───────────

async def test_get_sessions_empty_returns_200(client) -> None:
    wid, day_id = await create_workout_with_day(client, "TUESDAY")

    r = await client.get(f"/workouts/{wid}/days/{day_id}/sessions")

    assert r.status_code == 200
    assert r.json() == []


# ── 3. Full flow: start → log sets → complete ────────────────────────────────

async def test_full_session_flow(client) -> None:
    wid, day_id = await create_workout_with_day(client, "WEDNESDAY")
    ex_id = await add_exercise_to_day(client, wid, "WEDNESDAY", "squat")

    # Start session
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r.status_code == 201
    session_id = r.json()["id"]

    # Log set 1
    log_payload = {
        "workout_exercise_id": ex_id,
        "set_number": 1,
        "reps_completed": 10,
        "weight_kg": 80.0,
    }
    r2 = await client.post(f"/sessions/{session_id}/logs", json=log_payload)
    assert r2.status_code == 201
    log_data = r2.json()
    assert log_data["set_number"] == 1
    assert log_data["reps_completed"] == 10
    assert log_data["weight_kg"] == 80.0

    # Log set 2
    log2 = {**log_payload, "set_number": 2, "reps_completed": 9}
    r3 = await client.post(f"/sessions/{session_id}/logs", json=log2)
    assert r3.status_code == 201

    # Complete session
    r4 = await client.post(f"/sessions/{session_id}/complete", json={})
    assert r4.status_code == 200
    completed = r4.json()
    assert completed["status"] == "completed"
    assert completed["completed_at"] is not None

    # GET sessions — should include the session with logs
    r5 = await client.get(f"/workouts/{wid}/days/{day_id}/sessions")
    assert r5.status_code == 200
    sessions = r5.json()
    assert len(sessions) == 1
    assert len(sessions[0]["logs"]) == 2


# ── 4. Auth required — 401 ────────────────────────────────────────────────────

async def test_start_session_requires_auth(auth_client) -> None:
    r = await auth_client.post(
        "/workouts/00000000-0000-0000-0000-000000000001/days/00000000-0000-0000-0000-000000000002/sessions",
        json={},
    )
    assert r.status_code == 401


async def test_log_set_requires_auth(auth_client) -> None:
    r = await auth_client.post(
        "/sessions/00000000-0000-0000-0000-000000000001/logs",
        json={"workout_exercise_id": "x", "set_number": 1, "reps_completed": 5},
    )
    assert r.status_code == 401


async def test_complete_session_requires_auth(auth_client) -> None:
    r = await auth_client.post(
        "/sessions/00000000-0000-0000-0000-000000000001/complete",
        json={},
    )
    assert r.status_code == 401


async def test_get_sessions_requires_auth(auth_client) -> None:
    r = await auth_client.get(
        "/workouts/00000000-0000-0000-0000-000000000001/days/00000000-0000-0000-0000-000000000002/sessions"
    )
    assert r.status_code == 401


# ── 5. Start session — workout not found → 404 ────────────────────────────────

async def test_start_session_workout_not_found_returns_404(client) -> None:
    r = await client.post(
        "/workouts/00000000-0000-0000-0000-000000000099/days/00000000-0000-0000-0000-000000000099/sessions",
        json={},
    )
    assert r.status_code == 404


# ── 6. Log set — set_number=0 → Pydantic 422 ─────────────────────────────────

async def test_log_set_set_number_zero_returns_422(client) -> None:
    wid, day_id = await create_workout_with_day(client, "THURSDAY")
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    session_id = r.json()["id"]

    r2 = await client.post(
        f"/sessions/{session_id}/logs",
        json={"workout_exercise_id": "x", "set_number": 0, "reps_completed": 5, "weight_kg": 50.0},
    )
    assert r2.status_code == 422


# ── 7. Log set — reps_completed=0 → Pydantic 422 ─────────────────────────────

async def test_log_set_reps_zero_returns_422(client) -> None:
    wid, day_id = await create_workout_with_day(client, "FRIDAY")
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    session_id = r.json()["id"]

    r2 = await client.post(
        f"/sessions/{session_id}/logs",
        json={"workout_exercise_id": "x", "set_number": 1, "reps_completed": 0, "weight_kg": 50.0},
    )
    assert r2.status_code == 422


# ── 8. Log set — set_number exceeds plan → DomainViolation 422 ──────────────

async def test_log_set_exceeds_plan_returns_422(client) -> None:
    wid, day_id = await create_workout_with_day(client, "SATURDAY")
    ex_id = await add_exercise_to_day(client, wid, "SATURDAY", "deadlift")

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    session_id = r.json()["id"]

    # Exercise has sets=3; set_number=4 should fail
    r2 = await client.post(
        f"/sessions/{session_id}/logs",
        json={"workout_exercise_id": ex_id, "set_number": 4, "reps_completed": 5, "weight_kg": 50.0},
    )
    assert r2.status_code == 422


# ── 9. Log set — duplicate → 409 ─────────────────────────────────────────────

async def test_log_set_duplicate_returns_409(client) -> None:
    wid, day_id = await create_workout_with_day(client, "SUNDAY")
    ex_id = await add_exercise_to_day(client, wid, "SUNDAY", "pull-up")

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    session_id = r.json()["id"]

    payload = {"workout_exercise_id": ex_id, "set_number": 1, "reps_completed": 8, "weight_kg": 40.0}
    r1 = await client.post(f"/sessions/{session_id}/logs", json=payload)
    assert r1.status_code == 201

    r2 = await client.post(f"/sessions/{session_id}/logs", json=payload)
    assert r2.status_code == 409


# ── 9b. PATCH /sessions/{sid}/logs/{lid} — update an existing log ────────────

async def test_update_log_returns_200(client) -> None:
    wid, day_id = await create_workout_with_day(client, "MONDAY")
    ex_id = await add_exercise_to_day(client, wid, "MONDAY", "bench-press")

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    session_id = r.json()["id"]

    r1 = await client.post(
        f"/sessions/{session_id}/logs",
        json={"workout_exercise_id": ex_id, "set_number": 1, "reps_completed": 8, "weight_kg": 40.0},
    )
    assert r1.status_code == 201
    log_id = r1.json()["id"]

    r2 = await client.patch(
        f"/sessions/{session_id}/logs/{log_id}",
        json={"reps_completed": 10, "weight_kg": 45.0},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["id"] == log_id
    assert data["reps_completed"] == 10
    assert data["weight_kg"] == 45.0


async def test_update_log_partial_only_weight(client) -> None:
    wid, day_id = await create_workout_with_day(client, "TUESDAY")
    ex_id = await add_exercise_to_day(client, wid, "TUESDAY", "squat")

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    session_id = r.json()["id"]

    r1 = await client.post(
        f"/sessions/{session_id}/logs",
        json={"workout_exercise_id": ex_id, "set_number": 1, "reps_completed": 8, "weight_kg": 40.0},
    )
    assert r1.status_code == 201
    log_id = r1.json()["id"]

    r2 = await client.patch(
        f"/sessions/{session_id}/logs/{log_id}",
        json={"weight_kg": 42.5},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["reps_completed"] == 8  # unchanged
    assert data["weight_kg"] == 42.5


async def test_update_log_not_found_returns_404(client) -> None:
    wid, day_id = await create_workout_with_day(client, "WEDNESDAY")

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    session_id = r.json()["id"]

    r2 = await client.patch(
        f"/sessions/{session_id}/logs/00000000-0000-0000-0000-000000000099",
        json={"reps_completed": 10},
    )
    assert r2.status_code == 404


async def test_update_log_session_not_found_returns_404(client) -> None:
    r = await client.patch(
        "/sessions/00000000-0000-0000-0000-000000000099/logs/00000000-0000-0000-0000-000000000099",
        json={"reps_completed": 10},
    )
    assert r.status_code == 404


async def test_update_log_requires_auth(auth_client) -> None:
    r = await auth_client.patch(
        "/sessions/00000000-0000-0000-0000-000000000001/logs/00000000-0000-0000-0000-000000000002",
        json={"reps_completed": 10},
    )
    assert r.status_code == 401


# ── 10. Complete session — idempotent returns 200 ────────────────────────────

async def test_complete_session_idempotent(client) -> None:
    wid, day_id = await create_workout_with_day(client, "MONDAY")

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    session_id = r.json()["id"]

    r1 = await client.post(f"/sessions/{session_id}/complete", json={})
    assert r1.status_code == 200
    completed_at = r1.json()["completed_at"]

    r2 = await client.post(f"/sessions/{session_id}/complete", json={})
    assert r2.status_code == 200
    assert r2.json()["completed_at"] == completed_at


# ── 11. Multiple sessions same day ───────────────────────────────────────────

async def test_multiple_sessions_same_day(client) -> None:
    wid, day_id = await create_workout_with_day(client, "TUESDAY")

    r1 = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    r2 = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]

    r3 = await client.get(f"/workouts/{wid}/days/{day_id}/sessions")
    assert r3.status_code == 200
    assert len(r3.json()) == 2


# ── 12. DELETE /sessions/{session_id} ─────────────────────────────────────────


@pytest.fixture
async def client_user2(session) -> AsyncGenerator[AsyncClient, None]:
    """Client authenticated as a DIFFERENT user, sharing the same DB session."""
    app = create_app()

    async def override_get_session():
        yield session

    def override_get_current_user_id() -> str:
        return "00000000-0000-0000-0000-000000000002"

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_delete_session_returns_204_and_removes_it(client) -> None:
    wid, day_id = await create_workout_with_day(client, "MONDAY")

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r.status_code == 201
    session_id = r.json()["id"]

    r2 = await client.delete(f"/sessions/{session_id}")
    assert r2.status_code == 204

    r3 = await client.get(f"/workouts/{wid}/days/{day_id}/sessions")
    assert r3.status_code == 200
    assert all(s["id"] != session_id for s in r3.json())


async def test_delete_session_with_logs_returns_204(client) -> None:
    wid, day_id = await create_workout_with_day(client, "TUESDAY")
    ex_id = await add_exercise_to_day(client, wid, "TUESDAY", "squat")

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    session_id = r.json()["id"]

    r1 = await client.post(
        f"/sessions/{session_id}/logs",
        json={"workout_exercise_id": ex_id, "set_number": 1, "reps_completed": 10, "weight_kg": 80.0},
    )
    assert r1.status_code == 201

    r2 = await client.delete(f"/sessions/{session_id}")
    assert r2.status_code == 204

    r3 = await client.get(f"/workouts/{wid}/days/{day_id}/sessions")
    assert r3.status_code == 200
    assert all(s["id"] != session_id for s in r3.json())


async def test_delete_session_other_user_returns_403(client, client_user2) -> None:
    wid, day_id = await create_workout_with_day(client, "WEDNESDAY")

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    session_id = r.json()["id"]

    r2 = await client_user2.delete(f"/sessions/{session_id}")
    assert r2.status_code == 403

    # Session must still exist for its owner
    r3 = await client.get(f"/workouts/{wid}/days/{day_id}/sessions")
    assert any(s["id"] == session_id for s in r3.json())


async def test_delete_session_not_found_returns_404(client) -> None:
    r = await client.delete("/sessions/00000000-0000-0000-0000-000000000099")
    assert r.status_code == 404


# ── T27: Plan fields on add-exercise endpoint ────────────────────────────────

async def test_add_exercise_with_plan_fields_round_trips(client) -> None:
    wid, _day_id = await create_workout_with_day(client, "WEDNESDAY")

    r = await client.post(
        f"/workouts/{wid}/training-days/WEDNESDAY/exercises",
        json={"exercise_id": "bench-press", "sets": 4, "reps_per_set": 8, "weight_kg": 60.0},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["sets"] == 4
    assert data["reps_per_set"] == 8
    assert data["weight_kg"] == 60.0


async def test_add_exercise_without_plan_fields_uses_defaults(client) -> None:
    wid, _day_id = await create_workout_with_day(client, "THURSDAY")

    r = await client.post(
        f"/workouts/{wid}/training-days/THURSDAY/exercises",
        json={"exercise_id": "squat"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["sets"] == 3
    assert data["reps_per_set"] == 10
    assert data["weight_kg"] is None


async def test_add_exercise_partial_plan_fields(client) -> None:
    wid, _day_id = await create_workout_with_day(client, "FRIDAY")

    r = await client.post(
        f"/workouts/{wid}/training-days/FRIDAY/exercises",
        json={"exercise_id": "deadlift", "sets": 5},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["sets"] == 5
    assert data["reps_per_set"] == 10
    assert data["weight_kg"] is None


async def test_add_exercise_sets_zero_returns_422(client) -> None:
    wid, _day_id = await create_workout_with_day(client, "SATURDAY")

    r = await client.post(
        f"/workouts/{wid}/training-days/SATURDAY/exercises",
        json={"exercise_id": "bench-press", "sets": 0},
    )
    assert r.status_code == 422


async def test_add_exercise_weight_negative_returns_422(client) -> None:
    wid, _day_id = await create_workout_with_day(client, "SUNDAY")

    r = await client.post(
        f"/workouts/{wid}/training-days/SUNDAY/exercises",
        json={"exercise_id": "bench-press", "weight_kg": -1.0},
    )
    assert r.status_code == 422


async def test_get_workout_returns_plan_fields(client) -> None:
    wid, _day_id = await create_workout_with_day(client, "MONDAY")
    await client.post(
        f"/workouts/{wid}/training-days/MONDAY/exercises",
        json={"exercise_id": "bench-press", "sets": 4, "reps_per_set": 8, "weight_kg": 60.0},
    )

    r = await client.get(f"/workouts/{wid}")
    assert r.status_code == 200
    exercises = r.json()["training_days"][0]["exercises"]
    assert len(exercises) == 1
    ex = exercises[0]
    assert ex["sets"] == 4
    assert ex["reps_per_set"] == 8
    assert ex["weight_kg"] == 60.0
