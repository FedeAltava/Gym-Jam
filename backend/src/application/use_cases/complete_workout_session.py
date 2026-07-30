"""CompleteWorkoutSession use case — application layer."""
from __future__ import annotations

import logging

from returns.result import Failure, Result, Success

from backend.src.application.commands import CompleteWorkoutSessionCommand
from backend.src.application.dtos import WorkoutSessionDTO
from backend.src.application.errors import (
    ApplicationError,
    SessionNotFoundError,
    UnauthorizedError,
)
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.repositories.personal_record_repository import (
    PersonalRecordRepository,
)
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId

logger = logging.getLogger(__name__)


class CompleteWorkoutSessionUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        pr_repo: PersonalRecordRepository,
    ) -> None:
        self._session_repo = session_repo
        self._pr_repo = pr_repo

    async def execute(self, cmd: CompleteWorkoutSessionCommand) -> Result[WorkoutSessionDTO, ApplicationError]:
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

        # 3. Complete (idempotent — no-op if already completed). Capture the
        # prior state BEFORE complete() so re-completing an already-completed
        # session never re-runs PR detection (ADR 6).
        was_completed = session.status == "completed"
        session.complete()

        # 4. Save
        await self._session_repo.save(session)

        # 5. PR detection — NON-FATAL: completing the session must succeed
        # even if the PR pass fails.
        # Wrap in a savepoint so that an IntegrityError (e.g. concurrent upsert)
        # only rolls back the nested transaction and does NOT taint the outer
        # SQLAlchemy session. SQL repos override savepoint() with begin_nested();
        # in-memory repos use the default no-op context manager.
        if not was_completed:
            try:
                async with self._pr_repo.savepoint():
                    await self._detect_personal_records(session)
            except Exception:
                logger.warning(
                    "PR detection failed for session %s — session completion unaffected",
                    cmd.session_id,
                    exc_info=True,
                )

        return Success(WorkoutSessionDTO.from_aggregate(session))

    async def _detect_personal_records(self, session: WorkoutSession) -> None:
        # Bodyweight sets (weight_kg NULL) and zero-weight sets carry no PR.
        weighted_logs = [log for log in session.logs if log.weight_kg is not None and log.weight_kg > 0]
        if not weighted_logs:
            return

        # Logs reference plan rows; records are keyed by catalog exercise.
        workout_exercise_ids = list({str(log.workout_exercise_id.value) for log in weighted_logs})
        catalog_ids = await self._pr_repo.get_catalog_exercise_ids(workout_exercise_ids)

        # Reduce to the heaviest set per catalog exercise in this session.
        max_per_exercise: dict[str, float] = {}
        for log in weighted_logs:
            exercise_id = catalog_ids.get(str(log.workout_exercise_id.value))
            if exercise_id is None:
                continue
            assert log.weight_kg is not None  # filtered above
            if log.weight_kg > max_per_exercise.get(exercise_id, 0.0):
                max_per_exercise[exercise_id] = log.weight_kg
        if not max_per_exercise:
            return

        # One batch query against full prior log history (ADR 5), then upsert
        # only where this session strictly beats it (tie = no PR). A never
        # logged exercise is a PR by definition.
        previous_max = await self._pr_repo.get_previous_max_weights(
            user_id=session.user_id,
            exclude_session_id=str(session.id.value),
            exercise_ids=list(max_per_exercise),
        )
        achieved_at = session.completed_at
        assert achieved_at is not None  # complete() ran before detection
        for exercise_id, weight_kg in max_per_exercise.items():
            prior = previous_max.get(exercise_id)
            if prior is None or weight_kg > prior:
                await self._pr_repo.upsert_if_higher(
                    user_id=session.user_id,
                    exercise_id=exercise_id,
                    weight_kg=weight_kg,
                    session_id=str(session.id.value),
                    achieved_at=achieved_at,
                )
