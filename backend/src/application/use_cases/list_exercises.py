"""ListExercisesUseCase — application layer."""
from returns.result import Result, Success

from backend.src.application.dtos import ExerciseDTO
from backend.src.application.errors import ApplicationError
from backend.src.domain.repositories.exercise_repository import ExerciseRepository


class ListExercisesUseCase:
    def __init__(self, exercise_repo: ExerciseRepository) -> None:
        self._exercise_repo = exercise_repo

    async def execute(self) -> Result[list[ExerciseDTO], ApplicationError]:
        exercises = await self._exercise_repo.get_all()
        ordered = sorted(exercises, key=lambda e: (e.muscle_group, e.name))
        return Success([ExerciseDTO.from_entity(e) for e in ordered])
