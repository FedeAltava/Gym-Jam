"""DeleteExerciseLog use case — application layer."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import DeleteExerciseLogCommand
from backend.src.application.errors import (
    ApplicationError,
    LogNotFoundError,
    SessionNotFoundError,
    UnauthorizedError,
)
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.value_objects.exercise_log_id import ExerciseLogId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


class DeleteExerciseLogUseCase:
    def __init__(self, session_repo: SessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(self, cmd: DeleteExerciseLogCommand) -> Result[None, ApplicationError]:
        # 1. Load session
        session_id_result = WorkoutSessionId.from_string(cmd.session_id)
        if isinstance(session_id_result, Failure):
            return Failure(SessionNotFoundError(session_id=cmd.session_id))
        session = await self._session_repo.get_by_id(session_id_result.unwrap())
        if session is None:
            return Failure(SessionNotFoundError(session_id=cmd.session_id))

        # 2. Authorize
        if session.user_id != cmd.user_id:
            return Failure(UnauthorizedError(user_id=cmd.user_id, workout_id=str(session.workout_id.value)))

        # 3. Remove the log from the aggregate. A log belonging to another
        # session is simply absent here — same 404 as a nonexistent log.
        log_id_result = ExerciseLogId.from_string(cmd.log_id)
        if isinstance(log_id_result, Failure):
            return Failure(LogNotFoundError(log_id=cmd.log_id))
        if isinstance(session.remove_log(log_id_result.unwrap()), Failure):
            return Failure(LogNotFoundError(log_id=cmd.log_id))

        # 4. Persist (repo save diffs logs and deletes the removed row)
        await self._session_repo.save(session)
        return Success(None)
