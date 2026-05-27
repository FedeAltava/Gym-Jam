"""Tests for TrainingDay entity — RED phase."""
import pytest

from backend.src.domain.value_objects import (
    DayOfWeek,
    TrainingDayId,
    WorkoutExerciseId,
    WorkoutId,
)
from backend.src.domain.entities.training_day import TrainingDay
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.errors.workout_exercise_errors import (
    DuplicateExerciseInDayError,
    ExerciseNotFoundInDayError,
    ReorderMismatchError,
)
from backend.src.domain.events.training_day_events import (
    ExerciseAddedToDayEvent,
    ExerciseRemovedFromDayEvent,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_day(
    *,
    day_id: TrainingDayId | None = None,
    workout_id: WorkoutId | None = None,
    day: DayOfWeek = DayOfWeek.MONDAY,
) -> TrainingDay:
    return TrainingDay(
        id=day_id or TrainingDayId.generate(),
        workout_id=workout_id or WorkoutId.generate(),
        day=day,
    )


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------

class TestTrainingDayCreation:
    def test_training_day_creation_empty_exercises(self) -> None:
        td = _make_day()
        assert td.exercises == []

    def test_training_day_equality_by_id(self) -> None:
        shared_id = TrainingDayId.generate()
        td1 = TrainingDay(id=shared_id, workout_id=WorkoutId.generate(), day=DayOfWeek.MONDAY)
        td2 = TrainingDay(id=shared_id, workout_id=WorkoutId.generate(), day=DayOfWeek.FRIDAY)
        assert td1 == td2

    def test_training_day_inequality_different_id(self) -> None:
        td1 = _make_day()
        td2 = _make_day()
        assert td1 != td2


# ---------------------------------------------------------------------------
# exercises property
# ---------------------------------------------------------------------------

class TestTrainingDayExercisesProperty:
    def test_training_day_exercises_property_returns_sorted_by_order(self) -> None:
        td = _make_day()
        ex1 = td.add_exercise("ex-A")
        ex2 = td.add_exercise("ex-B")
        # Force out-of-order by manually swapping orders
        ex1.order = 3
        ex2.order = 1
        sorted_exercises = td.exercises
        assert sorted_exercises[0].exercise_id == "ex-B"
        assert sorted_exercises[1].exercise_id == "ex-A"

    def test_training_day_exercises_property_returns_defensive_copy(self) -> None:
        td = _make_day()
        td.add_exercise("ex-A")
        copy1 = td.exercises
        copy1.clear()
        assert len(td.exercises) == 1


# ---------------------------------------------------------------------------
# pull_events
# ---------------------------------------------------------------------------

class TestTrainingDayEvents:
    def test_training_day_pull_events_clears_after_return(self) -> None:
        td = _make_day()
        td.add_exercise("ex-A")
        events = td.pull_events()
        assert len(events) == 1
        assert td.pull_events() == []


# ---------------------------------------------------------------------------
# add_exercise
# ---------------------------------------------------------------------------

class TestAddExercise:
    def test_add_exercise_appends_to_empty_day(self) -> None:
        td = _make_day()
        td.add_exercise("ex-A")
        assert len(td.exercises) == 1

    def test_add_exercise_second_gets_next_order(self) -> None:
        td = _make_day()
        td.add_exercise("ex-A")
        ex2 = td.add_exercise("ex-B")
        assert ex2.order == 2

    def test_add_exercise_returns_workout_exercise(self) -> None:
        td = _make_day()
        result = td.add_exercise("ex-A")
        assert isinstance(result, WorkoutExercise)

    def test_add_exercise_emits_exercise_added_event(self) -> None:
        td = _make_day()
        td.add_exercise("ex-A")
        events = td.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], ExerciseAddedToDayEvent)

    def test_add_exercise_event_contains_correct_fields(self) -> None:
        td = _make_day()
        ex = td.add_exercise("ex-A")
        events = td.pull_events()
        evt = events[0]
        assert isinstance(evt, ExerciseAddedToDayEvent)
        assert evt.exercise_id == "ex-A"
        assert evt.workout_exercise_id == str(ex.id.value)
        assert evt.training_day_id == str(td.id.value)
        assert evt.order == 1

    def test_add_exercise_raises_duplicate_error(self) -> None:
        td = _make_day()
        td.add_exercise("ex-A")
        with pytest.raises(DuplicateExerciseInDayError):
            td.add_exercise("ex-A")

    def test_add_exercise_generates_id_if_not_provided(self) -> None:
        td = _make_day()
        ex = td.add_exercise("ex-A")
        assert isinstance(ex.id, WorkoutExerciseId)


# ---------------------------------------------------------------------------
# remove_exercise
# ---------------------------------------------------------------------------

class TestRemoveExercise:
    def test_remove_exercise_reduces_count(self) -> None:
        td = _make_day()
        ex = td.add_exercise("ex-A")
        td.pull_events()  # clear
        td.remove_exercise(ex.id)
        assert len(td.exercises) == 0

    def test_remove_exercise_emits_exercise_removed_event(self) -> None:
        td = _make_day()
        ex = td.add_exercise("ex-A")
        td.pull_events()
        td.remove_exercise(ex.id)
        events = td.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], ExerciseRemovedFromDayEvent)

    def test_remove_exercise_event_contains_correct_fields(self) -> None:
        td = _make_day()
        ex = td.add_exercise("ex-A")
        td.pull_events()
        td.remove_exercise(ex.id)
        events = td.pull_events()
        evt = events[0]
        assert isinstance(evt, ExerciseRemovedFromDayEvent)
        assert evt.training_day_id == str(td.id.value)
        assert evt.workout_exercise_id == str(ex.id.value)
        assert evt.exercise_id == "ex-A"

    def test_remove_exercise_raises_not_found(self) -> None:
        td = _make_day()
        with pytest.raises(ExerciseNotFoundInDayError):
            td.remove_exercise(WorkoutExerciseId.generate())

    def test_remove_exercise_does_not_affect_other_exercises(self) -> None:
        td = _make_day()
        ex_a = td.add_exercise("ex-A")
        td.add_exercise("ex-B")
        td.pull_events()
        td.remove_exercise(ex_a.id)
        remaining = td.exercises
        assert len(remaining) == 1
        assert remaining[0].exercise_id == "ex-B"


# ---------------------------------------------------------------------------
# reorder_exercises
# ---------------------------------------------------------------------------

class TestReorderExercises:
    def test_reorder_exercises_updates_order_fields(self) -> None:
        td = _make_day()
        ex_a = td.add_exercise("ex-A")
        ex_b = td.add_exercise("ex-B")
        td.reorder_exercises([ex_b.id, ex_a.id])
        ordered = td.exercises
        assert ordered[0].id == ex_b.id
        assert ordered[1].id == ex_a.id

    def test_reorder_exercises_same_order_is_noop(self) -> None:
        td = _make_day()
        ex_a = td.add_exercise("ex-A")
        ex_b = td.add_exercise("ex-B")
        td.reorder_exercises([ex_a.id, ex_b.id])
        ordered = td.exercises
        assert ordered[0].id == ex_a.id
        assert ordered[1].id == ex_b.id

    def test_reorder_exercises_raises_on_missing_id(self) -> None:
        td = _make_day()
        ex_a = td.add_exercise("ex-A")
        td.add_exercise("ex-B")
        with pytest.raises(ReorderMismatchError):
            td.reorder_exercises([ex_a.id])  # missing ex_b.id

    def test_reorder_exercises_raises_on_extra_id(self) -> None:
        td = _make_day()
        ex_a = td.add_exercise("ex-A")
        with pytest.raises(ReorderMismatchError):
            td.reorder_exercises([ex_a.id, WorkoutExerciseId.generate()])

    def test_reorder_exercises_raises_on_empty_list_when_exercises_exist(self) -> None:
        td = _make_day()
        td.add_exercise("ex-A")
        with pytest.raises(ReorderMismatchError):
            td.reorder_exercises([])

    def test_reorder_exercises_allows_empty_list_when_day_is_empty(self) -> None:
        td = _make_day()
        td.reorder_exercises([])  # should not raise
        assert td.exercises == []
