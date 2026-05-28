from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutId
from backend.src.infrastructure.persistence.mappers import WorkoutMapper
from backend.src.infrastructure.persistence.models import WorkoutModel, TrainingDayModel


class SqlAlchemyWorkoutRepository(WorkoutRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, workout: Workout) -> None:
        model = WorkoutMapper.to_model(workout)
        await self._session.merge(model)
        await self._session.flush()

    async def get_by_id(self, workout_id: WorkoutId) -> Workout | None:
        stmt = (
            select(WorkoutModel)
            .where(WorkoutModel.id == str(workout_id.value))
            .options(
                selectinload(WorkoutModel.training_days).selectinload(TrainingDayModel.exercises)
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return WorkoutMapper.to_domain(model)

    async def get_by_user(self, user_id: str) -> list[Workout]:
        stmt = (
            select(WorkoutModel)
            .where(WorkoutModel.user_id == user_id)
            .options(
                selectinload(WorkoutModel.training_days).selectinload(TrainingDayModel.exercises)
            )
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [WorkoutMapper.to_domain(m) for m in models]
