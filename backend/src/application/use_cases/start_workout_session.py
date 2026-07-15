"""StartWorkoutSession use case — application layer."""
from __future__ import annotations

from datetime import UTC, datetime

from returns.result import Failure, Result, Success

from backend.src.application.commands import StartWorkoutSessionCommand
from backend.src.application.dtos import WorkoutSessionDTO
from backend.src.application.errors import (
    ApplicationError,
    SessionAlreadyInProgressError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import TrainingDayId, WorkoutId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


class StartWorkoutSessionUseCase:
    def __init__(self, workout_repo: WorkoutRepository, session_repo: SessionRepository) -> None:
        self._workout_repo = workout_repo
        self._session_repo = session_repo

    async def execute(self, cmd: StartWorkoutSessionCommand) -> Result[WorkoutSessionDTO, ApplicationError]:
        # 1. Load workout
        id_result = WorkoutId.from_string(cmd.workout_id)
        if isinstance(id_result, Failure):
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))
        workout_id = id_result.unwrap()
        workout = await self._workout_repo.get_by_id(workout_id)
        if workout is None:
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))

        # 2. Authorize
        if workout.user_id != cmd.user_id:
            return Failure(UnauthorizedError(user_id=cmd.user_id, workout_id=cmd.workout_id))

        # 3. Validate training_day_id belongs to workout
        td_id_result = TrainingDayId.from_string(cmd.training_day_id)
        if isinstance(td_id_result, Failure):
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))
        training_day_id = td_id_result.unwrap()

        # Find matching training day by id
        matching_day = None
        for td in workout.get_training_days().values():
            if td.id == training_day_id:
                matching_day = td
                break

        if matching_day is None:
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))

        # 3b. Reject a second concurrent session for the same day. Two tabs
        # would otherwise both create zombie in-progress sessions.
        existing = await self._session_repo.get_in_progress_for_day(
            cmd.user_id, training_day_id
        )
        if existing is not None:
            return Failure(SessionAlreadyInProgressError(training_day_id=cmd.training_day_id))

        # 4. Create session
        session = WorkoutSession(
            id=WorkoutSessionId.generate(),
            user_id=cmd.user_id,
            workout_id=workout_id,
            training_day_id=training_day_id,
            started_at=datetime.now(UTC),
            completed_at=None,
            _logs=[],
        )

        # 5. Save and return
        await self._session_repo.save(session)
        return Success(WorkoutSessionDTO.from_aggregate(session))
