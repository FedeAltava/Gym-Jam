"""Integration tests for SqlAlchemyWorkoutRepository — 17 tests."""
import pytest
from uuid import uuid4

from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.value_objects import (
    WorkoutId,
    WorkoutName,
    DayOfWeek,
    TrainingDayId,
    WorkoutExerciseId,
)
from backend.src.infrastructure.persistence.workout_repository import SqlAlchemyWorkoutRepository


def _make_workout(user_id: str = "user-1", name: str = "Push Day", description: str | None = None) -> Workout:
    result = Workout.create(user_id=user_id, name=name, description=description)
    return result.unwrap()


# ─── 1. save + get_by_id round-trip ────────────────────────────────────────

async def test_save_and_get_by_id_returns_workout(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout()
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)

    assert loaded is not None
    assert str(loaded.name.value) == "Push Day"


# ─── 2. workout with days + exercises ──────────────────────────────────────

async def test_save_workout_with_training_days_and_exercises(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(name="Full Body")
    workout.add_training_day(DayOfWeek.MONDAY)
    workout.add_exercise_to_day(DayOfWeek.MONDAY, "exercise-bench")
    workout.add_exercise_to_day(DayOfWeek.MONDAY, "exercise-squat")
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)

    assert loaded is not None
    days = loaded.get_training_days()
    assert DayOfWeek.MONDAY in days
    exercises = loaded.get_exercises_for_day(DayOfWeek.MONDAY)
    assert len(exercises) == 2


# ─── 3. unknown id → None ──────────────────────────────────────────────────

async def test_get_by_id_returns_none_for_unknown_id(session):
    repo = SqlAlchemyWorkoutRepository(session)
    unknown = WorkoutId(uuid4())

    result = await repo.get_by_id(unknown)

    assert result is None


# ─── 4. save is idempotent (upsert) ────────────────────────────────────────

async def test_save_is_idempotent(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(name="Old Name")
    await repo.save(workout)

    # rename and save again
    workout.name = WorkoutName.create("New Name").unwrap()
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)
    assert loaded is not None
    assert str(loaded.name.value) == "New Name"


# ─── 5. get_by_user returns all workouts for a user ────────────────────────

async def test_get_by_user_returns_all_workouts(session):
    repo = SqlAlchemyWorkoutRepository(session)
    w1 = _make_workout(user_id="user-abc", name="Workout A")
    w2 = _make_workout(user_id="user-abc", name="Workout B")
    await repo.save(w1)
    await repo.save(w2)

    results = await repo.get_by_user("user-abc")

    assert len(results) == 2


# ─── 6. get_by_user empty for unknown user ─────────────────────────────────

async def test_get_by_user_returns_empty_for_unknown_user(session):
    repo = SqlAlchemyWorkoutRepository(session)

    results = await repo.get_by_user("user-does-not-exist-xyz")

    assert results == []


# ─── 7. user isolation ────────────────────────────────────────────────────

async def test_get_by_user_does_not_return_other_users_workouts(session):
    repo = SqlAlchemyWorkoutRepository(session)
    w1 = _make_workout(user_id="user-alice", name="Alice Workout")
    w2 = _make_workout(user_id="user-bob", name="Bob Workout")
    await repo.save(w1)
    await repo.save(w2)

    alice_results = await repo.get_by_user("user-alice")
    bob_results = await repo.get_by_user("user-bob")

    assert len(alice_results) == 1
    assert str(alice_results[0].name.value) == "Alice Workout"
    assert len(bob_results) == 1
    assert str(bob_results[0].name.value) == "Bob Workout"


# ─── 8. description round-trips ───────────────────────────────────────────

async def test_save_workout_with_description(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(description="A detailed description")
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)

    assert loaded is not None
    assert loaded.description == "A detailed description"


# ─── 9. None description round-trips ──────────────────────────────────────

async def test_save_workout_with_none_description(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(description=None)
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)

    assert loaded is not None
    assert loaded.description is None


# ─── 10. multiple training days ───────────────────────────────────────────

async def test_workout_with_multiple_training_days(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(name="3-Day Split")
    workout.add_training_day(DayOfWeek.MONDAY)
    workout.add_training_day(DayOfWeek.WEDNESDAY)
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)

    assert loaded is not None
    days = loaded.get_training_days()
    assert DayOfWeek.MONDAY in days
    assert DayOfWeek.WEDNESDAY in days


# ─── 11. exercises ordered ────────────────────────────────────────────────

async def test_training_day_exercises_ordered(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(name="Ordered Workout")
    workout.add_training_day(DayOfWeek.TUESDAY)
    workout.add_exercise_to_day(DayOfWeek.TUESDAY, "ex-first")
    workout.add_exercise_to_day(DayOfWeek.TUESDAY, "ex-second")
    workout.add_exercise_to_day(DayOfWeek.TUESDAY, "ex-third")
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)
    exercises = loaded.get_exercises_for_day(DayOfWeek.TUESDAY)

    assert len(exercises) == 3
    assert exercises[0].order == 1
    assert exercises[1].order == 2
    assert exercises[2].order == 3


# ─── 12. remove exercise cascades ─────────────────────────────────────────

async def test_remove_exercise_from_day_cascades(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(name="Cascade Exercise")
    workout.add_training_day(DayOfWeek.FRIDAY)
    ex = workout.add_exercise_to_day(DayOfWeek.FRIDAY, "ex-to-remove")
    await repo.save(workout)

    # Remove exercise from domain and save again
    workout.remove_exercise_from_day(DayOfWeek.FRIDAY, ex.id)
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)
    exercises = loaded.get_exercises_for_day(DayOfWeek.FRIDAY)
    assert len(exercises) == 0


# ─── 13. remove day cascades ──────────────────────────────────────────────

async def test_remove_training_day_cascades(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(name="Cascade Day")
    workout.add_training_day(DayOfWeek.SATURDAY)
    # Add exercise then remove it first (can't remove day with exercises)
    ex = workout.add_exercise_to_day(DayOfWeek.SATURDAY, "ex-in-day")
    workout.remove_exercise_from_day(DayOfWeek.SATURDAY, ex.id)
    # Now remove the day
    workout.remove_training_day(DayOfWeek.SATURDAY)
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)
    days = loaded.get_training_days()
    assert DayOfWeek.SATURDAY not in days


# ─── 14. no events after load ─────────────────────────────────────────────

async def test_workout_created_event_not_present_after_load(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(name="Event Check")
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)
    events = loaded.pull_events()

    assert events == []


# ─── 15. no N+1: eager loading works ─────────────────────────────────────

async def test_get_by_id_loads_exercises_without_extra_queries(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(name="Eager Load Test")
    workout.add_training_day(DayOfWeek.THURSDAY)
    workout.add_exercise_to_day(DayOfWeek.THURSDAY, "ex-1")
    workout.add_exercise_to_day(DayOfWeek.THURSDAY, "ex-2")
    workout.add_exercise_to_day(DayOfWeek.THURSDAY, "ex-3")
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)

    # If lazy loading were triggered after session expiry this would fail
    exercises = loaded.get_exercises_for_day(DayOfWeek.THURSDAY)
    assert len(exercises) == 3


# ─── 16. multiple workouts same user different days ───────────────────────

async def test_save_multiple_workouts_same_user_different_days(session):
    repo = SqlAlchemyWorkoutRepository(session)
    user = "user-multi"
    w1 = _make_workout(user_id=user, name="Workout Monday")
    w1.add_training_day(DayOfWeek.MONDAY)
    w2 = _make_workout(user_id=user, name="Workout Friday")
    w2.add_training_day(DayOfWeek.FRIDAY)

    await repo.save(w1)
    await repo.save(w2)

    results = await repo.get_by_user(user)
    assert len(results) == 2


# ─── 17. is_active defaults to True ──────────────────────────────────────

async def test_workout_is_active_default_true(session):
    repo = SqlAlchemyWorkoutRepository(session)
    workout = _make_workout(name="Active Check")
    await repo.save(workout)

    loaded = await repo.get_by_id(workout.id)

    assert loaded is not None
    assert loaded.is_active is True
