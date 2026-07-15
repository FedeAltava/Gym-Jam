from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PasswordResetTokenDTO:
    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    used_at: datetime | None


class PasswordResetTokenRepository(ABC):
    @abstractmethod
    async def create(self, id: str, user_id: str, token_hash: str, expires_at: datetime) -> None: ...

    @abstractmethod
    async def find_by_hash(self, token_hash: str) -> PasswordResetTokenDTO | None: ...

    @abstractmethod
    async def mark_used(self, token_id: str, used_at: datetime) -> bool: ...

    @abstractmethod
    async def invalidate_unused_for_user(self, user_id: str) -> None: ...
