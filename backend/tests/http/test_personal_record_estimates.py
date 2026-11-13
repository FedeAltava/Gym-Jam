"""HTTP regression tests: personal records by estimated one-rep max (from the feature verification)."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from backend.src.infrastructure.persistence.models import PersonalRecordModel
from backend.tests.http.test_idle_sessions import _ago, _backdate, _log_set, _start
from backend.tests.http.test_personal_records import add_exercise_to_day, create_workout_with_day


async def _session_with_sets(client, wid, day_id, ex_id, sets):
    r = await client.post(f"/workouts/{wid}/days/{day_id}/sessions", json={})
    assert r.status_code == 201
    sid = r.json()["id"]
    for n, (w, reps) in enumerate(sets, start=1):
        r2 = await client.post(
            f"/sessions/{sid}/logs",
            json={"workout_exercise_id": ex_id, "set_number": n, "reps_completed": reps, "weight_kg": w},
        )
        assert r2.status_code == 201, r2.text
    return sid


async def _complete(client, sid):
    r = await client.post(f"/sessions/{sid}/complete", json={})
    assert r.status_code == 200, r.text


async def _item(client, sid):
    r = await client.get(f"/sessions/{sid}")
    assert r.status_code == 200
    return r.json()


async def test_proposal_examples(client):
    wid, day_id = await create_workout_with_day(client, "MONDAY")
    ex = await add_exercise_to_day(client, wid, "MONDAY", "bench-press")
    s1 = await _session_with_sets(client, wid, day_id, ex, [(80.0, 10)])
    await _complete(client, s1)
    i1 = await _item(client, s1)
    assert i1["pr_count"] == 1 and len(i1["records"]) == 1
    assert i1["records"][0] == {"exercise_id": "bench-press", "weight_kg": 80.0, "reps": 10, "estimated_one_rep_max_kg": 106.7}
    # 82.5 x 3 ≈ 90.75 → not a record after 80 x 10
    s2 = await _session_with_sets(client, wid, day_id, ex, [(82.5, 3)])
    await _complete(client, s2)
    i2 = await _item(client, s2)
    assert i2["pr_count"] == 0 and i2["records"] == []
    # 80 x 12 ≈ 112 → record
    s3 = await _session_with_sets(client, wid, day_id, ex, [(80.0, 12)])
    await _complete(client, s3)
    i3 = await _item(client, s3)
    assert i3["records"][0]["reps"] == 12 and i3["records"][0]["estimated_one_rep_max_kg"] == 112.0
    # the older record row moved: s1 now holds nothing
    i1b = await _item(client, s1)
    assert i1b["pr_count"] == 0 and i1b["records"] == []
    # logs carry exercise_id
    assert all(log["exercise_id"] == "bench-press" for log in i3["logs"])


async def test_example_80x8_then_80x12(client):
    wid, day_id = await create_workout_with_day(client, "TUESDAY")
    ex = await add_exercise_to_day(client, wid, "TUESDAY", "deadlift")
    s1 = await _session_with_sets(client, wid, day_id, ex, [(80.0, 8)])
    await _complete(client, s1)
    assert (await _item(client, s1))["records"][0]["estimated_one_rep_max_kg"] == 101.3
    s2 = await _session_with_sets(client, wid, day_id, ex, [(80.0, 12)])
    await _complete(client, s2)
    assert (await _item(client, s2))["pr_count"] == 1


async def test_tie_at_tenth_kg(client):
    wid, day_id = await create_workout_with_day(client, "WEDNESDAY")
    ex = await add_exercise_to_day(client, wid, "WEDNESDAY", "overhead-press")
    s1 = await _session_with_sets(client, wid, day_id, ex, [(90.0, 1)])  # 93.0
    await _complete(client, s1)
    s2 = await _session_with_sets(client, wid, day_id, ex, [(87.225, 2)])  # 93.04 → 93.0 tie
    await _complete(client, s2)
    assert (await _item(client, s2))["pr_count"] == 0
    s3 = await _session_with_sets(client, wid, day_id, ex, [(87.5, 2)])  # 93.33 → 93.3 record
    await _complete(client, s3)
    assert (await _item(client, s3))["pr_count"] == 1
    assert (await _item(client, s1))["pr_count"] == 0


async def test_exact_tie_is_not_a_record(client):
    wid, day_id = await create_workout_with_day(client, "THURSDAY")
    ex = await add_exercise_to_day(client, wid, "THURSDAY", "hack-squat")
    s1 = await _session_with_sets(client, wid, day_id, ex, [(60.0, 5)])  # 70.0
    await _complete(client, s1)
    s2 = await _session_with_sets(client, wid, day_id, ex, [(52.5, 10)])  # 70.0
    await _complete(client, s2)
    assert (await _item(client, s2))["pr_count"] == 0
    assert (await _item(client, s1))["pr_count"] == 1


async def test_best_set_within_session_and_heaviest_not_marked(client):
    wid, day_id = await create_workout_with_day(client, "FRIDAY")
    ex = await add_exercise_to_day(client, wid, "FRIDAY", "bench-press")
    s1 = await _session_with_sets(client, wid, day_id, ex, [(100.0, 1), (80.0, 10), (80.0, 10)])
    await _complete(client, s1)
    item = await _item(client, s1)
    assert item["records"] == [{"exercise_id": "bench-press", "weight_kg": 80.0, "reps": 10, "estimated_one_rep_max_kg": 106.7}]
    assert item["pr_count"] == 1


async def test_zero_and_null_weight_never_record(client):
    wid, day_id = await create_workout_with_day(client, "SATURDAY")
    ex = await add_exercise_to_day(client, wid, "SATURDAY", "deadlift")
    s1 = await _session_with_sets(client, wid, day_id, ex, [(0.0, 20), (None, 30)])
    await _complete(client, s1)
    assert (await _item(client, s1))["records"] == []
    # a zero-weight prior set does not block a real first record either
    s2 = await _session_with_sets(client, wid, day_id, ex, [(20.0, 1)])
    await _complete(client, s2)
    assert (await _item(client, s2))["pr_count"] == 1


async def test_recomplete_idempotent(client):
    wid, day_id = await create_workout_with_day(client, "SUNDAY")
    ex = await add_exercise_to_day(client, wid, "SUNDAY", "overhead-press")
    s1 = await _session_with_sets(client, wid, day_id, ex, [(40.0, 8)])
    await _complete(client, s1)
    r = await client.post(f"/sessions/{s1}/complete", json={})
    assert r.status_code in (200, 409), r.text
    assert (await _item(client, s1))["pr_count"] == 1


async def test_idle_autocomplete_stores_reps(client, session):
    wid, _, ex_id, sid = await _start(client, "MONDAY")
    log_id = await _log_set(client, sid, ex_id)  # 80 x 10
    last = _ago(hours=2)
    await _backdate(session, sid, last - timedelta(hours=1), log_id, last)
    r = await client.get("/sessions", params={"workout_id": wid})
    item = next(s for s in r.json()["items"] if s["id"] == sid)
    assert item["pr_count"] == 1 and item["records"][0]["reps"] == 10
    rows = (await session.execute(select(PersonalRecordModel).where(PersonalRecordModel.session_id == sid))).scalars().all()
    assert [(x.weight_kg, x.reps) for x in rows] == [(80.0, 10)]


async def test_other_users_records_do_not_leak(client, client_user2):
    wid, day_id = await create_workout_with_day(client, "MONDAY")
    ex = await add_exercise_to_day(client, wid, "MONDAY", "bench-press")
    s1 = await _session_with_sets(client, wid, day_id, ex, [(70.0, 10)])
    await _complete(client, s1)
    wid2, day2 = await create_workout_with_day(client_user2, "MONDAY")
    ex2 = await add_exercise_to_day(client_user2, wid2, "MONDAY", "bench-press")
    s2 = await _session_with_sets(client_user2, wid2, day2, ex2, [(50.0, 10)])
    await _complete(client_user2, s2)
    # user2's first bench is their own record, independent of user1's heavier one
    assert (await _item(client_user2, s2))["pr_count"] == 1
    r = await client_user2.get(f"/sessions/{s1}")
    assert r.status_code in (403, 404)
    r = await client.get("/sessions", params={"page_size": 100})
    assert all(it["id"] != s2 for it in r.json()["items"])
