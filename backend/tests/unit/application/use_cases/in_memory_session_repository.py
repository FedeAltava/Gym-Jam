"""In-memory implementation of SessionRepository for use case unit tests."""
from __future__ import annotations

from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.value_objects import TrainingDayId, WorkoutId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._store: dict[str, WorkoutSession] = {}

    async def save(self, session: WorkoutSession) -> None:
        self._store[str(session.id.value)] = session

    async def get_by_id(self, id: WorkoutSessionId) -> WorkoutSession | None:
        return self._store.get(str(id.value))

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
