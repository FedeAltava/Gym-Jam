"""ResetPasswordUseCase — consume a reset token and update the password."""
from __future__ import annotations
import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from returns.result import Failure, Result, Success

from backend.src.application.errors import ApplicationError, DomainViolationError
from backend.src.infrastructure.auth.password import hash_password
from backend.src.infrastructure.persistence.models import PasswordResetTokenModel, RefreshTokenModel
from backend.src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository

_INVALID_TOKEN_MSG = "Invalid or expired reset token"


class ResetPasswordUseCase:
    def __init__(self, user_repo: SqlAlchemyUserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, raw_token: str, new_password: str, session: AsyncSession) -> Result[None, ApplicationError]:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        result = await session.execute(
            select(PasswordResetTokenModel).where(PasswordResetTokenModel.token_hash == token_hash)
        )
        record = result.scalar_one_or_none()

        if record is None or record.used_at is not None or record.expires_at <= datetime.now(UTC):
            return Failure(DomainViolationError(
                domain_error=ValueError(_INVALID_TOKEN_MSG),
                message=_INVALID_TOKEN_MSG,
            ))

        user = await self._user_repo.find_by_id(record.user_id, session)
        if user is None:
            return Failure(DomainViolationError(
                domain_error=ValueError(_INVALID_TOKEN_MSG),
                message=_INVALID_TOKEN_MSG,
            ))

        user.hashed_password = hash_password(new_password)
        record.used_at = datetime.now(UTC)

        # Revoke all refresh tokens for the user.
        now = datetime.now(UTC)
        tokens_result = await session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.user_id == user.id,
                RefreshTokenModel.revoked_at.is_(None),
            )
        )
        for token in tokens_result.scalars().all():
            token.revoked_at = now

        return Success(None)
