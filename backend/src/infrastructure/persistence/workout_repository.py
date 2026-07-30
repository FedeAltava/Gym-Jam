from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutId
from backend.src.infrastructure.persistence.mappers import WorkoutMapper
from backend.src.infrastructure.persistence.models import WorkoutModel, TrainingDayModel, WorkoutExerciseModel


class SqlAlchemyWorkoutRepository(WorkoutRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, workout: Workout) -> None:
        # Selective diff + upsert instead of DELETE-then-INSERT: this guards
        # the narrow DELETE-then-INSERT slot-reuse race (a second save's DELETE
        # wipes rows the first save just inserted before either commits).
        # Serialization of concurrent WRITERS (the diff-computation race where
        # two sessions read the same stale aggregate) is provided by callers
        # using get_by_id_locked at load time, NOT by this diff algorithm.
        workout_id_str = str(workout.id.value)
        model = WorkoutMapper.to_model(workout)

        new_orders = {
            exercise.id: exercise.order_in_day
            for day in model.training_days
            for exercise in day.exercises
        }
        result = await self._session.execute(
            select(WorkoutExerciseModel.id, WorkoutExerciseModel.order_in_day).where(
                WorkoutExerciseModel.workout_id == workout_id_str
            )
        )
        existing_orders = dict(result.all())

        stale_ids = existing_orders.keys() - new_orders.keys()
        if stale_ids:
            # Delete only rows actually removed from the aggregate. This also
            # frees their (training_day_id, order_in_day) slots before the
            # merge below inserts new rows.
            await self._session.execute(
                delete(WorkoutExerciseModel).where(WorkoutExerciseModel.id.in_(stale_ids))
            )

        reordered_ids = {
            exercise_id
            for exercise_id in existing_orders.keys() & new_orders.keys()
            if existing_orders[exercise_id] != new_orders[exercise_id]
        }
        if reordered_ids:
            # Park reordered rows on temporary negative slots so in-flight
            # reorders never trip the per-row UNIQUE
            # (training_day_id, order_in_day) constraint while the merge
            # rewrites final positions. Orders are >= 1, so -order - 1 is
            # always negative and the mapping is collision-free.
            # synchronize_session="fetch" keeps identity-map instances in
            # sync so the merge detects the change back to the final value.
            await self._session.execute(
                update(WorkoutExerciseModel)
                .where(WorkoutExerciseModel.id.in_(reordered_ids))
                .values(order_in_day=-WorkoutExerciseModel.order_in_day - 1)
                .execution_options(synchronize_session="fetch")
            )

        # ORM-level upsert: INSERT new rows, UPDATE surviving ones.
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

    async def get_by_id_locked(self, workout_id: WorkoutId) -> Workout | None:
        stmt = (
            select(WorkoutModel)
            .where(WorkoutModel.id == str(workout_id.value))
            .options(
                selectinload(WorkoutModel.training_days).selectinload(TrainingDayModel.exercises)
            )
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return WorkoutMapper.to_domain(model)

    async def get_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> list[Workout]:
        stmt = (
            select(WorkoutModel)
            .where(WorkoutModel.user_id == user_id)
            # Newest first so recent workouts land on page 1 of the dashboard;
            # id breaks created_at ties deterministically.
            .order_by(WorkoutModel.created_at.desc(), WorkoutModel.id.asc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(WorkoutModel.training_days).selectinload(TrainingDayModel.exercises)
            )
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [WorkoutMapper.to_domain(m) for m in models]

    async def delete(self, workout_id: WorkoutId) -> bool:
        stmt = (
            select(WorkoutModel)
            .where(WorkoutModel.id == str(workout_id.value))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        return True
