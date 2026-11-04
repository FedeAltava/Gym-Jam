"""HTTP tests for the body weight log (/users/me/body-weight)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

# The schema is shared by the whole test session: each test uses its own
# dates and only looks at those.


def _entries_on(body: list[dict], *days: str) -> list[dict]:
    return [e for e in body if e["measured_on"] in days]


async def test_put_records_weight_and_get_lists_it(client) -> None:
    r = await client.put("/users/me/body-weight/2024-01-10", json={"weight_kg": 84.7})

    assert r.status_code == 200
    assert r.json() == {"measured_on": "2024-01-10", "weight_kg": 84.7}
    listed = (await client.get("/users/me/body-weight")).json()
    assert _entries_on(listed, "2024-01-10") == [{"measured_on": "2024-01-10", "weight_kg": 84.7}]


async def test_put_same_day_replaces_the_weight(client) -> None:
    await client.put("/users/me/body-weight/2024-02-10", json={"weight_kg": 84.7})

    r = await client.put("/users/me/body-weight/2024-02-10", json={"weight_kg": 84.1})

    assert r.status_code == 200
    listed = (await client.get("/users/me/body-weight")).json()
    assert _entries_on(listed, "2024-02-10") == [{"measured_on": "2024-02-10", "weight_kg": 84.1}]


async def test_get_lists_newest_first(client) -> None:
    for day, weight in [("2024-03-01", 85.0), ("2024-03-03", 84.5), ("2024-03-02", 84.8)]:
        assert (await client.put(f"/users/me/body-weight/{day}", json={"weight_kg": weight})).status_code == 200

    listed = (await client.get("/users/me/body-weight")).json()

    assert [e["measured_on"] for e in _entries_on(listed, "2024-03-01", "2024-03-02", "2024-03-03")] == [
        "2024-03-03",
        "2024-03-02",
        "2024-03-01",
    ]
    days = [e["measured_on"] for e in listed]
    assert days == sorted(days, reverse=True)


async def test_put_today_is_accepted(client) -> None:
    today = datetime.now(UTC).date().isoformat()

    r = await client.put(f"/users/me/body-weight/{today}", json={"weight_kg": 84.0})

    assert r.status_code == 200
    assert (await client.delete(f"/users/me/body-weight/{today}")).status_code == 204


async def test_put_future_date_returns_422_and_stores_nothing(client) -> None:
    future = (datetime.now(UTC).date() + timedelta(days=3)).isoformat()

    r = await client.put(f"/users/me/body-weight/{future}", json={"weight_kg": 84.0})

    assert r.status_code == 422
    assert _entries_on((await client.get("/users/me/body-weight")).json(), future) == []


async def test_put_invalid_weight_returns_422(client) -> None:
    for weight in (0, -3, 400.5):
        r = await client.put("/users/me/body-weight/2024-04-10", json={"weight_kg": weight})
        assert r.status_code == 422
    assert (await client.put("/users/me/body-weight/2024-04-10", json={})).status_code == 422
    assert _entries_on((await client.get("/users/me/body-weight")).json(), "2024-04-10") == []


async def test_put_invalid_date_returns_422(client) -> None:
    r = await client.put("/users/me/body-weight/not-a-date", json={"weight_kg": 80})

    assert r.status_code == 422


async def test_delete_removes_the_entry(client) -> None:
    await client.put("/users/me/body-weight/2024-05-10", json={"weight_kg": 83.0})

    r = await client.delete("/users/me/body-weight/2024-05-10")

    assert r.status_code == 204
    assert _entries_on((await client.get("/users/me/body-weight")).json(), "2024-05-10") == []


async def test_delete_missing_entry_returns_404(client) -> None:
    r = await client.delete("/users/me/body-weight/2024-06-10")

    assert r.status_code == 404


async def test_entries_are_private_to_each_user(client, client_user2) -> None:
    await client.put("/users/me/body-weight/2024-07-10", json={"weight_kg": 84.0})

    assert _entries_on((await client_user2.get("/users/me/body-weight")).json(), "2024-07-10") == []
    assert (await client_user2.delete("/users/me/body-weight/2024-07-10")).status_code == 404
    # The other user's own entry on the same day is independent.
    assert (await client_user2.put("/users/me/body-weight/2024-07-10", json={"weight_kg": 60.0})).status_code == 200
    mine = _entries_on((await client.get("/users/me/body-weight")).json(), "2024-07-10")
    assert mine == [{"measured_on": "2024-07-10", "weight_kg": 84.0}]


async def test_body_weight_requires_auth(auth_client) -> None:
    assert (await auth_client.get("/users/me/body-weight")).status_code == 401
    assert (await auth_client.put("/users/me/body-weight/2024-01-10", json={"weight_kg": 80})).status_code == 401
    assert (await auth_client.delete("/users/me/body-weight/2024-01-10")).status_code == 401
