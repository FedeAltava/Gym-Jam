"""HTTP tests for PATCH /users/me/preferences (slice 2 — user preferences)."""
from __future__ import annotations


# ── 1. Update rest_seconds only (partial — units stays default) ──────────────

async def test_patch_preferences_updates_rest_seconds(client) -> None:
    r = await client.patch("/users/me/preferences", json={"rest_seconds": 120})

    assert r.status_code == 200
    data = r.json()
    assert data["rest_seconds"] == 120
    assert data["units"] == "kg"  # untouched by partial update
    assert data["id"] == "00000000-0000-0000-0000-000000000001"


# ── 2. Update units only (different user → rest_seconds still default) ───────

async def test_patch_preferences_updates_units(client_user2) -> None:
    r = await client_user2.patch("/users/me/preferences", json={"units": "lb"})

    assert r.status_code == 200
    data = r.json()
    assert data["units"] == "lb"
    assert data["rest_seconds"] == 90  # untouched by partial update


# ── 3. Validation: rest_seconds out of range → 422 ───────────────────────────

async def test_patch_preferences_validates_rest_seconds(client) -> None:
    r = await client.patch("/users/me/preferences", json={"rest_seconds": 999})

    assert r.status_code == 422


async def test_patch_preferences_rejects_negative_rest_seconds(client) -> None:
    r = await client.patch("/users/me/preferences", json={"rest_seconds": -1})

    assert r.status_code == 422


# ── 4. Validation: invalid units value → 422 ─────────────────────────────────

async def test_patch_preferences_validates_units(client) -> None:
    r = await client.patch("/users/me/preferences", json={"units": "oz"})

    assert r.status_code == 422


# ── 5. Unauthenticated → 401 ─────────────────────────────────────────────────

async def test_patch_preferences_requires_auth(auth_client) -> None:
    r = await auth_client.patch("/users/me/preferences", json={"rest_seconds": 120})

    assert r.status_code == 401


# ── 6. New users get preference defaults in UserResponse ─────────────────────

async def test_register_returns_preference_defaults(auth_client) -> None:
    r = await auth_client.post(
        "/auth/register",
        json={"email": "prefs-defaults@example.com", "password": "Password1"},
    )

    assert r.status_code == 201
    data = r.json()
    assert data["rest_seconds"] == 90
    assert data["units"] == "kg"
