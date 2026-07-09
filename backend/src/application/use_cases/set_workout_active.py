"""SetWorkoutActiveUseCase — activate or deactivate a workout."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import SetWorkoutActiveCommand
from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.application.errors import ApplicationError, UnauthorizedError, WorkoutNotFoundError
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutId


class SetWorkoutActiveUseCase:
    def __init__(self, repo: WorkoutRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: SetWorkoutActiveCommand) -> Result[WorkoutWithDaysDTO, ApplicationError]:
        id_result = WorkoutId.from_string(cmd.workout_id)
        if isinstance(id_result, Failure):
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))
        workout_id = id_result.unwrap()

        workout = await self._repo.get_by_id(workout_id)
        if workout is None:
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))

        if workout.user_id != cmd.user_id:
            return Failure(UnauthorizedError(user_id=cmd.user_id, workout_id=cmd.workout_id))

        if cmd.is_active:
            workout.activate()
        else:
            workout.deactivate()

        await self._repo.save(workout)
        return Success(WorkoutWithDaysDTO.from_aggregate(workout))
