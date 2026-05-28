"""GetWorkoutsByUserUseCase — application layer."""
from dataclasses import dataclass

from returns.result import Result, Success

from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.application.errors import ApplicationError
from backend.src.domain.repositories.workout_repository import WorkoutRepository


@dataclass(frozen=True)
class GetWorkoutsByUserQuery:
    user_id: str


class GetWorkoutsByUserUseCase:
    def __init__(self, repo: WorkoutRepository) -> None:
        self._repo = repo

    async def execute(self, query: GetWorkoutsByUserQuery) -> Result[list[WorkoutWithDaysDTO], ApplicationError]:
        workouts = await self._repo.get_by_user(query.user_id)
        dtos = [WorkoutWithDaysDTO.from_workout(w) for w in workouts]
        return Success(dtos)
