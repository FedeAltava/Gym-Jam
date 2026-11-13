"""Unit tests for CompleteWorkoutSessionUseCase."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import CompleteWorkoutSessionCommand
from backend.src.application.dtos import WorkoutSessionDTO
from backend.src.application.errors import SessionNotFoundError, UnauthorizedError
from backend.src.application.use_cases.complete_workout_session import CompleteWorkoutSessionUseCase
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.estimated_one_rep_max import estimated_one_rep_max
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import (
    DayOfWeek,
    TrainingDayId,
    WorkoutExerciseId,
    WorkoutId,
    WorkoutSessionId,
)
from backend.tests.unit.application.use_cases.in_memory_personal_record_repository import (
    InMemoryPersonalRecordRepository,
)
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)


def _make_session(user_id: str = "user-1") -> WorkoutSession:
    return WorkoutSession(
        id=WorkoutSessionId.generate(),
        user_id=user_id,
        workout_id=WorkoutId.generate(),
        training_day_id=TrainingDayId.generate(),
        started_at=datetime.now(UTC),
    )


def _make_exercise(session: WorkoutSession, exercise_id: str = "bench-press") -> WorkoutExercise:
    return WorkoutExercise(
        id=WorkoutExerciseId.generate(),
        workout_id=session.workout_id,
        day=DayOfWeek("MONDAY"),
        exercise_id=exercise_id,
        order=1,
    )


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def pr_repo() -> InMemoryPersonalRecordRepository:
    return InMemoryPersonalRecordRepository()


@pytest.fixture
def use_case(
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> CompleteWorkoutSessionUseCase:
    return CompleteWorkoutSessionUseCase(session_repo, pr_repo)


async def test_complete_session_happy_path(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    session = _make_session()
    await session_repo.save(session)

    cmd = CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))
    result = await use_case.execute(cmd)

    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, WorkoutSessionDTO)
    assert dto.status == "completed"
    assert dto.completed_at is not None


async def test_complete_session_idempotent(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    session = _make_session()
    await session_repo.save(session)

    cmd = CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))
    r1 = await use_case.execute(cmd)
    assert isinstance(r1, Success)
    first_completed_at = r1.unwrap().completed_at

    # Complete again — should be idempotent (completed_at unchanged)
    r2 = await use_case.execute(cmd)
    assert isinstance(r2, Success)
    assert r2.unwrap().completed_at == first_completed_at


async def test_complete_session_not_found(use_case: CompleteWorkoutSessionUseCase) -> None:
    cmd = CompleteWorkoutSessionCommand(
        user_id="user-1",
        session_id=str(WorkoutSessionId.generate().value),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SessionNotFoundError)


async def test_complete_session_invalid_id(use_case: CompleteWorkoutSessionUseCase) -> None:
    cmd = CompleteWorkoutSessionCommand(user_id="user-1", session_id="not-a-uuid")
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), SessionNotFoundError)


async def test_complete_session_unauthorized(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    session = _make_session(user_id="owner")
    await session_repo.save(session)

    cmd = CompleteWorkoutSessionCommand(user_id="attacker", session_id=str(session.id.value))
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


# ── PR detection on completion ────────────────────────────────────────────────


def _seed_logged_session(
    session_repo_store: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
    weight_kg: float | None,
    exercise_id: str = "bench-press",
    reps: int = 10,
) -> WorkoutSession:
    session = _make_session()
    exercise = _make_exercise(session, exercise_id)
    pr_repo.catalog_map[str(exercise.id.value)] = exercise_id
    session.log_set(exercise, set_number=1, reps_completed=reps, weight_kg=weight_kg)
    return session


def _complete(use_case: CompleteWorkoutSessionUseCase, session: WorkoutSession):
    return use_case.execute(
        CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))
    )


async def test_first_ever_log_creates_pr(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    session = _seed_logged_session(session_repo, pr_repo, weight_kg=60.0)
    await session_repo.save(session)

    result = await use_case.execute(
        CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))
    )

    assert isinstance(result, Success)
    assert ("user-1", "bench-press") in pr_repo.records
    record = pr_repo.records[("user-1", "bench-press")]
    assert record["weight_kg"] == 60.0
    assert record["reps"] == 10
    assert record["session_id"] == str(session.id.value)
    assert record["achieved_at"] == session.completed_at


async def test_beating_previous_best_estimate_creates_pr(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    pr_repo.history_best_estimate["bench-press"] = estimated_one_rep_max(80.0, 10)
    session = _seed_logged_session(session_repo, pr_repo, weight_kg=85.0)
    await session_repo.save(session)

    result = await use_case.execute(
        CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))
    )

    assert isinstance(result, Success)
    assert len(pr_repo.upsert_calls) == 1
    assert pr_repo.records[("user-1", "bench-press")]["weight_kg"] == 85.0


async def test_more_reps_at_the_same_weight_is_a_pr(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    # Previous best 80 × 8 ≈ 101 kg; now 80 × 12 = 112 kg → record.
    pr_repo.history_best_estimate["bench-press"] = estimated_one_rep_max(80.0, 8)
    session = _seed_logged_session(session_repo, pr_repo, weight_kg=80.0, reps=12)
    await session_repo.save(session)

    result = await _complete(use_case, session)

    assert isinstance(result, Success)
    assert len(pr_repo.upsert_calls) == 1
    record = pr_repo.records[("user-1", "bench-press")]
    assert record["weight_kg"] == 80.0
    assert record["reps"] == 12
    assert record["session_id"] == str(session.id.value)


async def test_heavier_with_far_fewer_reps_is_not_a_pr(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    # Previous best 80 × 10 ≈ 107 kg; now 82.5 × 3 ≈ 91 kg → no record.
    pr_repo.history_best_estimate["bench-press"] = estimated_one_rep_max(80.0, 10)
    session = _seed_logged_session(session_repo, pr_repo, weight_kg=82.5, reps=3)
    await session_repo.save(session)

    result = await _complete(use_case, session)

    assert isinstance(result, Success)
    assert pr_repo.upsert_calls == []
    assert ("user-1", "bench-press") not in pr_repo.records


async def test_best_set_of_the_session_by_estimate_is_stored_with_its_reps(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    # 85 × 5 ≈ 99 kg is the heaviest set, but 80 × 10 ≈ 107 kg is the best estimate.
    session = _make_session()
    exercise = _make_exercise(session, "bench-press")
    pr_repo.catalog_map[str(exercise.id.value)] = "bench-press"
    session.log_set(exercise, set_number=1, reps_completed=5, weight_kg=85.0)
    session.log_set(exercise, set_number=2, reps_completed=10, weight_kg=80.0)
    session.log_set(exercise, set_number=3, reps_completed=8, weight_kg=80.0)
    await session_repo.save(session)

    result = await _complete(use_case, session)

    assert isinstance(result, Success)
    assert len(pr_repo.upsert_calls) == 1
    record = pr_repo.records[("user-1", "bench-press")]
    assert record["weight_kg"] == 80.0
    assert record["reps"] == 10
    assert record["session_id"] == str(session.id.value)


async def test_tie_with_previous_best_estimate_is_not_a_pr(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    pr_repo.history_best_estimate["bench-press"] = estimated_one_rep_max(80.0, 10)
    session = _seed_logged_session(session_repo, pr_repo, weight_kg=80.0, reps=10)
    await session_repo.save(session)

    result = await use_case.execute(
        CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))
    )

    assert isinstance(result, Success)
    assert pr_repo.upsert_calls == []


async def test_null_weight_logs_are_skipped(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    session = _seed_logged_session(session_repo, pr_repo, weight_kg=None)
    await session_repo.save(session)

    result = await use_case.execute(
        CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))
    )

    assert isinstance(result, Success)
    assert pr_repo.upsert_calls == []


async def test_recompleting_completed_session_skips_detection(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    session = _seed_logged_session(session_repo, pr_repo, weight_kg=100.0)
    await session_repo.save(session)
    cmd = CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))

    r1 = await use_case.execute(cmd)
    r2 = await use_case.execute(cmd)

    assert isinstance(r1, Success)
    assert isinstance(r2, Success)
    # Detection ran exactly once — the idempotent re-complete never re-awards.
    assert len(pr_repo.upsert_calls) == 1


async def test_pr_detection_failure_does_not_break_completion(
    use_case: CompleteWorkoutSessionUseCase,
    session_repo: InMemorySessionRepository,
    pr_repo: InMemoryPersonalRecordRepository,
) -> None:
    session = _seed_logged_session(session_repo, pr_repo, weight_kg=90.0)
    await session_repo.save(session)
    pr_repo.raise_always = True

    result = await use_case.execute(
        CompleteWorkoutSessionCommand(user_id="user-1", session_id=str(session.id.value))
    )

    assert isinstance(result, Success)
    assert result.unwrap().status == "completed"
