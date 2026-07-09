"""Tests for GetWorkoutsByUserUseCase."""
import pytest
from returns.result import Success

from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.application.commands import GetWorkoutsByUserQuery
from backend.src.application.use_cases.get_workouts_by_user import (
    GetWorkoutsByUserUseCase,
)
from backend.src.domain.aggregates.workout import Workout
from backend.tests.unit.application.use_cases.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)


def _make_workout(user_id: str = "user-1", name: str = "Test Workout") -> Workout:
    result = Workout.create(
        user_id=user_id,
        name=name,
        training_days=[],
    )
    return result.unwrap()


@pytest.fixture
def repo() -> InMemoryWorkoutRepository:
    return InMemoryWorkoutRepository()


@pytest.fixture
def use_case(repo: InMemoryWorkoutRepository) -> GetWorkoutsByUserUseCase:
    return GetWorkoutsByUserUseCase(repo)


async def test_returns_all_workouts_for_user(
    use_case: GetWorkoutsByUserUseCase, repo: InMemoryWorkoutRepository
) -> None:
    w1 = _make_workout(user_id="user-1", name="Workout A")
    w2 = _make_workout(user_id="user-1", name="Workout B")
    await repo.save(w1)
    await repo.save(w2)
    result = await use_case.execute(GetWorkoutsByUserQuery(user_id="user-1"))
    assert isinstance(result, Success)
    dtos = result.unwrap()
    assert len(dtos) == 2
    assert all(isinstance(d, WorkoutWithDaysDTO) for d in dtos)


async def test_returns_empty_list_for_unknown_user(
    use_case: GetWorkoutsByUserUseCase,
) -> None:
    result = await use_case.execute(GetWorkoutsByUserQuery(user_id="unknown-user"))
    assert isinstance(result, Success)
    assert result.unwrap() == []


async def test_returns_only_user_workouts(
    use_case: GetWorkoutsByUserUseCase, repo: InMemoryWorkoutRepository
) -> None:
    w1 = _make_workout(user_id="user-1", name="User1 Workout")
    w2 = _make_workout(user_id="user-2", name="User2 Workout")
    await repo.save(w1)
    await repo.save(w2)
    result = await use_case.execute(GetWorkoutsByUserQuery(user_id="user-1"))
    assert isinstance(result, Success)
    dtos = result.unwrap()
    assert len(dtos) == 1
    assert dtos[0].user_id == "user-1"
    assert dtos[0].name == "User1 Workout"


async def test_pagination_limit(
    use_case: GetWorkoutsByUserUseCase, repo: InMemoryWorkoutRepository
) -> None:
    for i in range(5):
        await repo.save(_make_workout(user_id="user-pg", name=f"Workout {i}"))
    result = await use_case.execute(GetWorkoutsByUserQuery(user_id="user-pg", limit=2, offset=0))
    assert isinstance(result, Success)
    assert len(result.unwrap()) == 2


async def test_pagination_offset(
    use_case: GetWorkoutsByUserUseCase, repo: InMemoryWorkoutRepository
) -> None:
    for i in range(5):
        await repo.save(_make_workout(user_id="user-off", name=f"Workout {i}"))
    result = await use_case.execute(GetWorkoutsByUserQuery(user_id="user-off", limit=10, offset=5))
    assert isinstance(result, Success)
    assert result.unwrap() == []
