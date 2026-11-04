"""BodyWeightRepository port — abstract base class for persistence."""
from abc import ABC, abstractmethod
from datetime import date

from backend.src.domain.entities.body_weight_entry import BodyWeightEntry


class BodyWeightRepository(ABC):
    @abstractmethod
    async def save(self, entry: BodyWeightEntry) -> None:
        """Insert the entry, or replace the weight of the user's entry for that day."""
        ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[BodyWeightEntry]:
        """The user's entries, newest day first."""
        ...

    @abstractmethod
    async def delete_for_user(self, user_id: str, measured_on: date) -> bool:
        """Delete the user's entry for that day. Returns False when there was none."""
        ...
