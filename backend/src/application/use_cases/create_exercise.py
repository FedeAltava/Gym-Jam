"""CreateExerciseUseCase — application layer."""
from __future__ import annotations

import uuid

from returns.result import Failure, Result, Success

from backend.src.application.commands import CreateExerciseCommand
from backend.src.application.dtos import ExerciseDTO
from backend.src.application.errors import ApplicationError
from backend.src.domain.entities.exercise import Exercise
from backend.src.domain.repositories.exercise_repository import ExerciseRepository


class CreateExerciseUseCase:
    def __init__(self, exercise_repo: ExerciseRepository) -> None:
        self._exercise_repo = exercise_repo

    async def execute(
        self, cmd: CreateExerciseCommand
    ) -> Result[ExerciseDTO, ApplicationError]:
        exercise = Exercise(
            id=str(uuid.uuid4()),
            name=cmd.name.strip(),
            muscle_group=cmd.muscle_group.strip(),
            is_bodyweight=cmd.is_bodyweight,
            owner_id=cmd.user_id,
        )
        await self._exercise_repo.save(exercise)
        return Success(ExerciseDTO.from_entity(exercise))
