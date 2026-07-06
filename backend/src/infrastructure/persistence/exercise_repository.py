from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.entities.exercise import Exercise
from backend.src.domain.repositories.exercise_repository import ExerciseRepository
from backend.src.infrastructure.persistence.models import ExerciseModel, WorkoutExerciseModel


def _to_domain(model: ExerciseModel) -> Exercise:
    return Exercise(
        id=model.id,
        name=model.name,
        muscle_group=model.muscle_group,
        is_bodyweight=model.is_bodyweight,
        owner_id=model.owner_id,
    )


class SqlAlchemyExerciseRepository(ExerciseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self, user_id: str | None = None) -> list[Exercise]:
        stmt = select(ExerciseModel)
        if user_id is not None:
            stmt = stmt.where(
                or_(ExerciseModel.owner_id.is_(None), ExerciseModel.owner_id == user_id)
            )
        else:
            stmt = stmt.where(ExerciseModel.owner_id.is_(None))
        result = await self._session.execute(stmt)
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

    async def save(self, exercise: Exercise) -> None:
        model = ExerciseModel(
            id=exercise.id,
            name=exercise.name,
            muscle_group=exercise.muscle_group,
            is_bodyweight=exercise.is_bodyweight,
            owner_id=exercise.owner_id,
        )
        self._session.add(model)
        await self._session.flush()

    async def delete(self, exercise_id: str) -> None:
        result = await self._session.execute(
            select(ExerciseModel).where(ExerciseModel.id == exercise_id)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    async def is_referenced_by_workout(self, exercise_id: str) -> bool:
        result = await self._session.execute(
            select(WorkoutExerciseModel.id)
            .where(WorkoutExerciseModel.exercise_id == exercise_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
