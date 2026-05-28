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
class GetWorkoutWithDaysQuery:
    workout_id: str
    user_id: str
