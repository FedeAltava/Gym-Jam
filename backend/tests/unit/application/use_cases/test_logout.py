"""Tests for LogoutUseCase — single-token and all-token revocation."""
import uuid
from datetime import UTC, datetime, timedelta

from returns.result import Success

from backend.src.application.use_cases.logout import LogoutUseCase
from backend.src.domain.entities.refresh_token import RefreshToken
from backend.tests.unit.application.use_cases.in_memory_refresh_token_repository import (
    InMemoryRefreshTokenRepository,
)

USER_ID = "user-1"


def _fake_hash(raw: str) -> str:
    return f"hash({raw})"


def _make_token(
    raw: str,
    user_id: str = USER_ID,
    revoked_at: datetime | None = None,
    replaced_by_id: str | None = None,
) -> RefreshToken:
    now = datetime.now(UTC)
    return RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token_hash=_fake_hash(raw),
        expires_at=now + timedelta(days=7),
        revoked_at=revoked_at,
        created_at=now,
        replaced_by_id=replaced_by_id,
    )


# 1. Logout with a refresh token revokes exactly that token
async def test_logout_with_token_revokes_only_that_token() -> None:
    target = _make_token("target")
    other = _make_token("other")
    repo = InMemoryRefreshTokenRepository([target, other])

    result = await LogoutUseCase(repo, hash_token=_fake_hash).execute(USER_ID, "target")

    assert isinstance(result, Success)
    assert repo.peek(target.id).is_revoked
    assert not repo.peek(other.id).is_revoked
    # Logout revocation is NOT a rotation — no grace on later reuse.
    assert repo.peek(target.id).replaced_by_id is None


# 2. Logout without a token revokes all the user's tokens
async def test_logout_without_token_revokes_all_user_tokens() -> None:
    first = _make_token("first")
    second = _make_token("second")
    foreign = _make_token("foreign", user_id="user-2")
    repo = InMemoryRefreshTokenRepository([first, second, foreign])

    result = await LogoutUseCase(repo, hash_token=_fake_hash).execute(USER_ID, None)

    assert isinstance(result, Success)
    assert repo.peek(first.id).is_revoked
    assert repo.peek(second.id).is_revoked
    assert not repo.peek(foreign.id).is_revoked


# 3. Possession of the refresh token IS the credential — it is revoked even
# when the accompanying user identity does not match (revoking a token you
# hold is always safe: at worst it ends the session it belongs to).
async def test_logout_revokes_presented_token_regardless_of_user() -> None:
    victim = _make_token("victim", user_id="user-2")
    repo = InMemoryRefreshTokenRepository([victim])

    result = await LogoutUseCase(repo, hash_token=_fake_hash).execute(USER_ID, "victim")

    assert isinstance(result, Success)
    assert repo.peek(victim.id).is_revoked


# 4. Single-token logout needs NO user identity (possession authenticates)
async def test_logout_with_token_needs_no_user_identity() -> None:
    target = _make_token("target")
    repo = InMemoryRefreshTokenRepository([target])

    result = await LogoutUseCase(repo, hash_token=_fake_hash).execute(None, "target")

    assert isinstance(result, Success)
    assert repo.peek(target.id).is_revoked


# 5. Logout with an unknown token succeeds silently
async def test_logout_with_unknown_token_succeeds() -> None:
    repo = InMemoryRefreshTokenRepository()
    result = await LogoutUseCase(repo, hash_token=_fake_hash).execute(USER_ID, "unknown")
    assert isinstance(result, Success)


# 6. Logout with an already-rotated token revokes its live descendant —
# otherwise logout would revoke nothing and the session would survive.
async def test_logout_with_rotated_token_revokes_descendant() -> None:
    descendant = _make_token("descendant")
    rotated = _make_token(
        "rotated",
        revoked_at=datetime.now(UTC) - timedelta(seconds=5),
        replaced_by_id=descendant.id,
    )
    repo = InMemoryRefreshTokenRepository([rotated, descendant])

    result = await LogoutUseCase(repo, hash_token=_fake_hash).execute(USER_ID, "rotated")

    assert isinstance(result, Success)
    assert repo.peek(descendant.id).is_revoked
    # The descendant's revocation is a logout revocation — no grace later.
    assert repo.peek(descendant.id).replaced_by_id is None


# 7. No token AND no user identity → succeeds without revoking anything
# (the route rejects this combination with 401 before reaching the use case).
async def test_logout_without_token_and_identity_revokes_nothing() -> None:
    token = _make_token("survivor")
    repo = InMemoryRefreshTokenRepository([token])

    result = await LogoutUseCase(repo, hash_token=_fake_hash).execute(None, None)

    assert isinstance(result, Success)
    assert not repo.peek(token.id).is_revoked
