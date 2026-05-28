"""GetWorkoutWithDaysUseCase — application layer."""
from returns.result import Failure, Result, Success

from backend.src.application.commands import GetWorkoutWithDaysQuery
from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.application.errors import (
    ApplicationError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutId


class GetWorkoutWithDaysUseCase:
    def __init__(self, repo: WorkoutRepository) -> None:
        self._repo = repo

    def execute(self, query: GetWorkoutWithDaysQuery) -> Result[WorkoutWithDaysDTO, ApplicationError]:
        # 1. Load workout
        workout_id = WorkoutId.from_string(query.workout_id).unwrap()
        workout = self._repo.get_by_id(workout_id)
        if workout is None:
            return Failure(WorkoutNotFoundError(workout_id=query.workout_id))

        # 2. Authorize
        if workout.user_id != query.user_id:
            return Failure(UnauthorizedError(user_id=query.user_id, workout_id=query.workout_id))

        # 3. Return DTO (no mutation, no save)
        return Success(WorkoutWithDaysDTO.from_aggregate(workout))
