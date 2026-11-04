"""Edge cases for session exercise swaps.

Complements test_sessions.py: cross-day slots, invariants after rejected
commands, routine edits while a swap exists, swap-row cleanup.
"""
from __future__ import annotations

import sqlalchemy

from backend.src.infrastructure.persistence.models import SessionExerciseSwapModel


async def _workout_with_two_days(client, name: str) -> tuple[str, dict[str, str]]:
    r = await client.post("/workouts", json={"name": name, "training_days": []})
    assert r.status_code == 201
    wid = r.json()["id"]
    for day in ("MONDAY", "THURSDAY"):
        assert (await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": day})).status_code == 201
    days = (await client.get(f"/workouts/{wid}")).json()["training_days"]
    return wid, {d["day_of_week"]: d["id"] for d in days}


async def _add(client, wid: str, day: str, exercise_id: str) -> str:
    r = await client.post(f"/workouts/{wid}/training-days/{day}/exercises", json={"exercise_id": exercise_id, "sets": 3})
    assert r.status_code == 201
    return r.json()["id"]


async def _start(client, wid: str, day_id: str) -> str:
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r.status_code == 201
    assert r.json()["swaps"] == []
    return r.json()["id"]


async def _day_sessions_bytes(client, wid: str, day_id: str) -> bytes:
    r = await client.get(f"/workouts/{wid}/days/{day_id}/sessions")
    assert r.status_code == 200
    return r.content


async def _swap_rows(session, session_id: str) -> list[tuple[str, str]]:
    rows = await session.execute(
        sqlalchemy.select(SessionExerciseSwapModel.workout_exercise_id, SessionExerciseSwapModel.exercise_id).where(
            SessionExerciseSwapModel.session_id == session_id
        )
    )
    return [tuple(r) for r in rows.all()]


async def test_swap_slot_of_another_day_of_same_workout_returns_404_and_changes_nothing(client) -> None:
    wid, days = await _workout_with_two_days(client, "Probe cross-day")
    await _add(client, wid, "MONDAY", "bench-press")
    thu_ex = await _add(client, wid, "THURSDAY", "hack-squat")
    sid = await _start(client, wid, days["MONDAY"])
    before = await _day_sessions_bytes(client, wid, days["MONDAY"])

    r = await client.put(f"/sessions/{sid}/exercises/{thu_ex}/swap", json={"exercise_id": "dumbbell-fly"})

    assert r.status_code == 404
    assert await _day_sessions_bytes(client, wid, days["MONDAY"]) == before
    assert (await client.get(f"/sessions/{sid}")).json()["logs"] == []


async def test_rejected_swaps_leave_session_byte_identical(client, client_user2) -> None:
    wid, days = await _workout_with_two_days(client, "Probe invariants")
    ex = await _add(client, wid, "MONDAY", "bench-press")
    sid = await _start(client, wid, days["MONDAY"])
    assert (await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "dumbbell-fly"})).status_code == 200
    before = await _day_sessions_bytes(client, wid, days["MONDAY"])

    # unknown catalog exercise
    assert (await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "no-such-exercise"})).status_code == 404
    assert await _day_sessions_bytes(client, wid, days["MONDAY"]) == before
    # empty body value
    assert (await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": ""})).status_code == 422
    assert await _day_sessions_bytes(client, wid, days["MONDAY"]) == before
    # unknown slot id
    assert (await client.put(f"/sessions/{sid}/exercises/not-a-slot/swap", json={"exercise_id": "dumbbell-fly"})).status_code == 404
    assert await _day_sessions_bytes(client, wid, days["MONDAY"]) == before
    # unknown session
    assert (await client.put("/sessions/not-a-session/exercises/x/swap", json={"exercise_id": "dumbbell-fly"})).status_code == 404
    # other user: swap and undo both 403
    assert (await client_user2.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "push-up"})).status_code == 403
    assert (await client_user2.delete(f"/sessions/{sid}/exercises/{ex}/swap")).status_code == 403
    assert await _day_sessions_bytes(client, wid, days["MONDAY"]) == before
    # completed: swap and undo both 409
    assert (await client.post(f"/sessions/{sid}/complete")).status_code == 200
    completed = await _day_sessions_bytes(client, wid, days["MONDAY"])
    assert (await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "push-up"})).status_code == 409
    assert (await client.delete(f"/sessions/{sid}/exercises/{ex}/swap")).status_code == 409
    assert await _day_sessions_bytes(client, wid, days["MONDAY"]) == completed
    detail = (await client.get(f"/sessions/{sid}")).json()
    assert detail["id"] == sid


async def test_put_with_planned_exercise_undoes_swap(client, session) -> None:
    wid, days = await _workout_with_two_days(client, "Probe put-undo")
    ex = await _add(client, wid, "MONDAY", "bench-press")
    sid = await _start(client, wid, days["MONDAY"])
    assert (await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "dumbbell-fly"})).status_code == 200
    assert await _swap_rows(session, sid) == [(ex, "dumbbell-fly")]

    r = await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "bench-press"})

    assert r.status_code == 200
    assert r.json()["swaps"] == []
    assert await _swap_rows(session, sid) == []
    # undo of a slot with no swap is also a 200 no-op
    r = await client.delete(f"/sessions/{sid}/exercises/{ex}/swap")
    assert r.status_code == 200
    assert r.json()["swaps"] == []


async def test_reswap_updates_single_row_and_survives_reload(client, session) -> None:
    wid, days = await _workout_with_two_days(client, "Probe reswap")
    ex1 = await _add(client, wid, "MONDAY", "bench-press")
    ex2 = await _add(client, wid, "MONDAY", "cable-crossover")
    sid = await _start(client, wid, days["MONDAY"])
    assert (await client.put(f"/sessions/{sid}/exercises/{ex1}/swap", json={"exercise_id": "dumbbell-fly"})).status_code == 200
    assert (await client.put(f"/sessions/{sid}/exercises/{ex2}/swap", json={"exercise_id": "push-up"})).status_code == 200
    r = await client.put(f"/sessions/{sid}/exercises/{ex1}/swap", json={"exercise_id": "incline-bench-press"})
    assert r.status_code == 200
    assert sorted(await _swap_rows(session, sid)) == sorted([(ex1, "incline-bench-press"), (ex2, "push-up")])

    listed = (await client.get(f"/workouts/{wid}/days/{days['MONDAY']}/sessions")).json()
    assert len(listed) == 1
    assert sorted((s["workout_exercise_id"], s["exercise_id"]) for s in listed[0]["swaps"]) == sorted(
        [(ex1, "incline-bench-press"), (ex2, "push-up")]
    )
    # routine plan untouched
    plan = (await client.get(f"/workouts/{wid}")).json()["training_days"]
    monday = next(d for d in plan if d["day_of_week"] == "MONDAY")
    assert [e["exercise_id"] for e in monday["exercises"]] == ["bench-press", "cable-crossover"]


async def test_swap_allowed_again_after_deleting_logged_set(client) -> None:
    wid, days = await _workout_with_two_days(client, "Probe log-delete")
    ex = await _add(client, wid, "MONDAY", "bench-press")
    sid = await _start(client, wid, days["MONDAY"])
    r = await client.post(f"/sessions/{sid}/logs", json={"workout_exercise_id": ex, "set_number": 1, "reps_completed": 8, "weight_kg": 50})
    assert r.status_code == 201
    log_id = r.json()["id"]
    assert (await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "dumbbell-fly"})).status_code == 409
    assert (await client.delete(f"/sessions/{sid}/logs/{log_id}")).status_code == 204

    r = await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "dumbbell-fly"})

    assert r.status_code == 200
    assert r.json()["swaps"] == [{"workout_exercise_id": ex, "exercise_id": "dumbbell-fly"}]
    # logging on the swapped slot keeps the swap and the log points at the slot
    r = await client.post(f"/sessions/{sid}/logs", json={"workout_exercise_id": ex, "set_number": 1, "reps_completed": 12, "weight_kg": 20})
    assert r.status_code == 201
    assert r.json()["workout_exercise_id"] == ex
    listed = (await client.get(f"/workouts/{wid}/days/{days['MONDAY']}/sessions")).json()
    assert listed[0]["swaps"] == [{"workout_exercise_id": ex, "exercise_id": "dumbbell-fly"}]
    assert [log["workout_exercise_id"] for log in listed[0]["logs"]] == [ex]
    assert (await client.delete(f"/sessions/{sid}/exercises/{ex}/swap")).status_code == 409


async def test_delete_session_removes_swap_rows(client, session) -> None:
    wid, days = await _workout_with_two_days(client, "Probe delete-session")
    ex = await _add(client, wid, "MONDAY", "bench-press")
    sid = await _start(client, wid, days["MONDAY"])
    assert (await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "dumbbell-fly"})).status_code == 200
    assert len(await _swap_rows(session, sid)) == 1

    assert (await client.delete(f"/sessions/{sid}")).status_code == 204

    assert await _swap_rows(session, sid) == []
    assert (await client.get(f"/sessions/{sid}")).status_code == 404


async def test_removing_planned_exercise_from_routine_cascades_swap(client, session) -> None:
    wid, days = await _workout_with_two_days(client, "Probe routine-remove")
    ex = await _add(client, wid, "MONDAY", "bench-press")
    keep = await _add(client, wid, "MONDAY", "cable-crossover")
    sid = await _start(client, wid, days["MONDAY"])
    assert (await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "dumbbell-fly"})).status_code == 200
    assert (await client.put(f"/sessions/{sid}/exercises/{keep}/swap", json={"exercise_id": "push-up"})).status_code == 200

    assert (await client.delete(f"/workouts/{wid}/training-days/MONDAY/exercises/{ex}")).status_code == 204

    assert await _swap_rows(session, sid) == [(keep, "push-up")]
    listed = (await client.get(f"/workouts/{wid}/days/{days['MONDAY']}/sessions")).json()
    assert listed[0]["swaps"] == [{"workout_exercise_id": keep, "exercise_id": "push-up"}]
    assert (await client.get(f"/sessions/{sid}")).status_code == 200
    # session still usable
    assert (await client.post(f"/sessions/{sid}/logs", json={"workout_exercise_id": keep, "set_number": 1, "reps_completed": 10, "weight_kg": None})).status_code == 201
    assert (await client.post(f"/sessions/{sid}/complete")).status_code == 200


async def test_deleting_whole_workout_with_swapped_session(client, session) -> None:
    wid, days = await _workout_with_two_days(client, "Probe workout-delete")
    ex = await _add(client, wid, "MONDAY", "bench-press")
    sid = await _start(client, wid, days["MONDAY"])
    assert (await client.put(f"/sessions/{sid}/exercises/{ex}/swap", json={"exercise_id": "dumbbell-fly"})).status_code == 200

    assert (await client.delete(f"/workouts/{wid}")).status_code == 204

    assert await _swap_rows(session, sid) == []
