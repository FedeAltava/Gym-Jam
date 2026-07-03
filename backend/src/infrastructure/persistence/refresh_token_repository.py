from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.entities.refresh_token import RefreshToken
from backend.src.domain.repositories.refresh_token_repository import RefreshTokenRepository
from backend.src.infrastructure.persistence.models import RefreshTokenModel


def _ensure_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes even for timezone-aware columns —
    # normalize to UTC here so domain entities stay timezone-aware and pure.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _to_domain(model: RefreshTokenModel) -> RefreshToken:
    return RefreshToken(
        id=model.id,
        user_id=model.user_id,
        token_hash=model.token_hash,
        expires_at=_ensure_utc(model.expires_at),
        revoked_at=_ensure_utc(model.revoked_at) if model.revoked_at is not None else None,
        created_at=_ensure_utc(model.created_at),
        replaced_by_id=model.replaced_by_id,
    )


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: RefreshToken) -> None:
        self._session.add(
            RefreshTokenModel(
                id=token.id,
                user_id=token.user_id,
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                revoked_at=token.revoked_at,
                created_at=token.created_at,
                replaced_by_id=token.replaced_by_id,
            )
        )
        await self._session.flush()

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        # populate_existing: always refresh from the row instead of returning a
        # possibly stale identity-map instance — the reuse/race fallback in the
        # refresh use case re-reads after a lost revoke race and MUST see the
        # committed DB state, not values fabricated by its own losing UPDATE.
        result = await self._session.execute(
            select(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .execution_options(populate_existing=True)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _to_domain(model)

    async def get_by_id(self, token_id: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshTokenModel)
            .where(RefreshTokenModel.id == token_id)
            .execution_options(populate_existing=True)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _to_domain(model)

    async def revoke(self, token_id: str, replaced_by_id: str | None = None) -> bool:
        # Atomic single-statement revoke: the `revoked_at IS NULL` guard makes
        # concurrent rotations race on the row — exactly one caller wins.
        # synchronize_session=False: the default ('evaluate') would write THIS
        # caller's values into the in-memory instance even when the UPDATE
        # matched 0 rows, fabricating a "rotated just now" state for the loser.
        result = await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == token_id, RefreshTokenModel.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC), replaced_by_id=replaced_by_id)
            .execution_options(synchronize_session=False)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def revoke_all_for_user(self, user_id: str) -> None:
        # Family nuke: revoke every active token AND clear replaced_by_id on
        # already-rotated rows so no row keeps an open rotation grace window.
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(
                revoked_at=func.coalesce(RefreshTokenModel.revoked_at, datetime.now(UTC)),
                replaced_by_id=None,
            )
            .execution_options(synchronize_session=False)
        )
        await self._session.flush()

    async def delete_expired(self, user_id: str) -> int:
        result = await self._session.execute(
            delete(RefreshTokenModel).where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.expires_at < datetime.now(UTC),
            )
        )
        await self._session.flush()
        return result.rowcount
