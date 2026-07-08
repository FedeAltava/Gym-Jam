"""HTTP tests for GET /users/me/stats."""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from backend.src.infrastructure.database import get_session
from backend.src.infrastructure.persistence.models import UserModel
from backend.src.main import create_app
from backend.src.presentation.dependencies import get_current_user_id

STATS_FIELDS = (
    "total_sessions",
    "streak",
    "total_prs",
    "weekly_volume_kg",
    "weekly_sessions",
    "weekly_prs",
)

_DAY_NAMES = (
    "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY",
)


@pytest.fixture
async def fresh_user_client(session) -> AsyncGenerator[AsyncClient, None]:
    """Client authenticated as a brand-new user with zero data.

    The shared stub users accumulate data across the HTTP suite (session-scoped
    in-memory DB), so deterministic stat assertions need their own user.
    """
    user_id = str(uuid.uuid4())
    session.add(
        UserModel(id=user_id, email=f"{user_id}@example.com", hashed_password="$stub$")
    )
    await session.commit()

    app = create_app()

    async def override_get_session():
        yield session

    def override_get_current_user_id() -> str:
        return user_id

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_get_user_stats_returns_200_with_valid_shape(client) -> None:
    r = await client.get("/users/me/stats")

    assert r.status_code == 200
    body = r.json()
    for field in STATS_FIELDS:
        assert field in body, f"missing field: {field}"
        assert body[field] >= 0
    assert isinstance(body["weekly_volume_kg"], (int, float))
    assert isinstance(body["streak"], int)


async def test_get_user_stats_requires_auth(auth_client) -> None:
    r = await auth_client.get("/users/me/stats")

    assert r.status_code == 401


async def test_get_user_stats_zero_state_for_new_user(fresh_user_client) -> None:
    r = await fresh_user_client.get("/users/me/stats")

    assert r.status_code == 200
    assert r.json() == {field: 0 for field in STATS_FIELDS}


async def test_get_user_stats_reflects_completed_session(fresh_user_client) -> None:
    client = fresh_user_client
    today_day = _DAY_NAMES[datetime.now(UTC).weekday()]

    r = await client.post("/workouts", json={"name": "Stats Workout", "training_days": []})
    assert r.status_code == 201
    wid = r.json()["id"]
    r = await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": today_day})
    assert r.status_code == 201
    r = await client.post(
        f"/workouts/{wid}/training-days/{today_day}/exercises",
        json={"exercise_id": "bench-press", "sets": 3},
    )
    assert r.status_code == 201
    ex_id = r.json()["id"]
    r = await client.get(f"/workouts/{wid}")
    day_id = r.json()["training_days"][0]["id"]

    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r.status_code == 201
    session_id = r.json()["id"]
    r = await client.post(
        f"/sessions/{session_id}/logs",
        json={
            "workout_exercise_id": ex_id,
            "set_number": 1,
            "reps_completed": 10,
            "weight_kg": 80.0,
        },
    )
    assert r.status_code == 201
    r = await client.post(f"/sessions/{session_id}/complete")
    assert r.status_code == 200

    r = await client.get("/users/me/stats")

    assert r.status_code == 200
    body = r.json()
    assert body["total_sessions"] == 1
    assert body["weekly_sessions"] == 1
    assert body["streak"] == 1  # today is a plan day with a completed session
    assert body["total_prs"] == 1  # first-ever weighted log is a PR
    assert body["weekly_prs"] == 1
    assert body["weekly_volume_kg"] == 800.0  # 10 reps × 80 kg
