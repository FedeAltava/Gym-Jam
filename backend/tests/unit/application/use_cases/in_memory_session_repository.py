"""In-memory implementation of SessionRepository for use case unit tests."""
from __future__ import annotations

from datetime import date

from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.read_models import SessionSnapshot
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.value_objects import TrainingDayId, WorkoutId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._store: dict[str, WorkoutSession] = {}
        self._history_items: list[SessionSnapshot] = []
        # Last kwargs received by list_history_for_user — lets use case tests
        # assert filter forwarding without a real query engine.
        self.last_history_call: dict[str, object] | None = None

    async def save(self, session: WorkoutSession) -> None:
        self._store[str(session.id.value)] = session

    async def get_by_id(self, id: WorkoutSessionId) -> WorkoutSession | None:
        return self._store.get(str(id.value))

    async def get_in_progress_for_day(
        self,
        user_id: str,
        training_day_id: TrainingDayId,
    ) -> WorkoutSession | None:
        for s in self._store.values():
            if (
                s.user_id == user_id
                and s.training_day_id == training_day_id
                and s.completed_at is None
            ):
                return s
        return None

    async def delete(self, session_id: WorkoutSessionId) -> None:
        self._store.pop(str(session_id.value), None)

    async def get_sessions_for_day(
        self,
        user_id: str,
        workout_id: WorkoutId,
        training_day_id: TrainingDayId,
    ) -> list[WorkoutSession]:
        results = [
            s
            for s in self._store.values()
            if (
                s.user_id == user_id
                and s.workout_id == workout_id
                and s.training_day_id == training_day_id
            )
        ]
        # Return newest first (consistent with SQL repo)
        return sorted(results, key=lambda s: s.started_at, reverse=True)

    async def get_history_item_for_user(
        self,
        user_id: str,
        session_id: str,
    ) -> SessionSnapshot | None:
        for item in self._history_items:
            if item.id == session_id:
                return item
        return None

    def seed_history(self, items: list[SessionSnapshot]) -> None:
        """Seed pre-built history read models (already ordered newest-first)."""
        self._history_items = list(items)

    async def list_history_for_user(
        self,
        user_id: str,
        workout_id: str | None,
        day_id: str | None,
        status: str | None,
        date_from: date | None,
        date_to: date | None,
        limit: int,
        offset: int,
        session_id: str | None = None,
    ) -> list[SessionSnapshot]:
        self.last_history_call = {
            "user_id": user_id,
            "workout_id": workout_id,
            "day_id": day_id,
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
            "offset": offset,
        }
        return self._history_items[offset : offset + limit]

    async def count_history_for_user(
        self,
        user_id: str,
        workout_id: str | None,
        day_id: str | None,
        status: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> int:
        return len(self._history_items)
