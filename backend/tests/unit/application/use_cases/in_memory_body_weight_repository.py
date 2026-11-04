"""In-memory implementation of BodyWeightRepository for use case unit tests."""
from __future__ import annotations

from datetime import date

from backend.src.domain.entities.body_weight_entry import BodyWeightEntry
from backend.src.domain.repositories.body_weight_repository import BodyWeightRepository


class InMemoryBodyWeightRepository(BodyWeightRepository):
    def __init__(self) -> None:
        self._store: dict[tuple[str, date], BodyWeightEntry] = {}

    async def save(self, entry: BodyWeightEntry) -> None:
        self._store[(entry.user_id, entry.measured_on)] = entry

    async def list_by_user(self, user_id: str) -> list[BodyWeightEntry]:
        entries = [e for (uid, _), e in self._store.items() if uid == user_id]
        return sorted(entries, key=lambda e: e.measured_on, reverse=True)

    async def delete_for_user(self, user_id: str, measured_on: date) -> bool:
        return self._store.pop((user_id, measured_on), None) is not None
