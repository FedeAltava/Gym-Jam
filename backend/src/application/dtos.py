from __future__ import annotations

from dataclasses import dataclass

from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.entities.training_day import TrainingDay
from backend.src.domain.entities.workout_exercise import WorkoutExercise


@dataclass(frozen=True)
class WorkoutExerciseDTO:
    id: str
    exercise_id: str
    day: str
    order: int

    @classmethod
    def from_entity(cls, exercise: WorkoutExercise) -> "WorkoutExerciseDTO":
        return cls(
            id=str(exercise.id.value),
            exercise_id=exercise.exercise_id,
            day=exercise.day.value,
            order=exercise.order,
        )


@dataclass(frozen=True)
class TrainingDayDTO:
    day_of_week: str
    exercises: tuple[WorkoutExerciseDTO, ...]

    @classmethod
    def from_entity(cls, training_day: TrainingDay) -> "TrainingDayDTO":
        return cls(
            day_of_week=training_day.day.value,
            exercises=tuple(
                WorkoutExerciseDTO.from_entity(ex)
                for ex in training_day.exercises
            ),
        )


@dataclass(frozen=True)
class WorkoutWithDaysDTO:
    id: str
    user_id: str
    name: str
    description: str | None
    is_active: bool
    training_days: tuple[TrainingDayDTO, ...]

    @classmethod
    def from_aggregate(cls, workout: Workout) -> "WorkoutWithDaysDTO":
        return cls(
            id=str(workout.id.value),
            user_id=workout.user_id,
            name=workout.name.value,
            description=workout.description,
            is_active=workout.is_active,
            training_days=tuple(
                TrainingDayDTO.from_entity(td)
                for td in workout.get_training_days().values()
            ),
        )
