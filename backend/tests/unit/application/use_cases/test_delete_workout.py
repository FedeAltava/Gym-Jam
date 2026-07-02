"""Tests for DeleteWorkoutUseCase."""
import pytest
from returns.result import Failure, Success

from backend.src.application.commands import DeleteWorkoutCommand
from backend.src.application.errors import UnauthorizedError, WorkoutNotFoundError
from backend.src.application.use_cases.delete_workout import DeleteWorkoutUseCase
from backend.src.domain.aggregates.workout import Workout
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout(user_id: str = "user-1", name: str = "Test Workout") -> Workout:
    return Workout.create(user_id=user_id, name=name, training_days=[]).unwrap()


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> DeleteWorkoutUseCase:
    return DeleteWorkoutUseCase(repo)


async def test_delete_existing_workout_returns_success(
    use_case: DeleteWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(user_id="user-1")
    await repo.save(workout)
    cmd = DeleteWorkoutCommand(workout_id=str(workout.id.value), user_id="user-1")
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    assert result.unwrap() is None


async def test_delete_removes_workout_from_repo(
    use_case: DeleteWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(user_id="user-1")
    await repo.save(workout)
    cmd = DeleteWorkoutCommand(workout_id=str(workout.id.value), user_id="user-1")
    await use_case.execute(cmd)
    assert await repo.get_by_id(workout.id) is None


async def test_delete_nonexistent_workout_returns_not_found(
    use_case: DeleteWorkoutUseCase,
) -> None:
    cmd = DeleteWorkoutCommand(
        workout_id="00000000-0000-0000-0000-000000000099",
        user_id="user-1",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_delete_wrong_owner_returns_unauthorized(
    use_case: DeleteWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(user_id="user-1")
    await repo.save(workout)
    cmd = DeleteWorkoutCommand(workout_id=str(workout.id.value), user_id="user-2")
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


async def test_delete_invalid_workout_id_returns_not_found(
    use_case: DeleteWorkoutUseCase,
) -> None:
    cmd = DeleteWorkoutCommand(workout_id="not-a-valid-uuid", user_id="user-1")
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)
