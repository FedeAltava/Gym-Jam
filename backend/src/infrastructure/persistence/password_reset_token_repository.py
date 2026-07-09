from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.repositories.password_reset_token_repository import (
    PasswordResetTokenDTO,
    PasswordResetTokenRepository,
)
from backend.src.infrastructure.persistence.models import PasswordResetTokenModel


class SqlAlchemyPasswordResetTokenRepository(PasswordResetTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, id: str, user_id: str, token_hash: str, expires_at: datetime) -> None:
        self._session.add(
            PasswordResetTokenModel(
                id=id,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        await self._session.flush()

    async def find_by_hash(self, token_hash: str) -> PasswordResetTokenDTO | None:
        result = await self._session.execute(
            select(PasswordResetTokenModel).where(PasswordResetTokenModel.token_hash == token_hash)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return PasswordResetTokenDTO(
            id=record.id,
            user_id=record.user_id,
            token_hash=record.token_hash,
            expires_at=record.expires_at,
            used_at=record.used_at,
        )

    async def mark_used(self, token_id: str, used_at: datetime) -> None:
        await self._session.execute(
            update(PasswordResetTokenModel)
            .where(PasswordResetTokenModel.id == token_id)
            .values(used_at=used_at)
            .execution_options(synchronize_session=False)
        )
        await self._session.flush()
