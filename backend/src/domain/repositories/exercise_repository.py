from abc import ABC, abstractmethod

from backend.src.domain.entities.exercise import Exercise


class ExerciseRepository(ABC):
    @abstractmethod
    async def get_all(self, user_id: str | None = None) -> list[Exercise]: ...

    @abstractmethod
    async def get_by_id(self, exercise_id: str) -> Exercise | None: ...

    @abstractmethod
    async def exists(self, exercise_id: str) -> bool: ...

    @abstractmethod
    async def save(self, exercise: Exercise) -> None: ...

    @abstractmethod
    async def delete(self, exercise_id: str) -> None: ...

    @abstractmethod
    async def is_referenced_by_workout(self, exercise_id: str) -> bool: ...
