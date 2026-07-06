"""SessionRepository ABC — port for workout session persistence."""
from abc import ABC, abstractmethod

from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects.training_day_id import TrainingDayId
from backend.src.domain.value_objects.workout_id import WorkoutId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


class SessionRepository(ABC):
    @abstractmethod
    async def save(self, session: WorkoutSession) -> None: ...

    @abstractmethod
    async def get_by_id(self, id: WorkoutSessionId) -> WorkoutSession | None: ...

    @abstractmethod
    async def delete(self, session_id: WorkoutSessionId) -> None: ...

    @abstractmethod
    async def get_sessions_for_day(
        self,
        user_id: str,
        workout_id: WorkoutId,
        training_day_id: TrainingDayId,
    ) -> list[WorkoutSession]: ...
