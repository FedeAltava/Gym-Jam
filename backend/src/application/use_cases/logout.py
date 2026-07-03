"""LogoutUseCase — application layer.

Revokes a single refresh token (possession of the raw token IS the
credential) or every token the user has when no token is provided (which
requires an authenticated user identity). Logout revocations never set
replaced_by_id, so a later reuse of the token gets no rotation grace.
"""
from __future__ import annotations

from collections.abc import Callable

from returns.result import Result, Success

from backend.src.application.errors import ApplicationError
from backend.src.domain.repositories.refresh_token_repository import RefreshTokenRepository

# A rotation-revoked token may point at a live descendant; follow the chain a
# bounded number of hops so logout kills the session even after rotations.
_MAX_ROTATION_HOPS = 5


class LogoutUseCase:
    def __init__(self, repo: RefreshTokenRepository, hash_token: Callable[[str], str]) -> None:
        self._repo = repo
        self._hash_token = hash_token

    async def execute(
        self, user_id: str | None, raw_refresh_token: str | None
    ) -> Result[None, ApplicationError]:
        if raw_refresh_token is not None:
            # Possession of the raw refresh token is the credential — no user
            # identity is needed (revoking a token you hold is always safe).
            # Unknown tokens are ignored silently: logout is best-effort and
            # must not leak whether a token exists.
            token = await self._repo.get_by_hash(self._hash_token(raw_refresh_token))
            for _ in range(_MAX_ROTATION_HOPS):
                if token is None:
                    break
                revoked = await self._repo.revoke(token.id)
                if revoked or token.replaced_by_id is None:
                    break
                # Already rotation-revoked: the live descendant carries the
                # session — revoke it instead.
                token = await self._repo.get_by_id(token.replaced_by_id)
        elif user_id is not None:
            await self._repo.revoke_all_for_user(user_id)
        return Success(None)
