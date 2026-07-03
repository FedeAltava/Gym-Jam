"""Tests for RenameWorkoutUseCase."""
import pytest
from returns.result import Failure, Success

from backend.src.application.commands import RenameWorkoutCommand
from backend.src.application.errors import DomainViolationError, UnauthorizedError, WorkoutNotFoundError
from backend.src.application.use_cases.rename_workout import RenameWorkoutUseCase
from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.domain.aggregates.workout import Workout
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout(user_id: str = "user-1", name: str = "Push Day") -> Workout:
    return Workout.create(user_id=user_id, name=name, training_days=[]).unwrap()


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> RenameWorkoutUseCase:
    return RenameWorkoutUseCase(repo)


async def test_rename_workout_happy_path_returns_dto_with_new_name(
    use_case: RenameWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(user_id="user-1", name="Push Day")
    await repo.save(workout)
    cmd = RenameWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        new_name="Pull Day",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, WorkoutWithDaysDTO)
    assert dto.name == "Pull Day"


async def test_rename_workout_not_found_returns_error(
    use_case: RenameWorkoutUseCase,
) -> None:
    cmd = RenameWorkoutCommand(
        workout_id="00000000-0000-0000-0000-000000000099",
        user_id="user-1",
        new_name="New Name",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_rename_workout_invalid_id_returns_not_found(
    use_case: RenameWorkoutUseCase,
) -> None:
    cmd = RenameWorkoutCommand(
        workout_id="not-a-valid-uuid",
        user_id="user-1",
        new_name="New Name",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), WorkoutNotFoundError)


async def test_rename_workout_wrong_owner_returns_unauthorized(
    use_case: RenameWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(user_id="user-1", name="Push Day")
    await repo.save(workout)
    cmd = RenameWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-2",
        new_name="New Name",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), UnauthorizedError)


async def test_rename_workout_empty_name_returns_domain_violation(
    use_case: RenameWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    workout = _make_workout(user_id="user-1", name="Push Day")
    await repo.save(workout)
    cmd = RenameWorkoutCommand(
        workout_id=str(workout.id.value),
        user_id="user-1",
        new_name="",
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
