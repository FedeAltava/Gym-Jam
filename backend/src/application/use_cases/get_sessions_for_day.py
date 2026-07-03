"""GetSessionsForDay use case — application layer."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import GetSessionsForDayCommand
from backend.src.application.dtos import WorkoutSessionDTO
from backend.src.application.errors import ApplicationError, WorkoutNotFoundError
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.value_objects import TrainingDayId, WorkoutId


class GetSessionsForDayUseCase:
    def __init__(self, session_repo: SessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(
        self, cmd: GetSessionsForDayCommand
    ) -> Result[list[WorkoutSessionDTO], ApplicationError]:
        # Parse workout_id
        wid_result = WorkoutId.from_string(cmd.workout_id)
        if isinstance(wid_result, Failure):
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))
        workout_id = wid_result.unwrap()

        # Parse training_day_id
        td_id_result = TrainingDayId.from_string(cmd.training_day_id)
        if isinstance(td_id_result, Failure):
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))
        training_day_id = td_id_result.unwrap()

        sessions = await self._session_repo.get_sessions_for_day(
            cmd.user_id, workout_id, training_day_id
        )
        return Success([WorkoutSessionDTO.from_aggregate(s) for s in sessions])
