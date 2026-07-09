"""RegisterUserUseCase — create a new user account."""
from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from returns.result import Failure, Result, Success

from backend.src.application.commands import RegisterUserCommand
from backend.src.application.errors import ApplicationError, DomainViolationError
from backend.src.domain.repositories.user_repository import UserRepository


class RegisterUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        create_user: Callable[[str, str, str], Any],
        hash_password: Callable[[str], str],
    ) -> None:
        self._user_repo = user_repo
        self._create_user = create_user
        self._hash_password = hash_password

    async def execute(self, cmd: RegisterUserCommand) -> Result[Any, ApplicationError]:
        existing = await self._user_repo.find_by_email(cmd.email)
        if existing is not None:
            return Failure(DomainViolationError(
                domain_error=ValueError("Email already registered"),
                message="Email already registered",
            ))
        user = self._create_user(
            str(uuid.uuid4()),
            cmd.email,
            self._hash_password(cmd.password),
        )
        await self._user_repo.save(user)
        return Success(user)
