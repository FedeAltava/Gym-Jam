from __future__ import annotations
from datetime import datetime, UTC
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.entities.training_day import TrainingDay
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.value_objects import (
    WorkoutId,
    TrainingDayId,
    WorkoutExerciseId,
    WorkoutName,
    DayOfWeek,
)
from backend.src.infrastructure.persistence.models import (
    WorkoutModel,
    TrainingDayModel,
    WorkoutExerciseModel,
)


class WorkoutMapper:
    @staticmethod
    def to_domain(model: WorkoutModel) -> Workout:
        training_days: dict[DayOfWeek, TrainingDay] = {}
        for day_model in model.training_days:
            day_of_week = DayOfWeek(day_model.day_of_week)
            exercises: list[WorkoutExercise] = []
            workout_id = WorkoutId(model.id)
            for ex_model in day_model.exercises:
                exercise = WorkoutExercise(
                    id=WorkoutExerciseId(ex_model.id),
                    workout_id=workout_id,
                    day=day_of_week,
                    exercise_id=ex_model.exercise_id,
                    order=ex_model.order_in_day,
                )
                exercises.append(exercise)
            day = TrainingDay(
                id=TrainingDayId(day_model.id),
                workout_id=workout_id,
                day=day_of_week,
                _exercises=exercises,
            )
            training_days[day_of_week] = day

        workout = Workout(
            id=WorkoutId(model.id),
            user_id=model.user_id,
            name=WorkoutName.create(model.name).unwrap(),
            description=model.description,
            is_active=model.is_active,
            created_at=model.created_at,
            _training_days=training_days,
            _events=[],
        )
        return workout

    @staticmethod
    def to_model(domain: Workout) -> WorkoutModel:
        workout_model = WorkoutModel(
            id=str(domain.id.value),
            user_id=domain.user_id,
            name=str(domain.name.value),
            description=domain.description,
            is_active=domain.is_active,
            created_at=domain.created_at,
            updated_at=datetime.now(UTC),
        )
        training_day_models: list[TrainingDayModel] = []
        for day_of_week, day in domain.get_training_days().items():
            day_model = TrainingDayModel(
                id=str(day.id.value),
                workout_id=str(domain.id.value),
                day_of_week=day_of_week.value,
            )
            exercise_models: list[WorkoutExerciseModel] = []
            for ex in day.exercises:
                ex_model = WorkoutExerciseModel(
                    id=str(ex.id.value),
                    workout_id=str(domain.id.value),
                    training_day_id=str(day.id.value),
                    exercise_id=ex.exercise_id,
                    order_in_day=ex.order,
                )
                exercise_models.append(ex_model)
            day_model.exercises = exercise_models
            training_day_models.append(day_model)
        workout_model.training_days = training_day_models
        return workout_model
