"""ForgotPasswordUseCase — request a password reset email."""
from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from returns.result import Result, Success

from backend.src.application.errors import ApplicationError
from backend.src.domain.repositories.password_reset_token_repository import PasswordResetTokenRepository
from backend.src.domain.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class ForgotPasswordUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: PasswordResetTokenRepository,
        send_email: Callable[[str, str], Awaitable[None]],
        base_url: str,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._send_email = send_email
        self._base_url = base_url

    async def execute(self, email: str) -> Result[None, ApplicationError]:
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
        try:
            await self._send_email(user.email, reset_url)
        except Exception:
            logger.exception("Failed to send password reset email to %s", user.email)

        return Success(None)
