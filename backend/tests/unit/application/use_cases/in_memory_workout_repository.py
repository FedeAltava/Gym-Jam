from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutId


class InMemoryWorkoutRepository(WorkoutRepository):
    def __init__(self) -> None:
        self._store: dict[str, Workout] = {}

    async def save(self, workout: Workout) -> None:
        self._store[str(workout.id.value)] = workout

    async def get_by_id(self, workout_id: WorkoutId) -> Workout | None:
        return self._store.get(str(workout_id.value))

    async def get_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> list[Workout]:
        results = [w for w in self._store.values() if w.user_id == user_id]
        return results[offset : offset + limit]

    async def delete(self, workout_id: WorkoutId) -> bool:
        key = str(workout_id.value)
        if key not in self._store:
            return False
        del self._store[key]
        return True
