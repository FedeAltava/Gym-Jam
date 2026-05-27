"""Cross-VO identity safety tests — FASE 1."""
import uuid

from backend.src.domain.value_objects.workout_exercise_id import WorkoutExerciseId
from backend.src.domain.value_objects.workout_id import WorkoutId


def test_two_generated_workout_ids_are_different() -> None:
    id1 = WorkoutId.generate()
    id2 = WorkoutId.generate()
    assert id1 != id2


def test_workout_id_and_exercise_id_same_uuid_are_not_equal() -> None:
    shared = uuid.uuid4()
    wid = WorkoutId(value=shared)
    eid = WorkoutExerciseId(value=shared)
    assert wid != eid
