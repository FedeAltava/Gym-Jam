"""Unit tests for WorkoutSession aggregate root — log_set() and complete()."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.src.domain.entities.exercise_log import ExerciseLog
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.errors.session_errors import (
    InvalidRepsCompleted,
    SessionAlreadyCompleted,
    SetAlreadyLogged,
    SetExceedsPlan,
)
from backend.src.domain.value_objects import (
    DayOfWeek,
    TrainingDayId,
    WorkoutExerciseId,
    WorkoutId,
    WorkoutSessionId,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_exercise(
    *,
    sets: int = 3,
    reps_per_set: int = 10,
    weight_kg: float | None = None,
    exercise_id: str = "bench-press",
) -> WorkoutExercise:
    return WorkoutExercise(
        id=WorkoutExerciseId.generate(),
        workout_id=WorkoutId.generate(),
        day=DayOfWeek.MONDAY,
        exercise_id=exercise_id,
        order=1,
        sets=sets,
        reps_per_set=reps_per_set,
        weight_kg=weight_kg,
    )


def _make_session(*, completed_at: datetime | None = None) -> WorkoutSession:
    return WorkoutSession(
        id=WorkoutSessionId.generate(),
        user_id="user-123",
        workout_id=WorkoutId.generate(),
        training_day_id=TrainingDayId.generate(),
        started_at=datetime.now(UTC),
        completed_at=completed_at,
    )


# ---------------------------------------------------------------------------
# T09 — log_set() behavior
# ---------------------------------------------------------------------------


class TestLogSet:
    def test_happy_path_returns_exercise_log_with_correct_fields(self) -> None:
        session = _make_session()
        exercise = _make_exercise(sets=3)

        log = session.log_set(
            exercise=exercise,
            set_number=1,
            reps_completed=10,
            weight_kg=50.0,
        )

        assert isinstance(log, ExerciseLog)
        assert log.session_id == session.id
        assert log.workout_exercise_id == exercise.id
        assert log.set_number == 1
        assert log.reps_completed == 10
        assert log.weight_kg == 50.0

    def test_happy_path_appends_log_to_session(self) -> None:
        session = _make_session()
        exercise = _make_exercise(sets=3)

        session.log_set(exercise=exercise, set_number=1, reps_completed=8, weight_kg=None)

        assert len(session.logs) == 1

    def test_set_number_beyond_plan_raises_set_exceeds_plan(self) -> None:
        session = _make_session()
        exercise = _make_exercise(sets=3)

        # set_number > exercise.sets is now rejected (B3 fix)
        with pytest.raises(SetExceedsPlan):
            session.log_set(exercise=exercise, set_number=4, reps_completed=10, weight_kg=None)

    def test_set_number_zero_raises_set_exceeds_plan(self) -> None:
        session = _make_session()
        exercise = _make_exercise(sets=3)

        with pytest.raises(SetExceedsPlan):
            session.log_set(exercise=exercise, set_number=0, reps_completed=10, weight_kg=None)

    def test_set_number_negative_raises_set_exceeds_plan(self) -> None:
        session = _make_session()
        exercise = _make_exercise(sets=3)

        with pytest.raises(SetExceedsPlan):
            session.log_set(exercise=exercise, set_number=-1, reps_completed=10, weight_kg=None)

    def test_duplicate_exercise_set_raises_set_already_logged(self) -> None:
        session = _make_session()
        exercise = _make_exercise(sets=3)

        session.log_set(exercise=exercise, set_number=1, reps_completed=10, weight_kg=None)

        with pytest.raises(SetAlreadyLogged) as exc_info:
            session.log_set(exercise=exercise, set_number=1, reps_completed=12, weight_kg=None)

        assert exc_info.value.set_number == 1
        assert str(exercise.id.value) in exc_info.value.workout_exercise_id

    def test_reps_completed_zero_raises_invalid_reps_completed(self) -> None:
        session = _make_session()
        exercise = _make_exercise(sets=3)

        with pytest.raises(InvalidRepsCompleted) as exc_info:
            session.log_set(exercise=exercise, set_number=1, reps_completed=0, weight_kg=None)

        assert exc_info.value.reps == 0

    def test_reps_completed_negative_raises_invalid_reps_completed(self) -> None:
        session = _make_session()
        exercise = _make_exercise(sets=3)

        with pytest.raises(InvalidRepsCompleted):
            session.log_set(exercise=exercise, set_number=1, reps_completed=-5, weight_kg=None)

    def test_log_set_on_completed_session_raises_session_already_completed(self) -> None:
        completed_at = datetime.now(UTC) - timedelta(minutes=30)
        session = _make_session(completed_at=completed_at)
        exercise = _make_exercise(sets=3)

        with pytest.raises(SessionAlreadyCompleted):
            session.log_set(exercise=exercise, set_number=1, reps_completed=10, weight_kg=None)

    def test_different_exercises_can_share_same_set_number(self) -> None:
        session = _make_session()
        exercise_a = _make_exercise(sets=3, exercise_id="bench-press")
        exercise_b = _make_exercise(sets=3, exercise_id="squat")

        session.log_set(exercise=exercise_a, set_number=1, reps_completed=10, weight_kg=60.0)
        log_b = session.log_set(exercise=exercise_b, set_number=1, reps_completed=8, weight_kg=80.0)

        assert len(session.logs) == 2
        assert log_b.workout_exercise_id == exercise_b.id

    def test_log_returns_copy_of_logs_not_internal_list(self) -> None:
        session = _make_session()
        exercise = _make_exercise(sets=3)
        session.log_set(exercise=exercise, set_number=1, reps_completed=10, weight_kg=None)

        logs_copy = session.logs
        logs_copy.clear()

        assert len(session.logs) == 1


# ---------------------------------------------------------------------------
# T10 — complete() idempotency
# ---------------------------------------------------------------------------


class TestComplete:
    def test_complete_sets_completed_at(self) -> None:
        session = _make_session()
        assert session.completed_at is None

        session.complete()

        assert session.completed_at is not None
        assert session.status == "completed"

    def test_complete_twice_does_not_raise(self) -> None:
        session = _make_session()
        session.complete()
        first_completed_at = session.completed_at

        # Should not raise
        session.complete()

        assert session.completed_at == first_completed_at

    def test_complete_twice_does_not_update_completed_at(self) -> None:
        session = _make_session()
        session.complete()
        first_ts = session.completed_at

        session.complete()

        assert session.completed_at == first_ts

    def test_status_is_in_progress_before_complete(self) -> None:
        session = _make_session()
        assert session.status == "in_progress"

    def test_status_is_completed_after_complete(self) -> None:
        session = _make_session()
        session.complete()
        assert session.status == "completed"

    def test_status_is_completed_when_constructed_with_completed_at(self) -> None:
        completed_at = datetime.now(UTC) - timedelta(hours=1)
        session = _make_session(completed_at=completed_at)
        assert session.status == "completed"
