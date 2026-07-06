from backend.src.domain.entities.exercise import Exercise
from backend.src.domain.repositories.exercise_repository import ExerciseRepository


class InMemoryExerciseRepository(ExerciseRepository):
    def __init__(self, exercises: list[Exercise] | None = None) -> None:
        self._store: dict[str, Exercise] = {e.id: e for e in (exercises or [])}

    async def get_all(self) -> list[Exercise]:
        return list(self._store.values())

    async def get_by_id(self, exercise_id: str) -> Exercise | None:
        return self._store.get(exercise_id)

    async def exists(self, exercise_id: str) -> bool:
        return exercise_id in self._store
