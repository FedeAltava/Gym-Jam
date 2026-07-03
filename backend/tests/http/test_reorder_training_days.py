"""HTTP tests for PUT /workouts/{id}/training-days/reorder."""
import pytest


async def _create_workout_with_days(client, name: str = "Reorder Days Test") -> dict:
    r = await client.post(
        "/workouts",
        json={"name": name, "training_days": ["MONDAY", "TUESDAY", "WEDNESDAY"]},
    )
    assert r.status_code == 201
    return r.json()


async def test_reorder_training_days_returns_200(client) -> None:
    workout = await _create_workout_with_days(client)
    wid = workout["id"]
    days = workout["training_days"]
    # days are sorted by order (all 1 initially — stable sort preserves insertion)
    day_ids = [d["id"] for d in days]
    # Reverse the order
    r = await client.put(
        f"/workouts/{wid}/training-days/reorder",
        json={"ordered_day_ids": list(reversed(day_ids))},
    )
    assert r.status_code == 200
    data = r.json()
    returned_ids = [d["id"] for d in data["training_days"]]
    assert returned_ids == list(reversed(day_ids))


async def test_reorder_training_days_auth_required(auth_client) -> None:
    r = await auth_client.put(
        "/workouts/00000000-0000-0000-0000-000000000001/training-days/reorder",
        json={"ordered_day_ids": []},
    )
    assert r.status_code == 401


async def test_reorder_training_days_workout_not_found(client) -> None:
    r = await client.put(
        "/workouts/00000000-0000-0000-0000-000000000999/training-days/reorder",
        json={"ordered_day_ids": ["00000000-0000-0000-0000-000000000001"]},
    )
    assert r.status_code == 404


async def test_reorder_training_days_mismatch_returns_422(client) -> None:
    workout = await _create_workout_with_days(client, "Mismatch Test")
    wid = workout["id"]
    days = workout["training_days"]
    # Only send one id out of three → mismatch
    r = await client.put(
        f"/workouts/{wid}/training-days/reorder",
        json={"ordered_day_ids": [days[0]["id"]]},
    )
    assert r.status_code == 422
