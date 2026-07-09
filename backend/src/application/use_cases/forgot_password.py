"""ForgotPasswordUseCase — request a password reset email."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from returns.result import Result, Success

from backend.src.application.errors import ApplicationError
from backend.src.domain.repositories.password_reset_token_repository import PasswordResetTokenRepository
from backend.src.domain.repositories.user_repository import UserRepository


class ForgotPasswordUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: PasswordResetTokenRepository,
        base_url: str,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._base_url = base_url

    async def execute(self, email: str) -> Result[tuple[str, str] | None, ApplicationError]:
        user = await self._user_repo.find_by_email(email)
        if user is None:
            return Success(None)

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        await self._token_repo.create(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        reset_url = f"{self._base_url}/reset-password?token={raw_token}"
        return Success((user.email, reset_url))
