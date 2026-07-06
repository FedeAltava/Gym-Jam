"""ChangePasswordUseCase — update password for an authenticated user."""
from __future__ import annotations
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from returns.result import Failure, Result, Success

from backend.src.application.errors import ApplicationError, DomainViolationError
from backend.src.domain.repositories.user_repository import UserRepository
from backend.src.infrastructure.auth.password import hash_password, verify_password
from backend.src.infrastructure.persistence.models import RefreshTokenModel


class ChangePasswordUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(
        self, user_id: str, current_password: str, new_password: str, session: AsyncSession
    ) -> Result[None, ApplicationError]:
        user = await self._user_repo.find_by_id(user_id, session)
        if user is None:
            return Failure(DomainViolationError(
                domain_error=ValueError("User not found"),
                message="User not found",
            ))

        if not verify_password(current_password, user.hashed_password):
            return Failure(DomainViolationError(
                domain_error=ValueError("Current password is incorrect"),
                message="Invalid credentials",
            ))

        user.hashed_password = hash_password(new_password)

        # Revoke all refresh tokens to force re-login on other devices.
        now = datetime.now(UTC)
        tokens_result = await session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
        )
        for token in tokens_result.scalars().all():
            token.revoked_at = now

        return Success(None)
