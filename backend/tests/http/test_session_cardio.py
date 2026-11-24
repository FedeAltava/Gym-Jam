"""Treadmill cardio recorded in a workout session.

POST /sessions/{id}/cardio adds an entry, DELETE /sessions/{id}/cardio/{entry_id}
removes it; every session response carries the entries as `cardio`.
"""
from __future__ import annotations

import uuid

import pytest
import sqlalchemy

from backend.src.infrastructure.persistence.models import SessionCardioEntryModel

FULL_ENTRY = {
    "duration_minutes": 20,
    "distance_km": 2.5,
    "speed_kmh": 7.5,
    "incline_percent": 3.5,
    "calories": 250,
}


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _start_session(client) -> tuple[str, str, str]:
    """Create a workout with a Monday day and start a session. Returns (wid, day_id, session_id)."""
    r = await client.post("/workouts", json={"name": f"Cardio {uuid.uuid4().hex[:8]}", "training_days": []})
    assert r.status_code == 201
    wid = r.json()["id"]
    assert (await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": "MONDAY"})).status_code == 201
    day_id = (await client.get(f"/workouts/{wid}")).json()["training_days"][0]["id"]
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r.status_code == 201
    assert r.json()["cardio"] == []
    return wid, day_id, r.json()["id"]


async def _add_cardio(client, session_id: str, body: dict) -> dict:
    r = await client.post(f"/sessions/{session_id}/cardio", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def _cardio_rows(session, session_id: str) -> int:
    result = await session.execute(
        sqlalchemy.select(sqlalchemy.func.count())
        .select_from(SessionCardioEntryModel)
        .where(SessionCardioEntryModel.session_id == session_id)
    )
    return result.scalar_one()


# ── Add ──────────────────────────────────────────────────────────────────────


async def test_add_cardio_returns_the_entry_and_every_session_view_shows_it(client) -> None:
    wid, day_id, sid = await _start_session(client)

    entry = await _add_cardio(client, sid, FULL_ENTRY)

    assert uuid.UUID(entry["id"])
    assert {k: entry[k] for k in FULL_ENTRY} == FULL_ENTRY
    expected = [{"id": entry["id"], **FULL_ENTRY}]
    day_sessions = (await client.get(f"/workouts/{wid}/days/{day_id}/sessions")).json()
    assert [{k: e[k] for k in ("id", *FULL_ENTRY)} for e in day_sessions[0]["cardio"]] == expected
    detail = (await client.get(f"/sessions/{sid}")).json()
    assert [{k: e[k] for k in ("id", *FULL_ENTRY)} for e in detail["cardio"]] == expected
    listed = next(s for s in (await client.get("/sessions")).json()["items"] if s["id"] == sid)
    assert [{k: e[k] for k in ("id", *FULL_ENTRY)} for e in listed["cardio"]] == expected


async def test_add_cardio_with_some_values_leaves_the_rest_null(client) -> None:
    _, _, sid = await _start_session(client)

    entry = await _add_cardio(client, sid, {"duration_minutes": 25, "calories": 180})

    assert entry["duration_minutes"] == 25
    assert entry["calories"] == 180
    assert entry["distance_km"] is None
    assert entry["speed_kmh"] is None
    assert entry["incline_percent"] is None


async def test_cardio_entries_are_listed_in_the_order_they_were_added(client) -> None:
    _, _, sid = await _start_session(client)
    ids = [(await _add_cardio(client, sid, {"duration_minutes": minutes}))["id"] for minutes in (10, 20, 30)]

    detail = (await client.get(f"/sessions/{sid}")).json()

    assert [e["id"] for e in detail["cardio"]] == ids
    assert [e["duration_minutes"] for e in detail["cardio"]] == [10, 20, 30]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"duration_minutes": None, "distance_km": None},
        {"duration_minutes": 0},
        {"duration_minutes": -1},
        {"duration_minutes": 1441},
        {"duration_minutes": 20.5},
        {"distance_km": 0},
        {"speed_kmh": -2.0},
        {"incline_percent": -1},
        {"incline_percent": 41},
        {"calories": 0},
        {"calories": 20001},
        {"calories": "many"},
    ],
)
async def test_invalid_cardio_returns_422_and_stores_nothing(client, session, body) -> None:
    wid, day_id, sid = await _start_session(client)
    before = (await client.get(f"/workouts/{wid}/days/{day_id}/sessions")).content

    r = await client.post(f"/sessions/{sid}/cardio", json=body)

    assert r.status_code == 422
    assert await _cardio_rows(session, sid) == 0
    assert (await client.get(f"/workouts/{wid}/days/{day_id}/sessions")).content == before


async def test_incline_zero_is_valid(client) -> None:
    _, _, sid = await _start_session(client)

    entry = await _add_cardio(client, sid, {"incline_percent": 0})

    assert entry["incline_percent"] == 0


async def test_cardio_can_be_added_and_deleted_on_a_completed_session(client) -> None:
    _, _, sid = await _start_session(client)
    assert (await client.post(f"/sessions/{sid}/complete", json={})).status_code == 200

    entry = await _add_cardio(client, sid, {"distance_km": 3.0})
    assert [e["id"] for e in (await client.get(f"/sessions/{sid}")).json()["cardio"]] == [entry["id"]]

    assert (await client.delete(f"/sessions/{sid}/cardio/{entry['id']}")).status_code == 204
    assert (await client.get(f"/sessions/{sid}")).json()["cardio"] == []


async def test_add_cardio_to_unknown_or_malformed_session_returns_404(client) -> None:
    assert (await client.post(f"/sessions/{uuid.uuid4()}/cardio", json=FULL_ENTRY)).status_code == 404
    assert (await client.post("/sessions/not-a-uuid/cardio", json=FULL_ENTRY)).status_code == 404


async def test_add_cardio_to_another_users_session_is_forbidden(client, client_user2, session) -> None:
    _, _, sid = await _start_session(client)

    r = await client_user2.post(f"/sessions/{sid}/cardio", json=FULL_ENTRY)

    assert r.status_code == 403
    assert await _cardio_rows(session, sid) == 0


async def test_cardio_requires_auth(auth_client) -> None:
    sid = uuid.uuid4()
    assert (await auth_client.post(f"/sessions/{sid}/cardio", json=FULL_ENTRY)).status_code == 401
    assert (await auth_client.delete(f"/sessions/{sid}/cardio/{uuid.uuid4()}")).status_code == 401


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete_cardio_removes_only_that_entry(client, session) -> None:
    _, _, sid = await _start_session(client)
    kept = await _add_cardio(client, sid, {"duration_minutes": 10})
    removed = await _add_cardio(client, sid, {"duration_minutes": 20})

    r = await client.delete(f"/sessions/{sid}/cardio/{removed['id']}")

    assert r.status_code == 204
    assert [e["id"] for e in (await client.get(f"/sessions/{sid}")).json()["cardio"]] == [kept["id"]]
    assert await _cardio_rows(session, sid) == 1


async def test_delete_unknown_malformed_or_foreign_entry_returns_404(client, session) -> None:
    _, _, sid = await _start_session(client)
    await _add_cardio(client, sid, {"duration_minutes": 10})
    # An entry of another session of the same user is not part of this one.
    _, _, other_sid = await _start_session(client)
    other = await _add_cardio(client, other_sid, {"duration_minutes": 15})

    for entry_id in (str(uuid.uuid4()), "not-a-uuid", other["id"]):
        r = await client.delete(f"/sessions/{sid}/cardio/{entry_id}")
        assert r.status_code == 404, entry_id

    assert await _cardio_rows(session, sid) == 1
    assert await _cardio_rows(session, other_sid) == 1


async def test_delete_cardio_of_another_users_session_is_forbidden(client, client_user2, session) -> None:
    _, _, sid = await _start_session(client)
    entry = await _add_cardio(client, sid, {"duration_minutes": 10})

    r = await client_user2.delete(f"/sessions/{sid}/cardio/{entry['id']}")

    assert r.status_code == 403
    assert await _cardio_rows(session, sid) == 1


async def test_deleting_the_session_removes_its_cardio(client, session) -> None:
    _, _, sid = await _start_session(client)
    await _add_cardio(client, sid, FULL_ENTRY)

    assert (await client.delete(f"/sessions/{sid}")).status_code == 204

    assert await _cardio_rows(session, sid) == 0


async def test_logging_a_set_keeps_the_cardio(client) -> None:
    wid, _, sid = await _start_session(client)
    r = await client.post(
        f"/workouts/{wid}/training-days/MONDAY/exercises", json={"exercise_id": "bench-press", "sets": 3}
    )
    ex_id = r.json()["id"]
    entry = await _add_cardio(client, sid, FULL_ENTRY)

    r = await client.post(
        f"/sessions/{sid}/logs", json={"workout_exercise_id": ex_id, "set_number": 1, "reps_completed": 8}
    )

    assert r.status_code == 201
    assert [e["id"] for e in (await client.get(f"/sessions/{sid}")).json()["cardio"]] == [entry["id"]]
