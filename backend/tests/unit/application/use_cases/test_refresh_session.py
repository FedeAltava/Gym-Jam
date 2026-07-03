"""Tests for RefreshSessionUseCase — rotation, reuse grace window, family revocation."""
import logging
import uuid
from datetime import UTC, datetime, timedelta

from returns.result import Failure, Success

from backend.src.application.dtos import TokenPairDTO
from backend.src.application.errors import InvalidRefreshTokenError
from backend.src.application.services.token_issuer import TokenIssuer
from backend.src.application.use_cases.refresh_session import RefreshSessionUseCase
from backend.src.domain.entities.refresh_token import RefreshToken
from backend.tests.unit.application.use_cases.in_memory_refresh_token_repository import (
    InMemoryRefreshTokenRepository,
)

USER_ID = "user-1"
GRACE = timedelta(seconds=60)
TTL = timedelta(days=7)


def _fake_hash(raw: str) -> str:
    return f"hash({raw})"


def _make_token(
    raw: str = "raw-token",
    user_id: str = USER_ID,
    revoked_at: datetime | None = None,
    replaced_by_id: str | None = None,
    expires_at: datetime | None = None,
) -> RefreshToken:
    now = datetime.now(UTC)
    return RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token_hash=_fake_hash(raw),
        expires_at=expires_at or (now + TTL),
        revoked_at=revoked_at,
        created_at=now - timedelta(hours=1),
        replaced_by_id=replaced_by_id,
    )


def _make_use_case(repo: InMemoryRefreshTokenRepository) -> RefreshSessionUseCase:
    issuer = TokenIssuer(
        repo,
        hash_token=_fake_hash,
        generate_token=lambda: f"generated-{uuid.uuid4()}",
        create_access_token=lambda user_id: f"access-for-{user_id}",
        refresh_token_ttl=TTL,
    )
    return RefreshSessionUseCase(
        repo,
        hash_token=_fake_hash,
        token_issuer=issuer,
        reuse_grace_period=GRACE,
    )


# 1. Happy path — rotation returns a new pair and revokes the old token
async def test_rotation_returns_new_pair_and_revokes_old_token() -> None:
    token = _make_token()
    repo = InMemoryRefreshTokenRepository([token])
    result = await _make_use_case(repo).execute("raw-token")

    assert isinstance(result, Success)
    pair = result.unwrap()
    assert isinstance(pair, TokenPairDTO)
    assert pair.access_token == f"access-for-{USER_ID}"
    assert pair.refresh_token != "raw-token"
    old = repo.peek(token.id)
    assert old is not None and old.is_revoked
    # Rotation revocation points at the replacing token.
    assert old.replaced_by_id is not None
    assert repo.peek(old.replaced_by_id) is not None


# 2. Unknown token → Failure
async def test_unknown_token_returns_failure() -> None:
    repo = InMemoryRefreshTokenRepository()
    result = await _make_use_case(repo).execute("nope")
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidRefreshTokenError)


# 3. Expired token → Failure, no family revocation
async def test_expired_token_returns_failure() -> None:
    other = _make_token(raw="other")
    expired = _make_token(expires_at=datetime.now(UTC) - timedelta(days=1))
    repo = InMemoryRefreshTokenRepository([expired, other])
    result = await _make_use_case(repo).execute("raw-token")
    assert isinstance(result, Failure)
    assert not repo.peek(other.id).is_revoked


# 3b. Expired token that was rotated WITHIN the grace window must NOT mint —
# expiry is checked before the revoked/grace branch.
async def test_expired_token_rotated_within_grace_window_is_rejected() -> None:
    descendant = _make_token(raw="descendant")
    expired_rotated = _make_token(
        revoked_at=datetime.now(UTC) - timedelta(seconds=5),
        replaced_by_id=descendant.id,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    repo = InMemoryRefreshTokenRepository([expired_rotated, descendant])
    result = await _make_use_case(repo).execute("raw-token")

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidRefreshTokenError)
    # Expiry rejection is not the theft path — the descendant survives.
    assert not repo.peek(descendant.id).is_revoked


# 4. Benign concurrent reuse — rotated within the grace window → fresh pair
async def test_reuse_of_rotated_token_within_grace_window_is_benign(caplog) -> None:
    descendant = _make_token(raw="descendant")
    rotated = _make_token(
        revoked_at=datetime.now(UTC) - timedelta(seconds=5),
        replaced_by_id=descendant.id,
    )
    repo = InMemoryRefreshTokenRepository([rotated, descendant])
    with caplog.at_level(logging.INFO):
        result = await _make_use_case(repo).execute("raw-token")

    assert isinstance(result, Success)
    # The family survives: the descendant token is still active.
    assert not repo.peek(descendant.id).is_revoked
    # Every grace redemption is logged with user and token identifiers.
    assert "grace redemption" in caplog.text
    assert USER_ID in caplog.text


# 4b. Grace requires a LIVE descendant — if the replacing token was itself
# revoked (logout, family nuke) the replay is treated as theft.
async def test_grace_denied_when_descendant_already_revoked() -> None:
    descendant = _make_token(raw="descendant", revoked_at=datetime.now(UTC))
    rotated = _make_token(
        revoked_at=datetime.now(UTC) - timedelta(seconds=5),
        replaced_by_id=descendant.id,
    )
    repo = InMemoryRefreshTokenRepository([rotated, descendant])
    result = await _make_use_case(repo).execute("raw-token")

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidRefreshTokenError)


# 4c. Replay after a family nuke (revoke_all_for_user) gets NO grace even
# though the rotation happened seconds ago — the nuke clears replaced_by_id.
async def test_replay_after_revoke_all_gets_no_grace() -> None:
    descendant = _make_token(raw="descendant")
    rotated = _make_token(
        revoked_at=datetime.now(UTC) - timedelta(seconds=5),
        replaced_by_id=descendant.id,
    )
    repo = InMemoryRefreshTokenRepository([rotated, descendant])
    await repo.revoke_all_for_user(USER_ID)
    result = await _make_use_case(repo).execute("raw-token")

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidRefreshTokenError)


# 5. Malicious reuse — rotated OUTSIDE the grace window → revoke everything
async def test_reuse_of_rotated_token_outside_grace_window_revokes_family() -> None:
    descendant = _make_token(raw="descendant")
    rotated = _make_token(
        revoked_at=datetime.now(UTC) - (GRACE + timedelta(seconds=10)),
        replaced_by_id=descendant.id,
    )
    repo = InMemoryRefreshTokenRepository([rotated, descendant])
    result = await _make_use_case(repo).execute("raw-token")

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidRefreshTokenError)
    assert repo.peek(descendant.id).is_revoked


# 6. Logout-revoked token gets NO grace even inside the window
async def test_reuse_of_logout_revoked_token_gets_no_grace() -> None:
    other = _make_token(raw="other")
    logged_out = _make_token(
        revoked_at=datetime.now(UTC) - timedelta(seconds=5),
        replaced_by_id=None,  # logout revocation — not a rotation
    )
    repo = InMemoryRefreshTokenRepository([logged_out, other])
    result = await _make_use_case(repo).execute("raw-token")

    assert isinstance(result, Failure)
    assert repo.peek(other.id).is_revoked


# 7. Lost concurrent-rotation race (revoke rowcount == 0) routes through grace
async def test_concurrent_rotation_race_is_treated_as_benign_reuse() -> None:
    token = _make_token()
    winner = _make_token(raw="winner")

    class RaceLosingRepo(InMemoryRefreshTokenRepository):
        async def revoke(self, token_id: str, replaced_by_id: str | None = None) -> bool:
            # Simulate another request winning the rotation between our
            # get_by_hash and revoke: the row is already revoked-by-rotation.
            stored = self.peek(token_id)
            if stored is not None and stored.revoked_at is None:
                stored.revoked_at = datetime.now(UTC)
                stored.replaced_by_id = winner.id
            return False

    repo = RaceLosingRepo([token, winner])
    result = await _make_use_case(repo).execute("raw-token")

    assert isinstance(result, Success)


# 8. Lost race where the winner rotated outside the window → family revoked
async def test_concurrent_race_with_stale_rotation_revokes_family() -> None:
    token = _make_token()

    class StaleRaceRepo(InMemoryRefreshTokenRepository):
        async def revoke(self, token_id: str, replaced_by_id: str | None = None) -> bool:
            stored = self.peek(token_id)
            if stored is not None and stored.revoked_at is None:
                stored.revoked_at = datetime.now(UTC) - (GRACE + timedelta(seconds=10))
                stored.replaced_by_id = "winner-token-id"
                return False
            return await super().revoke(token_id, replaced_by_id)

    repo = StaleRaceRepo([token])
    result = await _make_use_case(repo).execute("raw-token")

    assert isinstance(result, Failure)
    assert repo.peek(token.id).is_revoked
