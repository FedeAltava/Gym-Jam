"""DeleteWorkoutSession use case — application layer."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import DeleteWorkoutSessionCommand
from backend.src.application.errors import (
    ApplicationError,
    SessionNotFoundError,
    UnauthorizedError,
)
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


class DeleteWorkoutSessionUseCase:
    def __init__(self, session_repo: SessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(self, cmd: DeleteWorkoutSessionCommand) -> Result[None, ApplicationError]:
        # 1. Load session
        session_id_result = WorkoutSessionId.from_string(cmd.session_id)
        if isinstance(session_id_result, Failure):
            return Failure(SessionNotFoundError(session_id=cmd.session_id))
        session_id = session_id_result.unwrap()
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            return Failure(SessionNotFoundError(session_id=cmd.session_id))

        # 2. Authorize
        if session.user_id != cmd.user_id:
            return Failure(UnauthorizedError(user_id=cmd.user_id, workout_id=str(session.workout_id.value)))

        # 3. Delete (logs cascade at ORM and DB level)
        await self._session_repo.delete(session.id)
        return Success(None)
