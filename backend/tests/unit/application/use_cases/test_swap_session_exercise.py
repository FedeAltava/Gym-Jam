"""Unit tests for SwapSessionExerciseUseCase."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import SwapSessionExerciseCommand
from backend.src.application.dtos import ExerciseSwapDTO
from backend.src.application.errors import (
    ExerciseHasLoggedSetsError,
    ExerciseNotFoundError,
    SessionAlreadyCompletedError,
    SessionNotFoundError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.use_cases.swap_session_exercise import SwapSessionExerciseUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.entities.exercise import Exercise
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import DayOfWeek, WorkoutSessionId
from backend.tests.unit.application.use_cases.in_memory_exercise_repository import (
    InMemoryExerciseRepository,
)
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)

USER = "user-1"


@pytest.fixture
def workout_repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def use_case(
    workout_repo: InMemoryWorkoutRepository, session_repo: InMemorySessionRepository
) -> SwapSessionExerciseUseCase:
    exercise_repo = InMemoryExerciseRepository(
        [
            Exercise(id="bench-press", name="Press banca", muscle_group="Pecho"),
            Exercise(id="dumbbell-fly", name="Aperturas con mancuernas", muscle_group="Pecho"),
        ]
    )
    return SwapSessionExerciseUseCase(workout_repo, session_repo, exercise_repo)


async def _setup(
    workout_repo: InMemoryWorkoutRepository, session_repo: InMemorySessionRepository
) -> tuple[WorkoutSession, str, str]:
    """Returns (session, monday_workout_exercise_id, tuesday_workout_exercise_id)."""
    workout = Workout.create(
        user_id=USER, name="Torso", training_days=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY]
    ).unwrap()
    monday = workout.add_exercise_to_day(DayOfWeek.MONDAY, "bench-press", sets=3)
    tuesday = workout.add_exercise_to_day(DayOfWeek.TUESDAY, "bench-press", sets=3)
    await workout_repo.save(workout)
    session = WorkoutSession(
        id=WorkoutSessionId.generate(),
        user_id=USER,
        workout_id=workout.id,
        training_day_id=workout.get_training_days()[DayOfWeek.MONDAY].id,
        started_at=datetime.now(UTC),
    )
    await session_repo.save(session)
    return session, str(monday.id.value), str(tuesday.id.value)


def _cmd(session: WorkoutSession, workout_exercise_id: str, exercise_id: str | None, user_id: str = USER) -> SwapSessionExerciseCommand:
    return SwapSessionExerciseCommand(
        user_id=user_id,
        session_id=str(session.id.value),
        workout_exercise_id=workout_exercise_id,
        exercise_id=exercise_id,
    )


async def test_swap_returns_session_with_the_swap_and_persists_it(
    use_case: SwapSessionExerciseUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id, _ = await _setup(workout_repo, session_repo)

    result = await use_case.execute(_cmd(session, ex_id, "dumbbell-fly"))

    assert isinstance(result, Success)
    assert result.unwrap().swaps == (ExerciseSwapDTO(workout_exercise_id=ex_id, exercise_id="dumbbell-fly"),)
    stored = await session_repo.get_by_id(session.id)
    assert stored is not None
    assert {str(k.value): v for k, v in stored.swaps.items()} == {ex_id: "dumbbell-fly"}


async def test_undo_removes_the_swap(
    use_case: SwapSessionExerciseUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id, _ = await _setup(workout_repo, session_repo)
    await use_case.execute(_cmd(session, ex_id, "dumbbell-fly"))

    result = await use_case.execute(_cmd(session, ex_id, None))

    assert isinstance(result, Success)
    assert result.unwrap().swaps == ()


async def test_unknown_session_fails(use_case: SwapSessionExerciseUseCase) -> None:
    cmd = SwapSessionExerciseCommand(
        user_id=USER,
        session_id=str(WorkoutSessionId.generate().value),
        workout_exercise_id="x",
        exercise_id="dumbbell-fly",
    )

    result = await use_case.execute(cmd)

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SessionNotFoundError)


async def test_other_users_session_is_unauthorized(
    use_case: SwapSessionExerciseUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id, _ = await _setup(workout_repo, session_repo)

    result = await use_case.execute(_cmd(session, ex_id, "dumbbell-fly", user_id="user-2"))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)
    assert session.swaps == {}


async def test_exercise_from_another_day_is_rejected(
    use_case: SwapSessionExerciseUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, _, tuesday_ex_id = await _setup(workout_repo, session_repo)

    result = await use_case.execute(_cmd(session, tuesday_ex_id, "dumbbell-fly"))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)
    assert session.swaps == {}


async def test_unknown_catalog_exercise_is_rejected(
    use_case: SwapSessionExerciseUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id, _ = await _setup(workout_repo, session_repo)

    result = await use_case.execute(_cmd(session, ex_id, "no-such-exercise"))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), ExerciseNotFoundError)
    assert session.swaps == {}


async def test_completed_session_cannot_swap(
    use_case: SwapSessionExerciseUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id, _ = await _setup(workout_repo, session_repo)
    session.complete()

    result = await use_case.execute(_cmd(session, ex_id, "dumbbell-fly"))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SessionAlreadyCompletedError)


async def test_slot_with_logged_sets_cannot_swap(
    use_case: SwapSessionExerciseUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id, _ = await _setup(workout_repo, session_repo)
    workout = await workout_repo.get_by_id(session.workout_id)
    assert workout is not None
    exercise = workout.get_exercises_for_day(DayOfWeek.MONDAY)[0]
    session.log_set(exercise=exercise, set_number=1, reps_completed=10, weight_kg=60.0)

    result = await use_case.execute(_cmd(session, ex_id, "dumbbell-fly"))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), ExerciseHasLoggedSetsError)
    assert session.swaps == {}
