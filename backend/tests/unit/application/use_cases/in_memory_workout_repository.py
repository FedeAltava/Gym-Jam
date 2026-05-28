from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutId


class InMemoryWorkoutRepository(WorkoutRepository):
    def __init__(self) -> None:
        self._store: dict[str, Workout] = {}

    def save(self, workout: Workout) -> None:
        self._store[str(workout.id.value)] = workout

    def get_by_id(self, workout_id: WorkoutId) -> Workout | None:
        return self._store.get(str(workout_id.value))

    def get_by_user(self, user_id: str) -> list[Workout]:
        return [w for w in self._store.values() if w.user_id == user_id]
