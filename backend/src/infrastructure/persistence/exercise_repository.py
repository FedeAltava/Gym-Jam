from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.entities.exercise import Exercise
from backend.src.domain.repositories.exercise_repository import ExerciseRepository
from backend.src.infrastructure.persistence.models import ExerciseModel


def _to_domain(model: ExerciseModel) -> Exercise:
    return Exercise(id=model.id, name=model.name, muscle_group=model.muscle_group)


class SqlAlchemyExerciseRepository(ExerciseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Exercise]:
        result = await self._session.execute(select(ExerciseModel))
        return [_to_domain(m) for m in result.scalars().all()]

    async def get_by_id(self, exercise_id: str) -> Exercise | None:
        result = await self._session.execute(
            select(ExerciseModel).where(ExerciseModel.id == exercise_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _to_domain(model)

    async def exists(self, exercise_id: str) -> bool:
        result = await self._session.execute(
            select(ExerciseModel.id).where(ExerciseModel.id == exercise_id)
        )
        return result.scalar_one_or_none() is not None
