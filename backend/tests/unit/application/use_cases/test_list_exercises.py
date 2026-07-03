"""Tests for ListExercisesUseCase."""
import pytest
from returns.result import Success

from backend.src.application.dtos import ExerciseDTO
from backend.src.application.use_cases.list_exercises import ListExercisesUseCase
from backend.src.domain.entities.exercise import Exercise
from backend.tests.unit.application.use_cases.in_memory_exercise_repository import (
    InMemoryExerciseRepository,
)


@pytest.fixture
def exercise_repo() -> InMemoryExerciseRepository:
    return InMemoryExerciseRepository(
        [
            Exercise(id="squat", name="Sentadilla", muscle_group="Piernas"),
            Exercise(id="bench-press", name="Press de banca", muscle_group="Pecho"),
            Exercise(id="push-up", name="Flexiones", muscle_group="Pecho"),
        ]
    )


@pytest.fixture
def use_case(exercise_repo: InMemoryExerciseRepository) -> ListExercisesUseCase:
    return ListExercisesUseCase(exercise_repo)


async def test_list_exercises_returns_all_as_dtos(use_case: ListExercisesUseCase) -> None:
    result = await use_case.execute()
    assert isinstance(result, Success)
    dtos = result.unwrap()
    assert len(dtos) == 3
    assert all(isinstance(dto, ExerciseDTO) for dto in dtos)


async def test_list_exercises_ordered_by_muscle_group_then_name(
    use_case: ListExercisesUseCase,
) -> None:
    result = await use_case.execute()
    dtos = result.unwrap()
    assert [(dto.muscle_group, dto.name) for dto in dtos] == [
        ("Pecho", "Flexiones"),
        ("Pecho", "Press de banca"),
        ("Piernas", "Sentadilla"),
    ]


async def test_list_exercises_empty_catalog_returns_empty_list() -> None:
    use_case = ListExercisesUseCase(InMemoryExerciseRepository())
    result = await use_case.execute()
    assert isinstance(result, Success)
    assert result.unwrap() == []


# --- Filter tests ---


async def test_list_exercises_no_filter(use_case: ListExercisesUseCase) -> None:
    result = await use_case.execute()
    assert isinstance(result, Success)
    dtos = result.unwrap()
    assert len(dtos) == 3
    assert [(dto.muscle_group, dto.name) for dto in dtos] == [
        ("Pecho", "Flexiones"),
        ("Pecho", "Press de banca"),
        ("Piernas", "Sentadilla"),
    ]


async def test_list_exercises_filter_by_muscle_group(use_case: ListExercisesUseCase) -> None:
    result = await use_case.execute(muscle_group="Pecho")
    assert isinstance(result, Success)
    dtos = result.unwrap()
    assert len(dtos) == 2
    assert all(dto.muscle_group == "Pecho" for dto in dtos)
    assert [dto.name for dto in dtos] == ["Flexiones", "Press de banca"]


async def test_list_exercises_filter_case_insensitive(use_case: ListExercisesUseCase) -> None:
    result = await use_case.execute(muscle_group="pecho")
    assert isinstance(result, Success)
    dtos = result.unwrap()
    assert len(dtos) == 2
    assert all(dto.muscle_group == "Pecho" for dto in dtos)


async def test_list_exercises_filter_no_match(use_case: ListExercisesUseCase) -> None:
    result = await use_case.execute(muscle_group="NonExistent")
    assert isinstance(result, Success)
    assert result.unwrap() == []
