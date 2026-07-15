"""ResetPasswordUseCase — consume a reset token and update the password."""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime

from returns.result import Failure, Result, Success

from backend.src.application.errors import ApplicationError, DomainViolationError
from backend.src.domain.repositories.password_reset_token_repository import PasswordResetTokenRepository
from backend.src.domain.repositories.refresh_token_repository import RefreshTokenRepository
from backend.src.domain.repositories.user_repository import UserRepository

_INVALID_TOKEN_MSG = "Invalid or expired reset token"


class ResetPasswordUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: PasswordResetTokenRepository,
        refresh_token_repo: RefreshTokenRepository,
        hash_password: Callable[[str], str],
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._refresh_token_repo = refresh_token_repo
        self._hash_password = hash_password

    async def execute(self, raw_token: str, new_password: str) -> Result[None, ApplicationError]:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        record = await self._token_repo.find_by_hash(token_hash)

        if record is None or record.used_at is not None or record.expires_at <= datetime.now(UTC):
            return Failure(DomainViolationError(
                domain_error=ValueError(_INVALID_TOKEN_MSG),
                message=_INVALID_TOKEN_MSG,
            ))

        user = await self._user_repo.find_by_id(record.user_id)
        if user is None:
            return Failure(DomainViolationError(
                domain_error=ValueError(_INVALID_TOKEN_MSG),
                message=_INVALID_TOKEN_MSG,
            ))

        user.hashed_password = self._hash_password(new_password)
        marked = await self._token_repo.mark_used(record.id, datetime.now(UTC))
        if not marked:
            # A concurrent request already consumed this token — treat it as
            # invalid so the password change from this losing request is not
            # committed on the strength of an already-used token.
            return Failure(DomainViolationError(
                domain_error=ValueError(_INVALID_TOKEN_MSG),
                message=_INVALID_TOKEN_MSG,
            ))
        await self._refresh_token_repo.revoke_all_for_user(user.id)

        return Success(None)
