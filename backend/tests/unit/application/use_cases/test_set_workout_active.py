"""Tests for SetWorkoutActiveUseCase — single active workout per user."""
import pytest
from returns.result import Failure, Success

from backend.src.application.commands import SetWorkoutActiveCommand
from backend.src.application.errors import UnauthorizedError, WorkoutNotFoundError
from backend.src.application.use_cases.set_workout_active import SetWorkoutActiveUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> SetWorkoutActiveUseCase:
    return SetWorkoutActiveUseCase(repo)


async def _seed(repo: InMemoryWorkoutRepository, user_id: str, name: str, active: bool) -> Workout:
    workout = Workout.create(user_id=user_id, name=name).unwrap()
    if not active:
        workout.deactivate()
    await repo.save(workout)
    return workout


def _cmd(workout: Workout, user_id: str, is_active: bool) -> SetWorkoutActiveCommand:
    return SetWorkoutActiveCommand(workout_id=str(workout.id.value), user_id=user_id, is_active=is_active)


async def test_activate_deactivates_other_workouts_of_same_user(
    use_case: SetWorkoutActiveUseCase, repo: InMemoryWorkoutRepository
) -> None:
    a = await _seed(repo, "user-1", "Routine A", active=True)
    b = await _seed(repo, "user-1", "Routine B", active=True)
    c = await _seed(repo, "user-1", "Routine C", active=False)

    result = await use_case.execute(_cmd(c, "user-1", True))

    assert isinstance(result, Success)
    assert result.unwrap().is_active is True
    active = [w for w in await repo.get_by_user("user-1") if w.is_active]
    assert [w.id for w in active] == [c.id]
    assert (await repo.get_by_id(a.id)).is_active is False
    assert (await repo.get_by_id(b.id)).is_active is False


async def test_activate_does_not_touch_other_users(
    use_case: SetWorkoutActiveUseCase, repo: InMemoryWorkoutRepository
) -> None:
    mine = await _seed(repo, "user-1", "Mine", active=False)
    theirs = await _seed(repo, "user-2", "Theirs", active=True)

    await use_case.execute(_cmd(mine, "user-1", True))

    assert (await repo.get_by_id(theirs.id)).is_active is True


async def test_deactivate_does_not_touch_other_workouts(
    use_case: SetWorkoutActiveUseCase, repo: InMemoryWorkoutRepository
) -> None:
    a = await _seed(repo, "user-1", "Routine A", active=True)
    b = await _seed(repo, "user-1", "Routine B", active=True)

    result = await use_case.execute(_cmd(a, "user-1", False))

    assert isinstance(result, Success)
    assert (await repo.get_by_id(a.id)).is_active is False
    assert (await repo.get_by_id(b.id)).is_active is True


async def test_activate_unknown_workout_returns_not_found(use_case: SetWorkoutActiveUseCase) -> None:
    cmd = SetWorkoutActiveCommand(
        workout_id="00000000-0000-0000-0000-000000000999", user_id="user-1", is_active=True
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_activate_foreign_workout_is_unauthorized_and_changes_nothing(
    use_case: SetWorkoutActiveUseCase, repo: InMemoryWorkoutRepository
) -> None:
    mine = await _seed(repo, "user-1", "Mine", active=True)
    theirs = await _seed(repo, "user-2", "Theirs", active=False)

    result = await use_case.execute(_cmd(theirs, "user-1", True))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)
    assert (await repo.get_by_id(mine.id)).is_active is True
    assert (await repo.get_by_id(theirs.id)).is_active is False
