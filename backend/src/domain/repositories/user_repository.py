from abc import ABC, abstractmethod
from typing import Any


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: Any) -> None: ...

    @abstractmethod
    async def find_by_email(self, email: str) -> Any | None: ...

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Any | None: ...
