"""ExerciseLog entity — a single logged set within a WorkoutSession."""
from dataclasses import dataclass

from backend.src.domain.value_objects.exercise_log_id import ExerciseLogId
from backend.src.domain.value_objects.workout_exercise_id import WorkoutExerciseId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


@dataclass(eq=False)
class ExerciseLog:
    id: ExerciseLogId
    session_id: WorkoutSessionId
    workout_exercise_id: WorkoutExerciseId
    set_number: int
    reps_completed: int
    weight_kg: float | None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExerciseLog):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
