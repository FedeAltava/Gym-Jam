"""Training day domain errors."""
from backend.src.domain.errors.base import TrainingDayError


class DayNotInWorkoutError(TrainingDayError):
    def __init__(self, day: str, workout_id: str) -> None:
        super().__init__(f"Day '{day}' is not in workout '{workout_id}'.")
        self.day = day
        self.workout_id = workout_id


class DayAlreadyInWorkoutError(TrainingDayError):
    def __init__(self, day: str, workout_id: str) -> None:
        super().__init__(f"Day '{day}' already exists in workout '{workout_id}'.")
        self.day = day
        self.workout_id = workout_id


class CannotRemoveDayWithExercisesError(TrainingDayError):
    def __init__(self, day: str, exercise_count: int) -> None:
        super().__init__(
            f"Cannot remove day '{day}' — it still has {exercise_count} exercise(s)."
        )
        self.day = day
        self.exercise_count = exercise_count
