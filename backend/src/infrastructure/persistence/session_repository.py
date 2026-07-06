"""SqlAlchemySessionRepository — infrastructure layer."""
from __future__ import annotations

from sqlalchemy import delete, select
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
        session_id_str = str(session.id.value)
        # Delete-then-merge: remove all existing logs for this session, then
        # re-insert them alongside the session model. Consistent with
        # SqlAlchemyWorkoutRepository's exercise handling strategy.
        await self._session.execute(
            delete(WorkoutLogModel).where(WorkoutLogModel.session_id == session_id_str)
        )
        await self._session.flush()
        model = WorkoutSessionMapper.to_model(session)
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
