"""SwapSessionExercise use case — application layer."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import SwapSessionExerciseCommand
from backend.src.application.dtos import WorkoutSessionDTO
from backend.src.application.errors import (
    ApplicationError,
    DomainViolationError,
    ExerciseHasLoggedSetsError,
    ExerciseNotFoundError,
    SessionAlreadyCompletedError,
    SessionNotFoundError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.domain.errors.base import SessionError
from backend.src.domain.errors.session_errors import (
    ExerciseHasLoggedSets,
    SessionAlreadyCompleted,
)
from backend.src.domain.repositories.exercise_repository import ExerciseRepository
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutExerciseId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


class SwapSessionExerciseUseCase:
    """Replace a planned exercise with a catalog exercise for one session only.

    The routine plan is untouched: logs keep pointing at the planned slot and
    the session records which catalog exercise was done instead.
    """

    def __init__(
        self,
        workout_repo: WorkoutRepository,
        session_repo: SessionRepository,
        exercise_repo: ExerciseRepository,
    ) -> None:
        self._workout_repo = workout_repo
        self._session_repo = session_repo
        self._exercise_repo = exercise_repo

    async def execute(self, cmd: SwapSessionExerciseCommand) -> Result[WorkoutSessionDTO, ApplicationError]:
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

        # 3. Find the planned slot, scoped to the session's own training day
        workout = await self._workout_repo.get_by_id(session.workout_id)
        if workout is None:
            return Failure(WorkoutNotFoundError(workout_id=str(session.workout_id.value)))
        ex_id_result = WorkoutExerciseId.from_string(cmd.workout_exercise_id)
        if isinstance(ex_id_result, Failure):
            return Failure(WorkoutNotFoundError(workout_id=str(session.workout_id.value)))
        exercise = workout.find_exercise_in_day(session.training_day_id, ex_id_result.unwrap())
        if exercise is None:
            return Failure(WorkoutNotFoundError(workout_id=str(session.workout_id.value)))

        # 4. Undo swaps back to the planned exercise; otherwise the substitute
        # must exist in the catalog.
        target_id = cmd.exercise_id if cmd.exercise_id is not None else exercise.exercise_id
        if target_id != exercise.exercise_id and not await self._exercise_repo.exists(target_id):
            return Failure(ExerciseNotFoundError(exercise_id=target_id))

        # 5. Delegate to domain
        try:
            session.swap_exercise(exercise, target_id)
        except SessionAlreadyCompleted:
            return Failure(SessionAlreadyCompletedError(session_id=cmd.session_id))
        except ExerciseHasLoggedSets:
            return Failure(ExerciseHasLoggedSetsError(workout_exercise_id=cmd.workout_exercise_id))
        except SessionError as e:
            return Failure(DomainViolationError(domain_error=e, message=str(e)))

        # 6. Save and return
        await self._session_repo.save(session)
        return Success(WorkoutSessionDTO.from_aggregate(session))
