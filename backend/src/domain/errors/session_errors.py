"""Session domain errors."""
from backend.src.domain.errors.base import SessionError


class SessionAlreadyCompleted(SessionError):
    def __init__(self) -> None:
        super().__init__("Cannot modify a session that has already been completed.")


class SetExceedsPlan(SessionError):
    def __init__(self, set_number: int, max_sets: int) -> None:
        super().__init__(
            f"Set number {set_number} exceeds the plan maximum of {max_sets} sets."
        )
        self.set_number = set_number
        self.max_sets = max_sets


class SetAlreadyLogged(SessionError):
    def __init__(self, workout_exercise_id: str, set_number: int) -> None:
        super().__init__(
            f"Set {set_number} for exercise '{workout_exercise_id}' has already been logged."
        )
        self.workout_exercise_id = workout_exercise_id
        self.set_number = set_number


class InvalidRepsCompleted(SessionError):
    def __init__(self, reps: int) -> None:
        super().__init__(
            f"Reps completed must be at least 1, got {reps}."
        )
        self.reps = reps


class SessionNotFound(SessionError):
    def __init__(self) -> None:
        super().__init__("Workout session not found.")
