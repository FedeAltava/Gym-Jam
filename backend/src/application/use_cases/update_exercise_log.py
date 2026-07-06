"""UpdateExerciseLog use case — application layer."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import UpdateExerciseLogCommand
from backend.src.application.dtos import ExerciseLogDTO
from backend.src.application.errors import (
    ApplicationError,
    LogNotFoundError,
    SessionNotFoundError,
    UnauthorizedError,
)
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.value_objects.exercise_log_id import ExerciseLogId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


class UpdateExerciseLogUseCase:
    def __init__(self, session_repo: SessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(self, cmd: UpdateExerciseLogCommand) -> Result[ExerciseLogDTO, ApplicationError]:
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

        # 3. Find log within the session
        log_id_result = ExerciseLogId.from_string(cmd.log_id)
        if isinstance(log_id_result, Failure):
            return Failure(LogNotFoundError(log_id=cmd.log_id))
        log_id = log_id_result.unwrap()

        log = next((entry for entry in session.logs if entry.id == log_id), None)
        if log is None:
            return Failure(LogNotFoundError(log_id=cmd.log_id))

        # 4. Update fields (partial update — only fields present in the request).
        # fields_set distinguishes "omitted" from "sent as null": an explicit
        # null weight_kg clears the weight (e.g. bodyweight exercise logged
        # with weight by mistake). reps_completed cannot be null.
        if "reps_completed" in cmd.fields_set and cmd.reps_completed is not None:
            log.reps_completed = cmd.reps_completed
        if "weight_kg" in cmd.fields_set:
            log.weight_kg = cmd.weight_kg

        # 5. Persist
        await self._session_repo.save(session)
        return Success(ExerciseLogDTO.from_entity(log))
