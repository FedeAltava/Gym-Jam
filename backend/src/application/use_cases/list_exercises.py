"""ListExercisesUseCase — application layer."""
from returns.result import Result, Success

from backend.src.application.dtos import ExerciseDTO
from backend.src.application.errors import ApplicationError
from backend.src.domain.repositories.exercise_repository import ExerciseRepository


class ListExercisesUseCase:
    def __init__(self, exercise_repo: ExerciseRepository) -> None:
        self._exercise_repo = exercise_repo

    async def execute(
        self, muscle_group: str | None = None, user_id: str | None = None
    ) -> Result[list[ExerciseDTO], ApplicationError]:
        exercises = await self._exercise_repo.get_all(user_id=user_id)
        if muscle_group is not None:
            exercises = [
                e for e in exercises if e.muscle_group.lower() == muscle_group.lower()
            ]
        ordered = sorted(exercises, key=lambda e: (e.muscle_group, e.name))
        return Success([ExerciseDTO.from_entity(e) for e in ordered])
