"""HTTP tests for refresh token rotation, reuse detection, and logout."""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy

from backend.src.infrastructure.auth.refresh_tokens import hash_refresh_token
from backend.src.infrastructure.config import settings
from backend.src.infrastructure.persistence.models import RefreshTokenModel
from backend.src.infrastructure.rate_limiter import login_limiter, refresh_limiter, register_limiter

BASE = "/auth"

_DEFAULT_PASSWORD = "password123"


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Reset rate limiter state before each test to avoid cross-test interference."""
    login_limiter.reset()
    register_limiter.reset()
    refresh_limiter.reset()
    yield
    login_limiter.reset()
    register_limiter.reset()
    refresh_limiter.reset()


# Helpers
async def register_and_login(client, email, password=_DEFAULT_PASSWORD):
    register_r = await client.post(f"{BASE}/register", json={"email": email, "password": password})
    assert register_r.status_code == 201
    login_r = await client.post(f"{BASE}/login", json={"email": email, "password": password})
    assert login_r.status_code == 200
    return register_r.json()["id"], login_r.json()


async def refresh(client, refresh_token):
    return await client.post(f"{BASE}/refresh", json={"refresh_token": refresh_token})


# 1. Login persists a refresh token and returns both tokens
async def test_login_returns_token_pair(auth_client):
    _, tokens = await register_and_login(auth_client, "pair@example.com")
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"


# 2. Refresh — happy path returns a new working pair
async def test_refresh_returns_new_working_pair(auth_client):
    _, tokens = await register_and_login(auth_client, "rotate@example.com")
    r = await refresh(auth_client, tokens["refresh_token"])
    assert r.status_code == 200
    new_tokens = r.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    # New access token works
    me = await auth_client.get(
        f"{BASE}/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "rotate@example.com"
    # New refresh token works too
    r2 = await refresh(auth_client, new_tokens["refresh_token"])
    assert r2.status_code == 200


# 3. Refresh — unknown token returns 401
async def test_refresh_unknown_token_returns_401(auth_client):
    r = await refresh(auth_client, "definitely-not-a-token")
    assert r.status_code == 401


# 4. Refresh — expired token returns 401
async def test_refresh_expired_token_returns_401(auth_client, session):
    user_id, _ = await register_and_login(auth_client, "expired@example.com")
    raw = "expired-raw-refresh-token"
    session.add(
        RefreshTokenModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token_hash=hash_refresh_token(raw),
            expires_at=datetime.now(UTC) - timedelta(days=1),
            revoked_at=None,
        )
    )
    await session.commit()
    r = await refresh(auth_client, raw)
    assert r.status_code == 401


# 5a. Reuse right after rotation (multi-tab race) is benign within the grace
# window — a fresh pair is issued and the family is NOT revoked.
async def test_refresh_reuse_within_grace_window_is_benign(auth_client):
    _, tokens = await register_and_login(auth_client, "reuse@example.com")
    old_refresh = tokens["refresh_token"]
    r = await refresh(auth_client, old_refresh)
    assert r.status_code == 200
    new_refresh = r.json()["refresh_token"]
    # Concurrent-tab reuse of the just-rotated token gets a fresh pair...
    reuse = await refresh(auth_client, old_refresh)
    assert reuse.status_code == 200
    assert reuse.json()["refresh_token"] not in (old_refresh, new_refresh)
    # ...and the descendant token from the first rotation still works.
    r2 = await refresh(auth_client, new_refresh)
    assert r2.status_code == 200


# 5b. Reuse OUTSIDE the grace window — 401 and ALL user tokens revoked
async def test_refresh_reuse_outside_grace_window_revokes_all(auth_client, session):
    _, tokens = await register_and_login(auth_client, "reuse-stale@example.com")
    old_refresh = tokens["refresh_token"]
    r = await refresh(auth_client, old_refresh)
    assert r.status_code == 200
    new_refresh = r.json()["refresh_token"]
    # Age the rotation beyond the grace window.
    stale = datetime.now(UTC) - timedelta(seconds=settings.refresh_token_reuse_grace_seconds + 30)
    await session.execute(
        sqlalchemy.update(RefreshTokenModel)
        .where(RefreshTokenModel.token_hash == hash_refresh_token(old_refresh))
        .values(revoked_at=stale)
    )
    await session.commit()
    # Reusing the rotated (revoked) token is rejected...
    reuse = await refresh(auth_client, old_refresh)
    assert reuse.status_code == 401
    # ...and the stolen-token heuristic revoked the NEW token as well.
    r2 = await refresh(auth_client, new_refresh)
    assert r2.status_code == 401


# 5c. A token revoked by LOGOUT gets no grace — immediate reuse revokes all
async def test_refresh_of_logout_revoked_token_gets_no_grace(auth_client):
    _, first = await register_and_login(auth_client, "nograce@example.com")
    second_login = await auth_client.post(
        f"{BASE}/login", json={"email": "nograce@example.com", "password": _DEFAULT_PASSWORD}
    )
    second = second_login.json()
    # Revoke the first token via logout (single-token revocation).
    r = await auth_client.post(
        f"{BASE}/logout",
        json={"refresh_token": first["refresh_token"]},
        headers={"Authorization": f"Bearer {first['access_token']}"},
    )
    assert r.status_code == 204
    # Immediate reuse is NOT benign (no rotation happened) — theft heuristic
    # fires and the second session's token is revoked too.
    reuse = await refresh(auth_client, first["refresh_token"])
    assert reuse.status_code == 401
    assert (await refresh(auth_client, second["refresh_token"])).status_code == 401


# 5d. Login purges the user's expired refresh tokens
async def test_login_purges_expired_tokens(auth_client, session):
    user_id, _ = await register_and_login(auth_client, "purge@example.com")
    expired_id = str(uuid.uuid4())
    session.add(
        RefreshTokenModel(
            id=expired_id,
            user_id=user_id,
            token_hash=hash_refresh_token("purge-me-raw-token"),
            expires_at=datetime.now(UTC) - timedelta(days=1),
            revoked_at=None,
        )
    )
    await session.commit()
    login_r = await auth_client.post(
        f"{BASE}/login", json={"email": "purge@example.com", "password": _DEFAULT_PASSWORD}
    )
    assert login_r.status_code == 200
    remaining = await session.execute(
        sqlalchemy.select(RefreshTokenModel).where(RefreshTokenModel.id == expired_id)
    )
    assert remaining.scalar_one_or_none() is None


# 6. Logout with a refresh token revokes exactly that token
async def test_logout_with_refresh_token_revokes_it(auth_client):
    _, tokens = await register_and_login(auth_client, "logout1@example.com")
    r = await auth_client.post(
        f"{BASE}/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 204
    r = await refresh(auth_client, tokens["refresh_token"])
    assert r.status_code == 401


# 7. Logout without a body revokes all the user's tokens
async def test_logout_without_body_revokes_all_tokens(auth_client):
    _, first = await register_and_login(auth_client, "logout2@example.com")
    second_login = await auth_client.post(
        f"{BASE}/login", json={"email": "logout2@example.com", "password": _DEFAULT_PASSWORD}
    )
    second = second_login.json()
    r = await auth_client.post(
        f"{BASE}/logout",
        headers={"Authorization": f"Bearer {first['access_token']}"},
    )
    assert r.status_code == 204
    assert (await refresh(auth_client, first["refresh_token"])).status_code == 401
    assert (await refresh(auth_client, second["refresh_token"])).status_code == 401


# 8. Logout without a refresh token (revoke-all) requires authentication
async def test_logout_without_token_returns_401(auth_client):
    r = await auth_client.post(f"{BASE}/logout")
    assert r.status_code == 401


# 8b. Revoke-all with an INVALID bearer is rejected and revokes nothing
async def test_logout_revoke_all_requires_valid_bearer(auth_client):
    _, tokens = await register_and_login(auth_client, "revokeall-bearer@example.com")
    r = await auth_client.post(
        f"{BASE}/logout",
        json={"refresh_token": None},
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert r.status_code == 401
    assert (await refresh(auth_client, tokens["refresh_token"])).status_code == 200


# 9. Logout revokes the PRESENTED refresh token by possession — the token is
# the credential, regardless of the bearer identity accompanying the request.
async def test_logout_revokes_presented_token_by_possession(auth_client):
    _, victim = await register_and_login(auth_client, "victim@example.com")
    _, other = await register_and_login(auth_client, "attacker@example.com")
    r = await auth_client.post(
        f"{BASE}/logout",
        json={"refresh_token": victim["refresh_token"]},
        headers={"Authorization": f"Bearer {other['access_token']}"},
    )
    assert r.status_code == 204
    # Whoever holds the raw token could refresh with it anyway — revoking it
    # is the safe action, so the presented token is dead now.
    assert (await refresh(auth_client, victim["refresh_token"])).status_code == 401


# 9b. Single-token logout works with NO bearer at all — possession of the
# refresh token authenticates it (logout after access-token expiry).
async def test_logout_with_refresh_token_needs_no_bearer(auth_client):
    _, tokens = await register_and_login(auth_client, "nobearer@example.com")
    r = await auth_client.post(
        f"{BASE}/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert r.status_code == 204
    assert (await refresh(auth_client, tokens["refresh_token"])).status_code == 401


# 9c. Single-token logout also works with an invalid/expired bearer attached
async def test_logout_with_invalid_bearer_and_refresh_token_still_revokes(auth_client):
    _, tokens = await register_and_login(auth_client, "stalebearer@example.com")
    r = await auth_client.post(
        f"{BASE}/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert r.status_code == 204
    assert (await refresh(auth_client, tokens["refresh_token"])).status_code == 401


# 9d. Logout with an already-rotated token revokes its live descendant
async def test_logout_with_rotated_token_revokes_descendant(auth_client):
    _, tokens = await register_and_login(auth_client, "rotatedlogout@example.com")
    old_refresh = tokens["refresh_token"]
    r = await refresh(auth_client, old_refresh)
    assert r.status_code == 200
    new_refresh = r.json()["refresh_token"]
    # Logout presenting the OLD (rotation-revoked) token...
    r = await auth_client.post(f"{BASE}/logout", json={"refresh_token": old_refresh})
    assert r.status_code == 204
    # ...kills the session: the live descendant is revoked too.
    assert (await refresh(auth_client, new_refresh)).status_code == 401


# 9e. Replay of a just-rotated token AFTER a revoke-all gets NO grace even
# inside the grace window — the family nuke closes rotation grace.
async def test_refresh_after_revoke_all_gets_no_grace(auth_client):
    _, tokens = await register_and_login(auth_client, "nukegrace@example.com")
    old_refresh = tokens["refresh_token"]
    r = await refresh(auth_client, old_refresh)
    assert r.status_code == 200
    new_access = r.json()["access_token"]
    # Nuke the whole family via revoke-all (valid bearer, no body token).
    r = await auth_client.post(
        f"{BASE}/logout", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert r.status_code == 204
    # The rotated token was replaced seconds ago, but no grace applies.
    assert (await refresh(auth_client, old_refresh)).status_code == 401


# 10. Refresh rate limit — 30 attempts per 60s trigger 429
async def test_refresh_rate_limit_returns_429(auth_client):
    for _ in range(30):
        await refresh(auth_client, "bad-token")
    r = await refresh(auth_client, "bad-token")
    assert r.status_code == 429
