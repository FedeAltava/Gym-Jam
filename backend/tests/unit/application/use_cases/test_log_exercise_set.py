"""Unit tests for LogExerciseSetUseCase."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import LogExerciseSetCommand
from backend.src.application.dtos import ExerciseLogDTO
from backend.src.application.errors import (
    SessionAlreadyCompletedError,
    SessionNotFoundError,
    SetAlreadyLoggedError,
    UnauthorizedError,
)
from backend.src.application.use_cases.log_exercise_set import LogExerciseSetUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import (
    DayOfWeek,
    TrainingDayId,
    WorkoutId,
    WorkoutSessionId,
)
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout(user_id: str = "user-1", days: list[str] | None = None) -> Workout:
    day_list = [DayOfWeek(d) for d in (days or ["MONDAY"])]
    return Workout.create(user_id=user_id, name="Test Workout", training_days=day_list).unwrap()


def _make_session(user_id: str, workout_id: WorkoutId, training_day_id: TrainingDayId) -> WorkoutSession:
    return WorkoutSession(
        id=WorkoutSessionId.generate(),
        user_id=user_id,
        workout_id=workout_id,
        training_day_id=training_day_id,
        started_at=datetime.now(UTC),
    )


@pytest.fixture
def workout_repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def use_case(workout_repo: InMemoryWorkoutRepository, session_repo: InMemorySessionRepository) -> LogExerciseSetUseCase:
    return LogExerciseSetUseCase(workout_repo, session_repo)


async def _setup_session_with_exercise(
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
    user_id: str = "user-1",
    sets: int = 3,
) -> tuple[WorkoutSession, str]:
    """Returns (session, workout_exercise_id_str)."""
    workout = _make_workout(user_id=user_id, days=["MONDAY"])
    td = list(workout.get_training_days().values())[0]
    exercise = workout.add_exercise_to_day(DayOfWeek.MONDAY, "bench-press", sets=sets)
    await workout_repo.save(workout)

    session = _make_session(user_id, workout.id, td.id)
    await session_repo.save(session)

    return session, str(exercise.id.value)


async def test_log_set_happy_path(
    use_case: LogExerciseSetUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id = await _setup_session_with_exercise(workout_repo, session_repo)

    cmd = LogExerciseSetCommand(
        user_id="user-1",
        session_id=str(session.id.value),
        workout_exercise_id=ex_id,
        set_number=1,
        reps_completed=10,
        weight_kg=50.0,
    )
    result = await use_case.execute(cmd)

    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, ExerciseLogDTO)
    assert dto.set_number == 1
    assert dto.reps_completed == 10
    assert dto.weight_kg == 50.0


async def test_log_set_no_weight(
    use_case: LogExerciseSetUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id = await _setup_session_with_exercise(workout_repo, session_repo)

    cmd = LogExerciseSetCommand(
        user_id="user-1",
        session_id=str(session.id.value),
        workout_exercise_id=ex_id,
        set_number=1,
        reps_completed=8,
        weight_kg=None,
    )
    result = await use_case.execute(cmd)

    assert isinstance(result, Success)
    assert result.unwrap().weight_kg is None


async def test_log_set_session_not_found(use_case: LogExerciseSetUseCase) -> None:
    cmd = LogExerciseSetCommand(
        user_id="user-1",
        session_id=str(WorkoutSessionId.generate().value),
        workout_exercise_id=str(WorkoutSessionId.generate().value),
        set_number=1,
        reps_completed=5,
        weight_kg=None,
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SessionNotFoundError)


async def test_log_set_invalid_session_id(use_case: LogExerciseSetUseCase) -> None:
    cmd = LogExerciseSetCommand(
        user_id="user-1",
        session_id="not-a-uuid",
        workout_exercise_id="also-not-uuid",
        set_number=1,
        reps_completed=5,
        weight_kg=None,
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SessionNotFoundError)


async def test_log_set_unauthorized(
    use_case: LogExerciseSetUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id = await _setup_session_with_exercise(workout_repo, session_repo, user_id="owner")

    cmd = LogExerciseSetCommand(
        user_id="attacker",
        session_id=str(session.id.value),
        workout_exercise_id=ex_id,
        set_number=1,
        reps_completed=5,
        weight_kg=None,
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


async def test_log_extra_set_beyond_plan_succeeds(
    use_case: LogExerciseSetUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    from returns.result import Success

    session, ex_id = await _setup_session_with_exercise(workout_repo, session_repo, sets=3)

    cmd = LogExerciseSetCommand(
        user_id="user-1",
        session_id=str(session.id.value),
        workout_exercise_id=ex_id,
        set_number=4,  # extra set beyond plan — now allowed
        reps_completed=10,
        weight_kg=80.0,
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)


async def test_log_set_duplicate(
    use_case: LogExerciseSetUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id = await _setup_session_with_exercise(workout_repo, session_repo)

    cmd = LogExerciseSetCommand(
        user_id="user-1",
        session_id=str(session.id.value),
        workout_exercise_id=ex_id,
        set_number=1,
        reps_completed=10,
        weight_kg=None,
    )
    # First log succeeds
    r1 = await use_case.execute(cmd)
    assert isinstance(r1, Success)
    # Second is duplicate — must reload session from repo
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SetAlreadyLoggedError)


async def test_log_set_on_completed_session(
    use_case: LogExerciseSetUseCase,
    workout_repo: InMemoryWorkoutRepository,
    session_repo: InMemorySessionRepository,
) -> None:
    session, ex_id = await _setup_session_with_exercise(workout_repo, session_repo)
    session.complete()
    await session_repo.save(session)

    cmd = LogExerciseSetCommand(
        user_id="user-1",
        session_id=str(session.id.value),
        workout_exercise_id=ex_id,
        set_number=1,
        reps_completed=10,
        weight_kg=None,
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SessionAlreadyCompletedError)
