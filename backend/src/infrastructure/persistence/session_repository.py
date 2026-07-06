"""SqlAlchemySessionRepository — infrastructure layer."""
from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.value_objects import TrainingDayId, WorkoutId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId
from backend.src.infrastructure.persistence.mappers import WorkoutSessionMapper
from backend.src.infrastructure.persistence.models import WorkoutLogModel, WorkoutSessionModel


class SqlAlchemySessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, session: WorkoutSession) -> None:
        # Selective diff + upsert instead of DELETE-then-INSERT: wholesale
        # deletion is racy under concurrent saves (a second save's DELETE
        # wipes rows the first save just inserted before either commits).
        # Consistent with SqlAlchemyWorkoutRepository's exercise handling.
        session_id_str = str(session.id.value)
        model = WorkoutSessionMapper.to_model(session)

        new_set_numbers = {log.id: log.set_number for log in model.logs}
        result = await self._session.execute(
            select(WorkoutLogModel.id, WorkoutLogModel.set_number).where(
                WorkoutLogModel.session_id == session_id_str
            )
        )
        existing_set_numbers = dict(result.all())

        stale_ids = existing_set_numbers.keys() - new_set_numbers.keys()
        if stale_ids:
            # Delete only rows actually removed from the aggregate. This also
            # frees their (session_id, workout_exercise_id, set_number) slots
            # before the merge below inserts new rows.
            await self._session.execute(
                delete(WorkoutLogModel).where(WorkoutLogModel.id.in_(stale_ids))
            )

        renumbered_ids = {
            log_id
            for log_id in existing_set_numbers.keys() & new_set_numbers.keys()
            if existing_set_numbers[log_id] != new_set_numbers[log_id]
        }
        if renumbered_ids:
            # Park renumbered rows on temporary negative slots so set-number
            # shuffles never trip the per-row UNIQUE
            # (session_id, workout_exercise_id, set_number) constraint while
            # the merge rewrites final values. Set numbers are >= 1, so
            # -set_number - 1 is always negative and collision-free.
            await self._session.execute(
                update(WorkoutLogModel)
                .where(WorkoutLogModel.id.in_(renumbered_ids))
                .values(set_number=-WorkoutLogModel.set_number - 1)
                .execution_options(synchronize_session="fetch")
            )

        # ORM-level upsert: INSERT new rows, UPDATE surviving ones.
        await self._session.merge(model)
        await self._session.flush()

    async def get_by_id(self, id: WorkoutSessionId) -> WorkoutSession | None:
        stmt = (
            select(WorkoutSessionModel)
            .where(WorkoutSessionModel.id == str(id.value))
            .options(selectinload(WorkoutSessionModel.logs))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return WorkoutSessionMapper.to_domain(model)

    async def delete(self, session_id: WorkoutSessionId) -> None:
        stmt = select(WorkoutSessionModel).where(
            WorkoutSessionModel.id == str(session_id.value)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return
        # ORM delete so logs cascade via "all, delete-orphan" (DB-level
        # ondelete="CASCADE" is the backstop). Do NOT reuse save()'s
        # delete-then-merge path here.
        await self._session.delete(model)
        await self._session.flush()

    async def get_sessions_for_day(
        self,
        user_id: str,
        workout_id: WorkoutId,
        training_day_id: TrainingDayId,
    ) -> list[WorkoutSession]:
        stmt = (
            select(WorkoutSessionModel)
            .where(
                WorkoutSessionModel.user_id == user_id,
                WorkoutSessionModel.workout_id == str(workout_id.value),
                WorkoutSessionModel.training_day_id == str(training_day_id.value),
            )
            .order_by(WorkoutSessionModel.started_at.desc())
            .options(selectinload(WorkoutSessionModel.logs))
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [WorkoutSessionMapper.to_domain(m) for m in models]
