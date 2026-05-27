"""Tests for WorkoutExercise entity — RED phase."""
import pytest

from backend.src.domain.value_objects import DayOfWeek, WorkoutExerciseId, WorkoutId
from backend.src.domain.entities.workout_exercise import WorkoutExercise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_exercise(
    *,
    ex_id: WorkoutExerciseId | None = None,
    workout_id: WorkoutId | None = None,
    day: DayOfWeek = DayOfWeek.MONDAY,
    exercise_id: str = "exercise-abc",
    order: int = 1,
) -> WorkoutExercise:
    return WorkoutExercise(
        id=ex_id or WorkoutExerciseId.generate(),
        workout_id=workout_id or WorkoutId.generate(),
        day=day,
        exercise_id=exercise_id,
        order=order,
    )


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------

class TestWorkoutExerciseCreation:
    def test_workout_exercise_creation_stores_all_fields(self) -> None:
        ex_id = WorkoutExerciseId.generate()
        w_id = WorkoutId.generate()
        exercise = WorkoutExercise(
            id=ex_id,
            workout_id=w_id,
            day=DayOfWeek.TUESDAY,
            exercise_id="ex-001",
            order=3,
        )
        assert exercise.id == ex_id
        assert exercise.workout_id == w_id
        assert exercise.day == DayOfWeek.TUESDAY
        assert exercise.exercise_id == "ex-001"
        assert exercise.order == 3

    def test_workout_exercise_uses_workout_exercise_id_vo(self) -> None:
        ex_id = WorkoutExerciseId.generate()
        exercise = _make_exercise(ex_id=ex_id)
        assert isinstance(exercise.id, WorkoutExerciseId)

    def test_workout_exercise_uses_workout_id_vo(self) -> None:
        w_id = WorkoutId.generate()
        exercise = _make_exercise(workout_id=w_id)
        assert isinstance(exercise.workout_id, WorkoutId)

    def test_workout_exercise_uses_day_of_week_vo(self) -> None:
        exercise = _make_exercise(day=DayOfWeek.FRIDAY)
        assert isinstance(exercise.day, DayOfWeek)
        assert exercise.day == DayOfWeek.FRIDAY


# ---------------------------------------------------------------------------
# Equality
# ---------------------------------------------------------------------------

class TestWorkoutExerciseEquality:
    def test_workout_exercise_equality_by_id(self) -> None:
        shared_id = WorkoutExerciseId.generate()
        e1 = _make_exercise(ex_id=shared_id, exercise_id="ex-A", order=1)
        e2 = _make_exercise(ex_id=shared_id, exercise_id="ex-B", order=2)
        assert e1 == e2

    def test_workout_exercise_inequality_different_id(self) -> None:
        e1 = _make_exercise(exercise_id="ex-A")
        e2 = _make_exercise(exercise_id="ex-A")
        assert e1 != e2

    def test_workout_exercise_not_equal_to_other_type(self) -> None:
        exercise = _make_exercise()
        assert exercise != "not-an-exercise"
        assert exercise != 42


# ---------------------------------------------------------------------------
# Hash
# ---------------------------------------------------------------------------

class TestWorkoutExerciseHash:
    def test_workout_exercise_hash_consistent_with_equality(self) -> None:
        shared_id = WorkoutExerciseId.generate()
        e1 = _make_exercise(ex_id=shared_id)
        e2 = _make_exercise(ex_id=shared_id)
        assert hash(e1) == hash(e2)

    def test_workout_exercise_in_set_deduplication(self) -> None:
        shared_id = WorkoutExerciseId.generate()
        e1 = _make_exercise(ex_id=shared_id, order=1)
        e2 = _make_exercise(ex_id=shared_id, order=2)
        result = {e1, e2}
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Mutability
# ---------------------------------------------------------------------------

class TestWorkoutExerciseMutability:
    def test_workout_exercise_order_is_mutable(self) -> None:
        exercise = _make_exercise(order=1)
        exercise.order = 5
        assert exercise.order == 5
