"""Tests for CreateWorkoutUseCase — TDD RED phase."""
import pytest
from returns.result import Failure, Success

from backend.src.application.commands import CreateWorkoutCommand
from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.application.errors import InvalidDayOfWeekError, InvalidWorkoutNameError
from backend.src.application.use_cases.create_workout import CreateWorkoutUseCase
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> CreateWorkoutUseCase:
    return CreateWorkoutUseCase(repo)


async def test_create_workout_success_returns_dto(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="Push Day",
        description="Chest and triceps",
        training_days=("MONDAY", "THURSDAY"),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, WorkoutWithDaysDTO)
    assert dto.name == "Push Day"
    assert dto.user_id == "user-1"
    assert len(dto.training_days) == 2


async def test_create_workout_empty_name_returns_invalid_name_error(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="",
        description=None,
        training_days=(),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidWorkoutNameError)


async def test_create_workout_whitespace_name_returns_invalid_name_error(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="   ",
        description=None,
        training_days=(),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidWorkoutNameError)


async def test_create_workout_invalid_day_string_returns_invalid_day_error(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="Push Day",
        description=None,
        training_days=("NOT_A_DAY",),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidDayOfWeekError)


async def test_create_workout_with_multiple_days_creates_training_days(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="Full Body",
        description=None,
        training_days=("MONDAY", "WEDNESDAY", "FRIDAY"),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert len(dto.training_days) == 3
    days = {td.day_of_week for td in dto.training_days}
    assert "MONDAY" in days
    assert "WEDNESDAY" in days
    assert "FRIDAY" in days


async def test_create_workout_with_no_days_creates_empty_workout(use_case: CreateWorkoutUseCase) -> None:
    cmd = CreateWorkoutCommand(
        user_id="user-1",
        name="Rest Week",
        description=None,
        training_days=(),
    )
    result = await use_case.execute(cmd)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert len(dto.training_days) == 0


# ─── Single active workout per user ─────────────────────────────────────

def _cmd(user_id: str, name: str) -> CreateWorkoutCommand:
    return CreateWorkoutCommand(user_id=user_id, name=name, description=None, training_days=())


async def test_first_workout_is_created_active(use_case: CreateWorkoutUseCase) -> None:
    result = await use_case.execute(_cmd("user-1", "First Routine"))
    assert result.unwrap().is_active is True


async def test_workout_is_created_inactive_when_user_already_has_an_active_one(
    use_case: CreateWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    first = (await use_case.execute(_cmd("user-1", "First Routine"))).unwrap()

    second = (await use_case.execute(_cmd("user-1", "Second Routine"))).unwrap()

    assert second.is_active is False
    stored = await repo.get_by_user("user-1")
    assert [w.name.value for w in stored if w.is_active] == [first.name]


async def test_workout_is_created_active_when_existing_ones_are_inactive(
    use_case: CreateWorkoutUseCase, repo: InMemoryWorkoutRepository
) -> None:
    await use_case.execute(_cmd("user-1", "Old Routine"))
    for w in await repo.get_by_user("user-1"):
        w.deactivate()

    result = await use_case.execute(_cmd("user-1", "New Routine"))

    assert result.unwrap().is_active is True


async def test_other_users_active_workout_does_not_affect_creation(use_case: CreateWorkoutUseCase) -> None:
    await use_case.execute(_cmd("user-2", "Their Routine"))

    result = await use_case.execute(_cmd("user-1", "My Routine"))

    assert result.unwrap().is_active is True
