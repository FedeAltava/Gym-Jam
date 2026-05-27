"""Workout exercise domain errors."""
from backend.src.domain.errors.base import WorkoutExerciseError


class ExerciseNotFoundInDayError(WorkoutExerciseError):
    def __init__(self, workout_exercise_id: str) -> None:
        super().__init__(f"WorkoutExercise '{workout_exercise_id}' not found in this day.")
        self.workout_exercise_id = workout_exercise_id


class DuplicateExerciseInDayError(WorkoutExerciseError):
    def __init__(self, exercise_id: str, day: str) -> None:
        super().__init__(f"Exercise '{exercise_id}' already exists in day '{day}'.")
        self.exercise_id = exercise_id
        self.day = day


class ReorderMismatchError(WorkoutExerciseError):
    def __init__(self, missing: set, extra: set) -> None:
        super().__init__(
            f"Reorder mismatch — missing: {missing}, extra: {extra}."
        )
        self.missing = missing
        self.extra = extra
