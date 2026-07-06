"""DeleteExerciseUseCase — application layer."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import DeleteExerciseCommand
from backend.src.application.errors import (
    ApplicationError,
    ExerciseInUseError,
    ExerciseNotFoundError,
    UnauthorizedError,
)
from backend.src.domain.repositories.exercise_repository import ExerciseRepository


class DeleteExerciseUseCase:
    def __init__(self, exercise_repo: ExerciseRepository) -> None:
        self._exercise_repo = exercise_repo

    async def execute(
        self, cmd: DeleteExerciseCommand
    ) -> Result[None, ApplicationError]:
        exercise = await self._exercise_repo.get_by_id(cmd.exercise_id)
        if exercise is None:
            return Failure(ExerciseNotFoundError(cmd.exercise_id))

        if exercise.owner_id != cmd.user_id:
            return Failure(UnauthorizedError(user_id=cmd.user_id, workout_id=cmd.exercise_id))

        if await self._exercise_repo.is_referenced_by_workout(cmd.exercise_id):
            return Failure(ExerciseInUseError(cmd.exercise_id))

        await self._exercise_repo.delete(cmd.exercise_id)
        return Success(None)
