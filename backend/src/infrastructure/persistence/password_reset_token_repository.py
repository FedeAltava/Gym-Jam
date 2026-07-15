from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.repositories.password_reset_token_repository import (
    PasswordResetTokenDTO,
    PasswordResetTokenRepository,
)
from backend.src.infrastructure.persistence.models import PasswordResetTokenModel


def _ensure_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes even for timezone-aware columns —
    # normalize to UTC here so comparisons against aware datetimes don't raise.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


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
            expires_at=_ensure_utc(record.expires_at),
            used_at=_ensure_utc(record.used_at) if record.used_at is not None else None,
        )

    async def mark_used(self, token_id: str, used_at: datetime) -> bool:
        # Atomic single-statement mark: the `used_at IS NULL` guard makes two
        # concurrent resets with the same token race on the row — exactly one
        # wins. synchronize_session=False so the loser's UPDATE (0 rows) never
        # fabricates a "used just now" state on an in-memory instance.
        result = await self._session.execute(
            update(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.id == token_id,
                PasswordResetTokenModel.used_at.is_(None),
            )
            .values(used_at=used_at)
            .execution_options(synchronize_session=False)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def invalidate_unused_for_user(self, user_id: str) -> None:
        # Invalidate every still-unused reset token for this user so a freshly
        # issued token is the only valid one (single active token invariant).
        await self._session.execute(
            update(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.user_id == user_id,
                PasswordResetTokenModel.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
            .execution_options(synchronize_session=False)
        )
        await self._session.flush()
