from __future__ import annotations

from dataclasses import dataclass

from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.entities.exercise import Exercise
from backend.src.domain.entities.exercise_log import ExerciseLog
from backend.src.domain.entities.training_day import TrainingDay
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.entities.workout_session import WorkoutSession


@dataclass(frozen=True)
class ExerciseDTO:
    id: str
    name: str
    muscle_group: str
    is_bodyweight: bool

    @classmethod
    def from_entity(cls, exercise: Exercise) -> "ExerciseDTO":
        return cls(
            id=exercise.id,
            name=exercise.name,
            muscle_group=exercise.muscle_group,
            is_bodyweight=exercise.is_bodyweight,
        )


@dataclass(frozen=True)
class TokenPairDTO:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class WorkoutExerciseDTO:
    id: str
    exercise_id: str
    day: str
    order: int
    sets: int
    reps_per_set: int
    weight_kg: float | None

    @classmethod
    def from_entity(cls, exercise: WorkoutExercise) -> "WorkoutExerciseDTO":
        return cls(
            id=str(exercise.id.value),
            exercise_id=exercise.exercise_id,
            day=exercise.day.value,
            order=exercise.order,
            sets=exercise.sets,
            reps_per_set=exercise.reps_per_set,
            weight_kg=exercise.weight_kg,
        )

    @classmethod
    def from_exercise(cls, exercise: WorkoutExercise) -> "WorkoutExerciseDTO":
        return cls.from_entity(exercise)


@dataclass(frozen=True)
class TrainingDayDTO:
    id: str
    day_of_week: str
    order: int
    exercises: tuple[WorkoutExerciseDTO, ...]

    @classmethod
    def from_entity(cls, training_day: TrainingDay) -> "TrainingDayDTO":
        return cls(
            id=str(training_day.id.value),
            day_of_week=training_day.day.value,
            order=training_day.order,
            exercises=tuple(
                WorkoutExerciseDTO.from_entity(ex)
                for ex in training_day.exercises
            ),
        )

    @classmethod
    def from_training_day(cls, training_day: TrainingDay) -> "TrainingDayDTO":
        return cls.from_entity(training_day)


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
                for td in sorted(
                    workout.get_training_days().values(),
                    key=lambda td: td.order,
                )
            ),
        )

    @classmethod
    def from_workout(cls, workout: Workout) -> "WorkoutWithDaysDTO":
        return cls.from_aggregate(workout)


@dataclass(frozen=True)
class ExerciseLogDTO:
    id: str
    session_id: str
    workout_exercise_id: str
    set_number: int
    reps_completed: int
    weight_kg: float | None

    @classmethod
    def from_entity(cls, log: ExerciseLog) -> "ExerciseLogDTO":
        return cls(
            id=str(log.id.value),
            session_id=str(log.session_id.value),
            workout_exercise_id=str(log.workout_exercise_id.value),
            set_number=log.set_number,
            reps_completed=log.reps_completed,
            weight_kg=log.weight_kg,
        )


@dataclass(frozen=True)
class WorkoutSessionDTO:
    id: str
    user_id: str
    workout_id: str
    training_day_id: str
    started_at: str
    status: str
    completed_at: str | None
    logs: tuple[ExerciseLogDTO, ...]

    @classmethod
    def from_aggregate(cls, session: WorkoutSession) -> "WorkoutSessionDTO":
        return cls(
            id=str(session.id.value),
            user_id=session.user_id,
            workout_id=str(session.workout_id.value),
            training_day_id=str(session.training_day_id.value),
            started_at=session.started_at.isoformat(),
            status=session.status,
            completed_at=session.completed_at.isoformat() if session.completed_at is not None else None,
            logs=tuple(ExerciseLogDTO.from_entity(log) for log in session.logs),
        )
