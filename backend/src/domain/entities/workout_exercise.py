"""WorkoutExercise entity — identity-based equality, mutable order."""
from dataclasses import dataclass

from backend.src.domain.value_objects import DayOfWeek, WorkoutExerciseId, WorkoutId


@dataclass(eq=False)
class WorkoutExercise:
    id: WorkoutExerciseId
    workout_id: WorkoutId
    day: DayOfWeek
    exercise_id: str   # external catalog reference
    order: int         # 1-based, managed by TrainingDay

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WorkoutExercise):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
