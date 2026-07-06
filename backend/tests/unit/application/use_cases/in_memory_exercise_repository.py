from backend.src.domain.entities.exercise import Exercise
from backend.src.domain.repositories.exercise_repository import ExerciseRepository


class InMemoryExerciseRepository(ExerciseRepository):
    def __init__(self, exercises: list[Exercise] | None = None) -> None:
        self._store: dict[str, Exercise] = {e.id: e for e in (exercises or [])}
        self._workout_references: set[str] = set()

    async def get_all(self, user_id: str | None = None) -> list[Exercise]:
        if user_id is None:
            return [e for e in self._store.values() if e.owner_id is None]
        return [e for e in self._store.values() if e.owner_id is None or e.owner_id == user_id]

    async def get_by_id(self, exercise_id: str) -> Exercise | None:
        return self._store.get(exercise_id)

    async def exists(self, exercise_id: str) -> bool:
        return exercise_id in self._store

    async def save(self, exercise: Exercise) -> None:
        self._store[exercise.id] = exercise

    async def delete(self, exercise_id: str) -> None:
        self._store.pop(exercise_id, None)

    async def is_referenced_by_workout(self, exercise_id: str) -> bool:
        return exercise_id in self._workout_references

    def _mark_referenced(self, exercise_id: str) -> None:
        self._workout_references.add(exercise_id)
