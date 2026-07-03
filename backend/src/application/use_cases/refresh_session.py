"""RefreshSessionUseCase — application layer.

Implements refresh-token rotation with single-use semantics, a reuse grace
window for benign multi-tab races, and family revocation on suspected theft.
"""
from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from returns.result import Failure, Result, Success

from backend.src.application.dtos import TokenPairDTO
from backend.src.application.errors import ApplicationError, InvalidRefreshTokenError
from backend.src.application.services.token_issuer import TokenIssuer
from backend.src.domain.entities.refresh_token import RefreshToken
from backend.src.domain.repositories.refresh_token_repository import RefreshTokenRepository

logger = logging.getLogger(__name__)


class RefreshSessionUseCase:
    def __init__(
        self,
        repo: RefreshTokenRepository,
        hash_token: Callable[[str], str],
        token_issuer: TokenIssuer,
        reuse_grace_period: timedelta,
    ) -> None:
        self._repo = repo
        self._hash_token = hash_token
        self._token_issuer = token_issuer
        self._reuse_grace_period = reuse_grace_period

    async def execute(self, raw_refresh_token: str) -> Result[TokenPairDTO, ApplicationError]:
        now = datetime.now(UTC)
        token = await self._repo.get_by_hash(self._hash_token(raw_refresh_token))
        if token is None:
            return Failure(InvalidRefreshTokenError())

        # Expiry is checked BEFORE the revoked/grace branch: an expired token
        # must never mint a pair, even if it was rotated inside the window.
        if token.is_expired(now):
            return Failure(InvalidRefreshTokenError())

        if token.is_revoked:
            return await self._handle_revoked_token(token, now)

        # Rotation: the presented token is single-use. The atomic revoke makes
        # concurrent requests race — the loser routes through the reuse logic.
        new_token_id = str(uuid.uuid4())
        revoked = await self._repo.revoke(token.id, replaced_by_id=new_token_id)
        if not revoked:
            current = await self._repo.get_by_hash(token.token_hash)
            if current is None:
                return Failure(InvalidRefreshTokenError())
            return await self._handle_revoked_token(current, now)

        pair = await self._token_issuer.issue_pair(token.user_id, now, token_id=new_token_id)
        return Success(pair)

    async def _handle_revoked_token(
        self, token: RefreshToken, now: datetime
    ) -> Result[TokenPairDTO, ApplicationError]:
        if self._is_benign_concurrent_refresh(token, now) and token.replaced_by_id is not None:
            # Multi-tab race: another client already rotated this token within
            # the grace window. Grace applies ONLY while the descendant token
            # is still alive — a revoked/deleted descendant (logout, family
            # nuke) means the rotation chain was killed on purpose.
            descendant = await self._repo.get_by_id(token.replaced_by_id)
            if descendant is not None and not descendant.is_revoked:
                logger.info(
                    "Refresh grace redemption (user_id=%s, token_id=%s) — "
                    "token was rotated concurrently within the grace window",
                    token.user_id,
                    token.id,
                )
                pair = await self._token_issuer.issue_pair(token.user_id, now)
                return Success(pair)
        # Reuse of a revoked token outside the grace window (or revoked by
        # logout) — assume the token was stolen and revoke every token this
        # user has (forces a fresh login everywhere).
        await self._repo.revoke_all_for_user(token.user_id)
        logger.warning(
            "Refresh token reuse detected (user_id=%s, token_id=%s) — all tokens revoked",
            token.user_id,
            token.id,
        )
        return Failure(InvalidRefreshTokenError())

    def _is_benign_concurrent_refresh(self, token: RefreshToken, now: datetime) -> bool:
        # Only rotation-revoked tokens qualify: a logout revocation never gets
        # grace, and neither does a rotation older than the grace window.
        if not token.was_rotated or token.revoked_at is None:
            return False
        return now - token.revoked_at <= self._reuse_grace_period
