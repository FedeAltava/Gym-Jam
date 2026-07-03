"""ForgotPasswordUseCase — request a password reset email."""
from __future__ import annotations
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from returns.result import Result, Success

from backend.src.application.errors import ApplicationError
from backend.src.infrastructure.config import settings
from backend.src.infrastructure.email.email_service import send_reset_email
from backend.src.infrastructure.persistence.models import PasswordResetTokenModel
from backend.src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository


class ForgotPasswordUseCase:
    def __init__(self, user_repo: SqlAlchemyUserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, email: str, session: AsyncSession) -> Result[None, ApplicationError]:
        user = await self._user_repo.find_by_email(email, session)
        if user is None:
            # Always succeed — never reveal whether email exists.
            return Success(None)

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        record = PasswordResetTokenModel(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(record)

        reset_url = f"{settings.app_base_url}/reset-password?token={raw_token}"
        await send_reset_email(user.email, reset_url)

        return Success(None)
