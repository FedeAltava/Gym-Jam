"""Tests for Workout aggregate root — Fase 3 Slice 2."""
from __future__ import annotations

import pytest
from returns.result import Failure, Success

from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.errors.training_day_errors import (
    CannotRemoveDayWithExercisesError,
    DayAlreadyInWorkoutError,
    DayNotInWorkoutError,
)
from backend.src.domain.events.training_day_events import (
    TrainingDayAddedEvent,
    TrainingDayRemovedEvent,
)
from backend.src.domain.events.workout_events import WorkoutCreatedEvent
from backend.src.domain.value_objects import (
    DayOfWeek,
    WorkoutExerciseId,
    WorkoutId,
)


# ---------------------------------------------------------------------------
# create() — 8 tests
# ---------------------------------------------------------------------------


def test_create_workout_with_valid_name_returns_success():
    result = Workout.create(user_id="user-1", name="Push Day")
    assert isinstance(result, Success)
    workout = result.unwrap()
    assert workout.name.value == "Push Day"
    assert workout.user_id == "user-1"


def test_create_workout_initializes_training_days():
    result = Workout.create(
        user_id="user-1",
        name="Full Body",
        training_days=[DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY],
    )
    assert isinstance(result, Success)
    workout = result.unwrap()
    days = workout.get_training_days_list()
    assert DayOfWeek.MONDAY in days
    assert DayOfWeek.WEDNESDAY in days
    assert len(days) == 2


def test_create_workout_empty_name_returns_failure():
    result = Workout.create(user_id="user-1", name="")
    assert isinstance(result, Failure)


def test_create_workout_name_too_short_returns_failure():
    result = Workout.create(user_id="user-1", name="A")
    assert isinstance(result, Failure)


def test_create_workout_name_too_long_returns_failure():
    result = Workout.create(user_id="user-1", name="X" * 101)
    assert isinstance(result, Failure)


def test_create_workout_name_leading_whitespace_returns_failure():
    result = Workout.create(user_id="user-1", name="  Push Day")
    assert isinstance(result, Failure)


def test_create_workout_emits_workout_created_event():
    result = Workout.create(user_id="user-1", name="Push Day")
    workout = result.unwrap()
    events = workout.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], WorkoutCreatedEvent)
    assert events[0].workout_id == str(workout.id.value)
    assert events[0].user_id == "user-1"
    assert events[0].name == "Push Day"


def test_create_workout_with_explicit_workout_id():
    explicit_id = WorkoutId.generate()
    result = Workout.create(user_id="user-1", name="Push Day", workout_id=explicit_id)
    assert isinstance(result, Success)
    workout = result.unwrap()
    assert workout.id == explicit_id


# ---------------------------------------------------------------------------
# add_training_day — 4 tests
# ---------------------------------------------------------------------------


def test_add_training_day_increases_count():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    workout.pull_events()  # clear
    workout.add_training_day(DayOfWeek.MONDAY)
    assert DayOfWeek.MONDAY in workout.get_training_days_list()
    assert len(workout.get_training_days_list()) == 1


def test_add_training_day_emits_event():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    workout.pull_events()
    workout.add_training_day(DayOfWeek.TUESDAY)
    events = workout.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], TrainingDayAddedEvent)
    assert events[0].day == DayOfWeek.TUESDAY.value


def test_add_duplicate_training_day_raises_error():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    with pytest.raises(DayAlreadyInWorkoutError):
        workout.add_training_day(DayOfWeek.MONDAY)


def test_add_all_seven_days():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    for day in DayOfWeek:
        workout.add_training_day(day)
    assert len(workout.get_training_days_list()) == 7


# ---------------------------------------------------------------------------
# remove_training_day — 5 tests
# ---------------------------------------------------------------------------


def test_remove_training_day_decreases_count():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY],
    ).unwrap()
    workout.remove_training_day(DayOfWeek.MONDAY)
    assert DayOfWeek.MONDAY not in workout.get_training_days_list()
    assert len(workout.get_training_days_list()) == 1


def test_remove_training_day_emits_event():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    workout.pull_events()
    workout.remove_training_day(DayOfWeek.MONDAY)
    events = workout.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], TrainingDayRemovedEvent)
    assert events[0].day == DayOfWeek.MONDAY.value


def test_remove_nonexistent_training_day_raises_error():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    with pytest.raises(DayNotInWorkoutError):
        workout.remove_training_day(DayOfWeek.FRIDAY)


def test_remove_training_day_with_exercises_raises_error():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    workout.add_exercise_to_day(DayOfWeek.MONDAY, "exercise-abc")
    with pytest.raises(CannotRemoveDayWithExercisesError):
        workout.remove_training_day(DayOfWeek.MONDAY)


def test_remove_training_day_does_not_affect_other_days():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY],
    ).unwrap()
    workout.add_exercise_to_day(DayOfWeek.MONDAY, "exercise-xyz")
    with pytest.raises(CannotRemoveDayWithExercisesError):
        workout.remove_training_day(DayOfWeek.MONDAY)
    days = workout.get_training_days_list()
    assert DayOfWeek.TUESDAY in days
    assert len(workout.get_exercises_for_day(DayOfWeek.MONDAY)) == 1


# ---------------------------------------------------------------------------
# add_exercise_to_day — 4 tests
# ---------------------------------------------------------------------------


def test_add_exercise_to_day_returns_workout_exercise():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    exercise = workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-123")
    assert exercise.exercise_id == "ex-123"
    assert exercise.day == DayOfWeek.MONDAY


def test_add_exercise_to_nonexistent_day_raises_error():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    with pytest.raises(DayNotInWorkoutError):
        workout.add_exercise_to_day(DayOfWeek.FRIDAY, "ex-123")


def test_add_duplicate_exercise_to_day_raises_error():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-123")
    from backend.src.domain.errors.workout_exercise_errors import DuplicateExerciseInDayError
    with pytest.raises(DuplicateExerciseInDayError):
        workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-123")


def test_add_exercise_with_explicit_id():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    explicit_id = WorkoutExerciseId.generate()
    exercise = workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-456", explicit_id)
    assert exercise.id == explicit_id


# ---------------------------------------------------------------------------
# remove_exercise_from_day — 3 tests
# ---------------------------------------------------------------------------


def test_remove_exercise_from_day_succeeds():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    exercise = workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-123")
    workout.remove_exercise_from_day(DayOfWeek.MONDAY, exercise.id)
    assert len(workout.get_exercises_for_day(DayOfWeek.MONDAY)) == 0


def test_remove_exercise_from_nonexistent_day_raises_error():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    with pytest.raises(DayNotInWorkoutError):
        workout.remove_exercise_from_day(DayOfWeek.FRIDAY, WorkoutExerciseId.generate())


def test_remove_nonexistent_exercise_raises_error():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    from backend.src.domain.errors.workout_exercise_errors import ExerciseNotFoundInDayError
    with pytest.raises(ExerciseNotFoundInDayError):
        workout.remove_exercise_from_day(DayOfWeek.MONDAY, WorkoutExerciseId.generate())


# ---------------------------------------------------------------------------
# reorder_exercises_in_day — 3 tests
# ---------------------------------------------------------------------------


def test_reorder_exercises_in_day_succeeds():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    ex1 = workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-1")
    ex2 = workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-2")
    workout.reorder_exercises_in_day(DayOfWeek.MONDAY, [ex2.id, ex1.id])
    exercises = workout.get_exercises_for_day(DayOfWeek.MONDAY)
    assert exercises[0].id == ex2.id
    assert exercises[1].id == ex1.id


def test_reorder_exercises_in_nonexistent_day_raises_error():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    with pytest.raises(DayNotInWorkoutError):
        workout.reorder_exercises_in_day(DayOfWeek.FRIDAY, [])


def test_reorder_exercises_with_wrong_ids_raises_error():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-1")
    from backend.src.domain.errors.workout_exercise_errors import ReorderMismatchError
    with pytest.raises(ReorderMismatchError):
        workout.reorder_exercises_in_day(DayOfWeek.MONDAY, [WorkoutExerciseId.generate()])


# ---------------------------------------------------------------------------
# activate / deactivate — 3 tests
# ---------------------------------------------------------------------------


def test_new_workout_is_active_by_default():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    assert workout.is_active is True


def test_deactivate_sets_is_active_false():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    workout.deactivate()
    assert workout.is_active is False


def test_activate_sets_is_active_true():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    workout.deactivate()
    workout.activate()
    assert workout.is_active is True


# ---------------------------------------------------------------------------
# get_exercises_for_day — 3 tests
# ---------------------------------------------------------------------------


def test_get_exercises_for_day_returns_sorted_list():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    ex1 = workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-1")
    ex2 = workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-2")
    workout.reorder_exercises_in_day(DayOfWeek.MONDAY, [ex2.id, ex1.id])
    exercises = workout.get_exercises_for_day(DayOfWeek.MONDAY)
    assert exercises[0].id == ex2.id
    assert exercises[1].id == ex1.id


def test_get_exercises_for_empty_day_returns_empty_list():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    exercises = workout.get_exercises_for_day(DayOfWeek.MONDAY)
    assert exercises == []


def test_get_exercises_for_nonexistent_day_raises_error():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    with pytest.raises(DayNotInWorkoutError):
        workout.get_exercises_for_day(DayOfWeek.FRIDAY)


# ---------------------------------------------------------------------------
# get_training_days queries — 3 tests
# ---------------------------------------------------------------------------


def test_get_training_days_returns_defensive_copy():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    copy = workout.get_training_days()
    copy[DayOfWeek.TUESDAY] = None  # type: ignore[assignment]
    assert DayOfWeek.TUESDAY not in workout.get_training_days()


def test_get_training_days_list_returns_list_of_day_of_week():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY, DayOfWeek.FRIDAY],
    ).unwrap()
    days = workout.get_training_days_list()
    assert isinstance(days, list)
    assert all(isinstance(d, DayOfWeek) for d in days)
    assert len(days) == 2


def test_get_training_days_empty_when_no_days():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    assert workout.get_training_days_list() == []


# ---------------------------------------------------------------------------
# pull_events — 4 tests
# ---------------------------------------------------------------------------


def test_pull_events_after_create_returns_workout_created_event():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    events = workout.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], WorkoutCreatedEvent)


def test_pull_events_after_add_training_day_includes_event():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    workout.pull_events()
    workout.add_training_day(DayOfWeek.MONDAY)
    events = workout.pull_events()
    assert any(isinstance(e, TrainingDayAddedEvent) for e in events)


def test_pull_events_collects_child_training_day_events():
    workout = Workout.create(
        user_id="u",
        name="Test Workout",
        training_days=[DayOfWeek.MONDAY],
    ).unwrap()
    workout.pull_events()  # clear create + init events
    workout.add_exercise_to_day(DayOfWeek.MONDAY, "ex-1")
    events = workout.pull_events()
    from backend.src.domain.events.training_day_events import ExerciseAddedToDayEvent
    assert any(isinstance(e, ExerciseAddedToDayEvent) for e in events)


def test_pull_events_is_idempotent_second_call_returns_empty():
    workout = Workout.create(user_id="u", name="Test Workout").unwrap()
    workout.pull_events()  # drain
    events = workout.pull_events()
    assert events == []
