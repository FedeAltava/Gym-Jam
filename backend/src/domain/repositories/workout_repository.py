from abc import ABC, abstractmethod

from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.value_objects import WorkoutId


class WorkoutRepository(ABC):
    @abstractmethod
    def save(self, workout: Workout) -> None: ...

    @abstractmethod
    def get_by_id(self, workout_id: WorkoutId) -> Workout | None: ...

    @abstractmethod
    def get_by_user(self, user_id: str) -> list[Workout]: ...
