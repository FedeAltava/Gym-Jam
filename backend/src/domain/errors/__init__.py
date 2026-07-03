"""Domain errors — public re-exports."""
from backend.src.domain.errors.base import DomainError, SessionError, TrainingDayError, WorkoutExerciseError
from backend.src.domain.errors.training_day_errors import (
    CannotRemoveDayWithExercisesError,
    DayAlreadyInWorkoutError,
    DayNotInWorkoutError,
)
from backend.src.domain.errors.workout_exercise_errors import (
    DuplicateExerciseInDayError,
    ExerciseNotFoundInDayError,
    ReorderMismatchError,
)
from backend.src.domain.errors.session_errors import (
    InvalidRepsCompleted,
    SessionAlreadyCompleted,
    SessionNotFound,
    SetAlreadyLogged,
    SetExceedsPlan,
)

__all__ = [
    "CannotRemoveDayWithExercisesError",
    "DayAlreadyInWorkoutError",
    "DayNotInWorkoutError",
    "DomainError",
    "DuplicateExerciseInDayError",
    "ExerciseNotFoundInDayError",
    "InvalidRepsCompleted",
    "ReorderMismatchError",
    "SessionAlreadyCompleted",
    "SessionError",
    "SessionNotFound",
    "SetAlreadyLogged",
    "SetExceedsPlan",
    "TrainingDayError",
    "WorkoutExerciseError",
]
