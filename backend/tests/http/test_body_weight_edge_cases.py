"""Edge cases for the body weight log (bounds, dates, isolation, auth).

Every test uses its own dates (2023-*) so it never collides with the
session-shared schema used by the other HTTP tests.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

BW = "/users/me/body-weight"


def _on(body: list[dict], *days: str) -> list[dict]:
    return [e for e in body if e["measured_on"] in days]


async def _snapshot(client) -> bytes:
    r = await client.get(BW)
    assert r.status_code == 200
    return r.content


async def test_record_then_replace_same_day(client) -> None:
    r = await client.put(f"{BW}/2023-01-10", json={"weight_kg": 84.7})
    assert r.status_code == 200
    assert r.json() == {"measured_on": "2023-01-10", "weight_kg": 84.7}

    r = await client.put(f"{BW}/2023-01-10", json={"weight_kg": 83.9})
    assert r.status_code == 200
    assert r.json() == {"measured_on": "2023-01-10", "weight_kg": 83.9}
    assert _on((await client.get(BW)).json(), "2023-01-10") == [{"measured_on": "2023-01-10", "weight_kg": 83.9}]


async def test_list_is_newest_first(client) -> None:
    for day, kg in [("2023-02-05", 85.0), ("2023-02-20", 84.2), ("2023-02-12", 84.6)]:
        assert (await client.put(f"{BW}/{day}", json={"weight_kg": kg})).status_code == 200
    listed = (await client.get(BW)).json()
    assert [e["measured_on"] for e in _on(listed, "2023-02-05", "2023-02-12", "2023-02-20")] == [
        "2023-02-20",
        "2023-02-12",
        "2023-02-05",
    ]
    days = [e["measured_on"] for e in listed]
    assert days == sorted(days, reverse=True)


async def test_today_and_tomorrow_accepted_later_days_rejected(client) -> None:
    today = datetime.now(UTC).date()
    tomorrow = (today + timedelta(days=1)).isoformat()
    # Three days ahead stays rejected even if UTC midnight passes mid-test;
    # the exact +1/+2 boundary is pinned by the fixed-clock unit test.
    later = (today + timedelta(days=3)).isoformat()

    assert (await client.put(f"{BW}/{today.isoformat()}", json={"weight_kg": 84.0})).status_code == 200
    # UTC+1 slack: a client ahead of UTC may already be on the next day.
    assert (await client.put(f"{BW}/{tomorrow}", json={"weight_kg": 84.0})).status_code == 200

    before = await _snapshot(client)
    r = await client.put(f"{BW}/{later}", json={"weight_kg": 84.0})
    assert r.status_code == 422
    assert "future" in r.text.lower()
    assert await _snapshot(client) == before

    # cleanup so other probes see a stable list
    assert (await client.delete(f"{BW}/{today.isoformat()}")).status_code == 204
    assert (await client.delete(f"{BW}/{tomorrow}")).status_code == 204


async def test_weight_bounds(client) -> None:
    assert (await client.put(f"{BW}/2023-03-01", json={"weight_kg": 400})).status_code == 200
    assert (await client.put(f"{BW}/2023-03-02", json={"weight_kg": 0.1})).status_code == 200

    before = await _snapshot(client)
    for payload in (
        {"weight_kg": 0},
        {"weight_kg": -5},
        {"weight_kg": 400.01},
        {"weight_kg": "heavy"},
        {"weight_kg": None},
        {},
    ):
        r = await client.put(f"{BW}/2023-03-03", json=payload)
        assert r.status_code == 422, (payload, r.text)
        assert await _snapshot(client) == before, payload
    assert _on((await client.get(BW)).json(), "2023-03-03") == []


async def test_invalid_date_formats_rejected(client) -> None:
    before = await _snapshot(client)
    for bad in ("2024-13-01", "2024-02-30", "abc", "20240101", "2024-1-1"):
        r = await client.put(f"{BW}/{bad}", json={"weight_kg": 80})
        assert r.status_code == 422, (bad, r.text)
        assert await _snapshot(client) == before, bad
        r = await client.delete(f"{BW}/{bad}")
        assert r.status_code == 422, (bad, r.text)
        assert await _snapshot(client) == before, bad


async def test_delete_existing_missing_and_foreign(client, client_user2) -> None:
    assert (await client.put(f"{BW}/2023-04-10", json={"weight_kg": 83.0})).status_code == 200
    assert (await client.delete(f"{BW}/2023-04-10")).status_code == 204
    assert _on((await client.get(BW)).json(), "2023-04-10") == []

    before = await _snapshot(client)
    r = await client.delete(f"{BW}/2023-04-11")
    assert r.status_code == 404
    assert await _snapshot(client) == before

    # another user's row: 404 for me, row intact for them
    assert (await client_user2.put(f"{BW}/2023-04-12", json={"weight_kg": 61.0})).status_code == 200
    theirs = await _snapshot(client_user2)
    r = await client.delete(f"{BW}/2023-04-12")
    assert r.status_code == 404
    assert await _snapshot(client_user2) == theirs
    assert _on((await client_user2.get(BW)).json(), "2023-04-12") == [{"measured_on": "2023-04-12", "weight_kg": 61.0}]


async def test_get_is_isolated_per_user(client, client_user2) -> None:
    assert (await client.put(f"{BW}/2023-05-10", json={"weight_kg": 84.0})).status_code == 200
    assert (await client_user2.put(f"{BW}/2023-05-10", json={"weight_kg": 60.0})).status_code == 200
    assert _on((await client.get(BW)).json(), "2023-05-10") == [{"measured_on": "2023-05-10", "weight_kg": 84.0}]
    assert _on((await client_user2.get(BW)).json(), "2023-05-10") == [{"measured_on": "2023-05-10", "weight_kg": 60.0}]


async def test_auth_required_on_all_three(auth_client) -> None:
    assert (await auth_client.get(BW)).status_code == 401
    assert (await auth_client.put(f"{BW}/2023-06-10", json={"weight_kg": 80})).status_code == 401
    assert (await auth_client.delete(f"{BW}/2023-06-10")).status_code == 401
    bad = {"Authorization": "Bearer not-a-token"}
    assert (await auth_client.get(BW, headers=bad)).status_code == 401
    assert (await auth_client.put(f"{BW}/2023-06-10", json={"weight_kg": 80}, headers=bad)).status_code == 401
    assert (await auth_client.delete(f"{BW}/2023-06-10", headers=bad)).status_code == 401
