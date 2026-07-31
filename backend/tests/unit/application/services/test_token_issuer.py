"""Tests for TokenIssuer — the single home of token-pair issuance policy."""
import uuid
from datetime import UTC, datetime, timedelta

from backend.src.application.dtos import TokenPairDTO
from backend.src.application.services.token_issuer import TokenIssuer
from backend.src.domain.entities.refresh_token import RefreshToken
from backend.tests.unit.application.use_cases.in_memory_refresh_token_repository import (
    InMemoryRefreshTokenRepository,
)

USER_ID = "user-1"
TTL = timedelta(days=7)


def _fake_hash(raw: str) -> str:
    return f"hash({raw})"


def _make_issuer(repo: InMemoryRefreshTokenRepository) -> TokenIssuer:
    return TokenIssuer(
        repo,
        hash_token=_fake_hash,
        generate_token=lambda: f"generated-{uuid.uuid4()}",
        create_access_token=lambda user_id, **_kwargs: f"access-for-{user_id}",
        refresh_token_ttl=TTL,
    )


# 1. issue_pair persists a hashed refresh token with the configured TTL
async def test_issue_pair_persists_hashed_token_with_ttl() -> None:
    repo = InMemoryRefreshTokenRepository()
    now = datetime.now(UTC)

    pair = await _make_issuer(repo).issue_pair(USER_ID, now)

    assert isinstance(pair, TokenPairDTO)
    assert pair.access_token == f"access-for-{USER_ID}"
    stored = repo.all_tokens()
    assert len(stored) == 1
    token = stored[0]
    assert token.user_id == USER_ID
    # Only the hash is persisted — never the raw token.
    assert token.token_hash == _fake_hash(pair.refresh_token)
    assert token.expires_at == now + TTL
    assert token.revoked_at is None
    assert token.replaced_by_id is None


# 2. issue_pair honors an explicit token id (used by rotation)
async def test_issue_pair_honors_explicit_token_id() -> None:
    repo = InMemoryRefreshTokenRepository()
    await _make_issuer(repo).issue_pair(USER_ID, token_id="explicit-id")
    assert repo.peek("explicit-id") is not None


# 3. issue_for_login purges the user's expired tokens before issuing
async def test_issue_for_login_purges_expired_tokens() -> None:
    now = datetime.now(UTC)
    expired = RefreshToken(
        id="expired-token",
        user_id=USER_ID,
        token_hash=_fake_hash("stale"),
        expires_at=now - timedelta(days=1),
        revoked_at=None,
        created_at=now - timedelta(days=8),
    )
    foreign = RefreshToken(
        id="foreign-expired",
        user_id="user-2",
        token_hash=_fake_hash("foreign"),
        expires_at=now - timedelta(days=1),
        revoked_at=None,
        created_at=now - timedelta(days=8),
    )
    repo = InMemoryRefreshTokenRepository([expired, foreign])

    pair = await _make_issuer(repo).issue_for_login(USER_ID)

    assert pair.refresh_token
    assert repo.peek("expired-token") is None
    # Only THIS user's expired tokens are purged.
    assert repo.peek("foreign-expired") is not None
    assert len(repo.all_tokens()) == 2  # foreign expired + the new token
