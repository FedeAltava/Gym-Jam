"""UpdateUserPreferencesUseCase — partial update of per-user settings."""
from __future__ import annotations

from typing import Any

from returns.result import Failure, Result, Success

from backend.src.application.commands import UpdateUserPreferencesCommand
from backend.src.application.errors import ApplicationError, DomainViolationError
from backend.src.domain.repositories.user_repository import UserRepository


class UpdateUserPreferencesUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, cmd: UpdateUserPreferencesCommand) -> Result[Any, ApplicationError]:
        user = await self._user_repo.find_by_id(cmd.user_id)
        if user is None:
            return Failure(DomainViolationError(
                domain_error=ValueError("User not found"),
                message="User not found",
            ))

        if cmd.rest_seconds is not None:
            user.rest_seconds = cmd.rest_seconds
        if cmd.units is not None:
            user.units = cmd.units

        await self._user_repo.save(user)
        return Success(user)
