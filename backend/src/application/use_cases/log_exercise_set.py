"""LogExerciseSet use case — application layer."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import LogExerciseSetCommand
from backend.src.application.dtos import ExerciseLogDTO
from backend.src.application.errors import (
    ApplicationError,
    DomainViolationError,
    SessionAlreadyCompletedError,
    SessionNotFoundError,
    SetAlreadyLoggedError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.domain.errors.session_errors import (
    SessionAlreadyCompleted,
    SessionError,
    SetAlreadyLogged,
)
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutExerciseId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


class LogExerciseSetUseCase:
    def __init__(self, workout_repo: WorkoutRepository, session_repo: SessionRepository) -> None:
        self._workout_repo = workout_repo
        self._session_repo = session_repo

    async def execute(self, cmd: LogExerciseSetCommand) -> Result[ExerciseLogDTO, ApplicationError]:
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

        # 3. Load workout to get exercise
        workout = await self._workout_repo.get_by_id(session.workout_id)
        if workout is None:
            return Failure(WorkoutNotFoundError(workout_id=str(session.workout_id.value)))

        # 4. Find workout exercise by id
        ex_id_result = WorkoutExerciseId.from_string(cmd.workout_exercise_id)
        if isinstance(ex_id_result, Failure):
            return Failure(WorkoutNotFoundError(workout_id=str(session.workout_id.value)))
        exercise_id = ex_id_result.unwrap()

        exercise = None
        for td in workout.get_training_days().values():
            for ex in td.exercises:
                if ex.id == exercise_id:
                    exercise = ex
                    break
            if exercise is not None:
                break

        if exercise is None:
            return Failure(WorkoutNotFoundError(workout_id=str(session.workout_id.value)))

        # 5. Delegate to domain — let domain errors propagate as ApplicationError
        try:
            log = session.log_set(
                exercise=exercise,
                set_number=cmd.set_number,
                reps_completed=cmd.reps_completed,
                weight_kg=cmd.weight_kg,
            )
        except SetAlreadyLogged as e:
            return Failure(SetAlreadyLoggedError(workout_exercise_id=cmd.workout_exercise_id, set_number=cmd.set_number))
        except SessionAlreadyCompleted as e:
            return Failure(SessionAlreadyCompletedError(session_id=cmd.session_id))
        except SessionError as e:
            return Failure(DomainViolationError(domain_error=e, message=str(e)))

        # 6. Save and return
        await self._session_repo.save(session)
        return Success(ExerciseLogDTO.from_entity(log))
