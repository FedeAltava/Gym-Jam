"""SqlAlchemyBodyWeightRepository — async SQLAlchemy implementation of BodyWeightRepository."""
from __future__ import annotations

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.entities.body_weight_entry import BodyWeightEntry
from backend.src.domain.repositories.body_weight_repository import BodyWeightRepository
from backend.src.infrastructure.persistence.models import BodyWeightEntryModel


class SqlAlchemyBodyWeightRepository(BodyWeightRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, entry: BodyWeightEntry) -> None:
        # (user_id, measured_on) is the primary key, so merge() updates the
        # day's existing row or inserts a new one.
        await self._session.merge(
            BodyWeightEntryModel(
                user_id=entry.user_id,
                measured_on=entry.measured_on,
                weight_kg=entry.weight_kg,
            )
        )
        await self._session.flush()

    async def list_by_user(self, user_id: str) -> list[BodyWeightEntry]:
        result = await self._session.execute(
            select(BodyWeightEntryModel)
            .where(BodyWeightEntryModel.user_id == user_id)
            .order_by(BodyWeightEntryModel.measured_on.desc())
        )
        return [
            BodyWeightEntry(user_id=m.user_id, measured_on=m.measured_on, weight_kg=m.weight_kg)
            for m in result.scalars().all()
        ]

    async def delete_for_user(self, user_id: str, measured_on: date) -> bool:
        result = await self._session.execute(
            delete(BodyWeightEntryModel).where(
                BodyWeightEntryModel.user_id == user_id,
                BodyWeightEntryModel.measured_on == measured_on,
            )
        )
        await self._session.flush()
        return result.rowcount > 0
