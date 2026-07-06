from abc import ABC, abstractmethod

from backend.src.domain.entities.exercise import Exercise


class ExerciseRepository(ABC):
    @abstractmethod
    async def get_all(self, muscle_group: str | None = None) -> list[Exercise]: ...

    @abstractmethod
    async def get_by_id(self, exercise_id: str) -> Exercise | None: ...

    @abstractmethod
    async def exists(self, exercise_id: str) -> bool: ...
