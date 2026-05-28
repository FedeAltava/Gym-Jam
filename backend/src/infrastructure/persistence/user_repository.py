from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.src.infrastructure.persistence.models import UserModel


class SqlAlchemyUserRepository:
    async def save(self, user: UserModel, session: AsyncSession) -> None:
        session.add(user)
        await session.flush()

    async def find_by_email(self, email: str, session: AsyncSession) -> UserModel | None:
        result = await session.execute(select(UserModel).where(UserModel.email == email))
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: str, session: AsyncSession) -> UserModel | None:
        result = await session.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalar_one_or_none()
