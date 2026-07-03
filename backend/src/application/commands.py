from dataclasses import dataclass


@dataclass(frozen=True)
class CreateWorkoutCommand:
    user_id: str
    name: str
    description: str | None
    training_days: tuple[str, ...]  # DayOfWeek string values


@dataclass(frozen=True)
class AddExerciseToWorkoutCommand:
    workout_id: str
    user_id: str
    day_of_week: str
    exercise_id: str
    sets: int = 3
    reps_per_set: int = 10
    weight_kg: float | None = None


@dataclass(frozen=True)
class RemoveExerciseFromWorkoutCommand:
    workout_id: str
    user_id: str
    day_of_week: str
    workout_exercise_id: str


@dataclass(frozen=True)
class AddTrainingDayCommand:
    workout_id: str
    user_id: str
    day_of_week: str


@dataclass(frozen=True)
class RemoveTrainingDayCommand:
    workout_id: str
    user_id: str
    day_of_week: str


@dataclass(frozen=True)
class ReorderExercisesCommand:
    workout_id: str
    user_id: str
    day_of_week: str
    ordered_exercise_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReorderTrainingDaysCommand:
    workout_id: str
    user_id: str
    ordered_day_ids: tuple[str, ...]


@dataclass(frozen=True)
class GetWorkoutWithDaysQuery:
    workout_id: str
    user_id: str


@dataclass(frozen=True)
class DeleteWorkoutCommand:
    workout_id: str
    user_id: str


@dataclass(frozen=True)
class StartWorkoutSessionCommand:
    user_id: str
    workout_id: str
    training_day_id: str


@dataclass(frozen=True)
class LogExerciseSetCommand:
    user_id: str
    session_id: str
    workout_exercise_id: str
    set_number: int
    reps_completed: int
    weight_kg: float | None


@dataclass(frozen=True)
class CompleteWorkoutSessionCommand:
    user_id: str
    session_id: str


@dataclass(frozen=True)
class GetSessionsForDayCommand:
    user_id: str
    workout_id: str
    training_day_id: str
