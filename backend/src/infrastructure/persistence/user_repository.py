from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.repositories.user_repository import UserRepository
from backend.src.infrastructure.persistence.models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: UserModel) -> None:
        self._session.add(user)
        await self._session.flush()

    async def find_by_email(self, email: str) -> UserModel | None:
        result = await self._session.execute(
            select(UserModel).where(func.lower(UserModel.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: str) -> UserModel | None:
        result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalar_one_or_none()
