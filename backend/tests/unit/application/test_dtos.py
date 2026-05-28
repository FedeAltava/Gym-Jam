"""Tests for application DTOs."""
from backend.src.application.dtos import TrainingDayDTO, WorkoutExerciseDTO, WorkoutWithDaysDTO
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.entities.training_day import TrainingDay
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.value_objects import (
    DayOfWeek,
    TrainingDayId,
    WorkoutExerciseId,
    WorkoutId,
    WorkoutName,
)


def _make_workout_exercise(
    exercise_id: str = "ex-1",
    day: DayOfWeek = DayOfWeek.MONDAY,
    order: int = 1,
) -> WorkoutExercise:
    workout_id = WorkoutId.generate()
    return WorkoutExercise(
        id=WorkoutExerciseId.generate(),
        workout_id=workout_id,
        day=day,
        exercise_id=exercise_id,
        order=order,
    )


def _make_training_day(day: DayOfWeek = DayOfWeek.MONDAY) -> TrainingDay:
    workout_id = WorkoutId.generate()
    return TrainingDay(
        id=TrainingDayId.generate(),
        workout_id=workout_id,
        day=day,
    )


def test_workout_exercise_dto_stores_fields() -> None:
    exercise = _make_workout_exercise(exercise_id="ex-42", day=DayOfWeek.WEDNESDAY, order=3)
    dto = WorkoutExerciseDTO.from_entity(exercise)

    assert dto.id == str(exercise.id.value)
    assert dto.exercise_id == "ex-42"
    assert dto.day == "WEDNESDAY"
    assert dto.order == 3


def test_training_day_dto_stores_exercises() -> None:
    td = _make_training_day(day=DayOfWeek.FRIDAY)
    td.add_exercise("ex-1")
    td.add_exercise("ex-2")

    dto = TrainingDayDTO.from_entity(td)

    assert dto.day_of_week == "FRIDAY"
    assert len(dto.exercises) == 2
    assert dto.exercises[0].exercise_id == "ex-1"
    assert dto.exercises[1].exercise_id == "ex-2"


def test_workout_with_days_dto_stores_all_fields() -> None:
    result = Workout.create(
        user_id="user-1",
        name="Push Day",
        description="Upper body push",
        training_days=[DayOfWeek.MONDAY, DayOfWeek.THURSDAY],
    )
    workout = result.unwrap()

    dto = WorkoutWithDaysDTO.from_aggregate(workout)

    assert dto.id == str(workout.id.value)
    assert dto.user_id == "user-1"
    assert dto.name == "Push Day"
    assert dto.description == "Upper body push"
    assert dto.is_active is True
    assert len(dto.training_days) == 2
    days = {td.day_of_week for td in dto.training_days}
    assert days == {"MONDAY", "THURSDAY"}


def test_workout_with_days_dto_no_description() -> None:
    result = Workout.create(user_id="user-2", name="Legs")
    workout = result.unwrap()
    dto = WorkoutWithDaysDTO.from_aggregate(workout)

    assert dto.description is None
    assert len(dto.training_days) == 0
