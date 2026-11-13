"""SqlAlchemyPersonalRecordRepository — infrastructure layer."""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterator

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.estimated_one_rep_max import beats_record, estimated_one_rep_max
from backend.src.domain.repositories.personal_record_repository import (
    PersonalRecordRepository,
)
from backend.src.infrastructure.persistence.models import (
    PersonalRecordModel,
    SessionExerciseSwapModel,
    WorkoutExerciseModel,
    WorkoutLogModel,
    WorkoutSessionModel,
)


class SqlAlchemyPersonalRecordRepository(PersonalRecordRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @asynccontextmanager
    async def savepoint(self) -> AsyncIterator[None]:
        async with self._session.begin_nested():
            yield

    async def get_catalog_exercise_ids(
        self, workout_exercise_ids: list[str]
    ) -> dict[str, str]:
        if not workout_exercise_ids:
            return {}
        stmt = select(WorkoutExerciseModel.id, WorkoutExerciseModel.exercise_id).where(
            WorkoutExerciseModel.id.in_(workout_exercise_ids)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row.id: row.exercise_id for row in rows}

    async def get_previous_best_estimates(
        self,
        user_id: str,
        exclude_session_id: str,
        exercise_ids: list[str],
    ) -> dict[str, float]:
        if not exercise_ids:
            return {}
        # One batch query over the user's full completed-log history (ADR 5):
        # logs → plan rows (catalog id) → sessions (owner + completed filter).
        # A session swap replaces the plan row's catalog id for that session.
        done_exercise_id = func.coalesce(
            SessionExerciseSwapModel.exercise_id, WorkoutExerciseModel.exercise_id
        )
        # Epley in SQL — same formula as domain `estimated_one_rep_max`.
        estimate = WorkoutLogModel.weight_kg * (1.0 + WorkoutLogModel.reps_completed / 30.0)
        stmt = (
            select(
                done_exercise_id.label("exercise_id"),
                func.max(estimate).label("best_estimate"),
            )
            .join(
                WorkoutExerciseModel,
                WorkoutLogModel.workout_exercise_id == WorkoutExerciseModel.id,
            )
            .outerjoin(
                SessionExerciseSwapModel,
                (SessionExerciseSwapModel.session_id == WorkoutLogModel.session_id)
                & (SessionExerciseSwapModel.workout_exercise_id == WorkoutLogModel.workout_exercise_id),
            )
            .join(
                WorkoutSessionModel,
                WorkoutLogModel.session_id == WorkoutSessionModel.id,
            )
            .where(
                WorkoutSessionModel.user_id == user_id,
                WorkoutSessionModel.completed_at.is_not(None),
                WorkoutSessionModel.id != exclude_session_id,
                done_exercise_id.in_(exercise_ids),
                WorkoutLogModel.weight_kg > 0,
            )
            .group_by(done_exercise_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row.exercise_id: float(row.best_estimate) for row in rows}

    async def upsert_if_higher(
        self,
        user_id: str,
        exercise_id: str,
        weight_kg: float,
        reps: int,
        session_id: str,
        achieved_at: datetime,
    ) -> bool:
        # Portable SELECT-then-INSERT/UPDATE (ADR 4) — no dialect ON CONFLICT.
        # Single-user request flow; the UNIQUE constraint is the race backstop.
        stmt = select(PersonalRecordModel).where(
            PersonalRecordModel.user_id == user_id,
            PersonalRecordModel.exercise_id == exercise_id,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()

        if existing is None:
            self._session.add(
                PersonalRecordModel(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    exercise_id=exercise_id,
                    weight_kg=weight_kg,
                    reps=reps,
                    achieved_at=achieved_at,
                    session_id=session_id,
                )
            )
            await self._session.flush()
            return True

        if beats_record(
            estimated_one_rep_max(weight_kg, reps),
            estimated_one_rep_max(existing.weight_kg, existing.reps),
        ):
            existing.weight_kg = weight_kg
            existing.reps = reps
            existing.achieved_at = achieved_at
            existing.session_id = session_id
            await self._session.flush()
            return True

        return False
