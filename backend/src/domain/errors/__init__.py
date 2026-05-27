"""Domain errors — public re-exports."""
from backend.src.domain.errors.base import DomainError, TrainingDayError, WorkoutExerciseError
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

__all__ = [
    "CannotRemoveDayWithExercisesError",
    "DayAlreadyInWorkoutError",
    "DayNotInWorkoutError",
    "DomainError",
    "DuplicateExerciseInDayError",
    "ExerciseNotFoundInDayError",
    "ReorderMismatchError",
    "TrainingDayError",
    "WorkoutExerciseError",
]
