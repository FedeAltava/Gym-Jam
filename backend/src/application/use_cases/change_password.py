"""ChangePasswordUseCase — update password for an authenticated user."""
from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from returns.result import Failure, Result, Success

from backend.src.application.errors import ApplicationError, DomainViolationError
from backend.src.domain.repositories.refresh_token_repository import RefreshTokenRepository
from backend.src.domain.repositories.user_repository import UserRepository


class ChangePasswordUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        hash_password: Callable[[str], str],
        verify_password: Callable[[str, str], bool],
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._hash_password = hash_password
        self._verify_password = verify_password

    async def execute(
        self, user_id: str, current_password: str, new_password: str
    ) -> Result[None, ApplicationError]:
        user = await self._user_repo.find_by_id(user_id)
        if user is None:
            return Failure(DomainViolationError(
                domain_error=ValueError("User not found"),
                message="User not found",
            ))

        if not self._verify_password(current_password, user.hashed_password):
            return Failure(DomainViolationError(
                domain_error=ValueError("Current password is incorrect"),
                message="Invalid credentials",
            ))

        user.hashed_password = self._hash_password(new_password)
        user.password_changed_at = datetime.now(UTC)
        await self._user_repo.save(user)
        await self._refresh_token_repo.revoke_all_for_user(user_id)

        return Success(None)
