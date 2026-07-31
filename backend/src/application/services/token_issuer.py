"""TokenIssuer — application-layer service.

Single home for the token-pair issuance policy (refresh TTL, hashing, id
generation). Consumed by the login flow and by refresh rotation so the
policy lives in exactly one place.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from backend.src.application.dtos import TokenPairDTO
from backend.src.domain.entities.refresh_token import RefreshToken
from backend.src.domain.repositories.refresh_token_repository import RefreshTokenRepository


class TokenIssuer:
    def __init__(
        self,
        repo: RefreshTokenRepository,
        hash_token: Callable[[str], str],
        generate_token: Callable[[], str],
        create_access_token: Callable[..., str],
        refresh_token_ttl: timedelta,
    ) -> None:
        self._repo = repo
        self._hash_token = hash_token
        self._generate_token = generate_token
        self._create_access_token = create_access_token
        self._refresh_token_ttl = refresh_token_ttl

    async def issue_pair(
        self,
        user_id: str,
        now: datetime | None = None,
        token_id: str | None = None,
        password_changed_at: datetime | None = None,
    ) -> TokenPairDTO:
        """Create an access token and a persisted (hashed) refresh token."""
        now = now or datetime.now(UTC)
        raw_refresh = self._generate_token()
        await self._repo.add(
            RefreshToken(
                id=token_id or str(uuid.uuid4()),
                user_id=user_id,
                token_hash=self._hash_token(raw_refresh),
                expires_at=now + self._refresh_token_ttl,
                revoked_at=None,
                created_at=now,
            )
        )
        return TokenPairDTO(
            access_token=self._create_access_token(
                user_id, password_changed_at=password_changed_at
            ),
            refresh_token=raw_refresh,
        )

    async def issue_for_login(
        self,
        user_id: str,
        password_changed_at: datetime | None = None,
    ) -> TokenPairDTO:
        # Opportunistic cleanup: drop this user's expired tokens so the table
        # does not grow without bound.
        await self._repo.delete_expired(user_id)
        return await self.issue_pair(user_id, password_changed_at=password_changed_at)
