from __future__ import annotations
from datetime import datetime, UTC
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.entities.exercise_log import ExerciseLog
from backend.src.domain.entities.training_day import TrainingDay
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import (
    WorkoutId,
    TrainingDayId,
    WorkoutExerciseId,
    WorkoutName,
    DayOfWeek,
    ExerciseLogId,
    WorkoutSessionId,
)
from backend.src.domain.value_objects.training_day_id import TrainingDayId
from backend.src.infrastructure.persistence.models import (
    WorkoutModel,
    WorkoutLogModel,
    WorkoutSessionModel,
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
            workout_id = WorkoutId.from_string(model.id).unwrap()
            for ex_model in day_model.exercises:
                exercise = WorkoutExercise(
                    id=WorkoutExerciseId.from_string(ex_model.id).unwrap(),
                    workout_id=workout_id,
                    day=day_of_week,
                    exercise_id=ex_model.exercise_id,
                    order=ex_model.order_in_day,
                    sets=ex_model.sets,
                    reps_per_set=ex_model.reps_per_set,
                    weight_kg=ex_model.weight_kg,
                )
                exercises.append(exercise)
            day = TrainingDay(
                id=TrainingDayId.from_string(day_model.id).unwrap(),
                workout_id=workout_id,
                day=day_of_week,
                order=day_model.order,
                _exercises=exercises,
            )
            training_days[day_of_week] = day

        workout = Workout(
            id=WorkoutId.from_string(model.id).unwrap(),
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
                order=day.order,
            )
            exercise_models: list[WorkoutExerciseModel] = []
            for ex in day.exercises:
                ex_model = WorkoutExerciseModel(
                    id=str(ex.id.value),
                    workout_id=str(domain.id.value),
                    training_day_id=str(day.id.value),
                    exercise_id=ex.exercise_id,
                    order_in_day=ex.order,
                    sets=ex.sets,
                    reps_per_set=ex.reps_per_set,
                    weight_kg=ex.weight_kg,
                )
                exercise_models.append(ex_model)
            day_model.exercises = exercise_models
            training_day_models.append(day_model)
        workout_model.training_days = training_day_models
        return workout_model


class WorkoutSessionMapper:
    @staticmethod
    def to_domain(model: WorkoutSessionModel) -> WorkoutSession:
        logs: list[ExerciseLog] = []
        for log_model in model.logs:
            log = ExerciseLog(
                id=ExerciseLogId.from_string(log_model.id).unwrap(),
                session_id=WorkoutSessionId.from_string(log_model.session_id).unwrap(),
                workout_exercise_id=WorkoutExerciseId.from_string(log_model.workout_exercise_id).unwrap(),
                set_number=log_model.set_number,
                reps_completed=log_model.reps_completed,
                weight_kg=log_model.weight_kg,
            )
            logs.append(log)

        def _as_utc(dt: datetime | None) -> datetime | None:
            if dt is None:
                return None
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

        return WorkoutSession(
            id=WorkoutSessionId.from_string(model.id).unwrap(),
            user_id=model.user_id,
            workout_id=WorkoutId.from_string(model.workout_id).unwrap(),
            training_day_id=TrainingDayId.from_string(model.training_day_id).unwrap(),
            started_at=_as_utc(model.started_at),
            completed_at=_as_utc(model.completed_at),
            _logs=logs,
        )

    @staticmethod
    def to_model(session: WorkoutSession) -> WorkoutSessionModel:
        session_model = WorkoutSessionModel(
            id=str(session.id.value),
            user_id=session.user_id,
            workout_id=str(session.workout_id.value),
            training_day_id=str(session.training_day_id.value),
            started_at=session.started_at,
            completed_at=session.completed_at,
        )
        log_models: list[WorkoutLogModel] = []
        for log in session.logs:
            log_model = WorkoutLogModel(
                id=str(log.id.value),
                session_id=str(session.id.value),
                workout_exercise_id=str(log.workout_exercise_id.value),
                set_number=log.set_number,
                reps_completed=log.reps_completed,
                weight_kg=log.weight_kg,
            )
            log_models.append(log_model)
        session_model.logs = log_models
        return session_model
