"""UserRepository — domain port for user persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: Any, session: AsyncSession) -> None: ...

    @abstractmethod
    async def find_by_email(self, email: str, session: AsyncSession) -> Any | None: ...

    @abstractmethod
    async def find_by_id(self, user_id: str, session: AsyncSession) -> Any | None: ...
