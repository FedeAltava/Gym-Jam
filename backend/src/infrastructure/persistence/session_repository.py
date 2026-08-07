"""SqlAlchemySessionRepository — infrastructure layer."""
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.read_models import SessionLogSnapshot, SessionSnapshot
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.value_objects import TrainingDayId, WorkoutId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId
from backend.src.infrastructure.persistence.mappers import WorkoutSessionMapper
from backend.src.infrastructure.persistence.models import (
    ExerciseModel,
    PersonalRecordModel,
    TrainingDayModel,
    WorkoutExerciseModel,
    WorkoutLogModel,
    WorkoutModel,
    WorkoutSessionModel,
)


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

        # merge() writes the FULL object state back to the row. The mapper does
        # not carry created_at or duration_minutes (the app never writes them
        # through this path), so a naive merge would overwrite the existing
        # row's values with NULL/defaults, destroying persisted data. Load the
        # existing row's values and copy them onto the model before merging so
        # merge preserves them. For a brand-new session (no existing row) the
        # model's own defaults apply on INSERT.
        existing_row = (
            await self._session.execute(
                select(
                    WorkoutSessionModel.created_at,
                    WorkoutSessionModel.duration_minutes,
                ).where(WorkoutSessionModel.id == session_id_str)
            )
        ).one_or_none()
        if existing_row is not None:
            model.created_at = existing_row.created_at
            model.duration_minutes = existing_row.duration_minutes

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

    async def get_in_progress_for_day(
        self,
        user_id: str,
        training_day_id: TrainingDayId,
    ) -> WorkoutSession | None:
        stmt = (
            select(WorkoutSessionModel)
            .where(
                WorkoutSessionModel.user_id == user_id,
                WorkoutSessionModel.training_day_id == str(training_day_id.value),
                WorkoutSessionModel.completed_at.is_(None),
            )
            .options(selectinload(WorkoutSessionModel.logs))
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
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

    async def get_history_item_for_user(
        self,
        user_id: str,
        session_id: str,
    ) -> SessionSnapshot | None:
        # Single-session read model, scoped by user_id so one user cannot fetch
        # another user's session. Reuses list_history_for_user's enriched query
        # (workout name, day-of-week, exercise names, PR count) instead of the
        # bare aggregate — the detail page needs those joined fields.
        items = await self.list_history_for_user(
            user_id=user_id,
            workout_id=None,
            day_id=None,
            status=None,
            date_from=None,
            date_to=None,
            limit=1,
            offset=0,
            session_id=session_id,
        )
        return items[0] if items else None

    async def list_history_for_user(
        self,
        user_id: str,
        workout_id: WorkoutId | None,
        day_id: TrainingDayId | None,
        status: str | None,
        date_from: date | None,
        date_to: date | None,
        limit: int,
        offset: int,
        session_id: str | None = None,
    ) -> list[SessionSnapshot]:
        # Exactly two queries, zero N+1.
        #
        # Query 1 — page of sessions with workout name + day-of-week.
        # Column-only select ON PURPOSE: loading WorkoutSessionModel entities
        # would auto-fire the logs relationship (lazy="selectin") — a third
        # query that cannot carry the exercise-name join.
        # Pre-grouped PR counts per session, attached via LEFT JOIN so
        # sessions without PRs still return (pr_count = 0).
        pr_counts = (
            select(
                PersonalRecordModel.session_id.label("session_id"),
                func.count().label("pr_count"),
            )
            .group_by(PersonalRecordModel.session_id)
            .subquery()
        )
        stmt = (
            select(
                WorkoutSessionModel.id,
                WorkoutSessionModel.workout_id,
                WorkoutSessionModel.training_day_id,
                WorkoutSessionModel.started_at,
                WorkoutSessionModel.completed_at,
                WorkoutModel.name.label("workout_name"),
                TrainingDayModel.day_of_week,
                func.coalesce(pr_counts.c.pr_count, 0).label("pr_count"),
            )
            .join(WorkoutModel, WorkoutSessionModel.workout_id == WorkoutModel.id)
            .join(
                TrainingDayModel,
                WorkoutSessionModel.training_day_id == TrainingDayModel.id,
            )
            .outerjoin(pr_counts, pr_counts.c.session_id == WorkoutSessionModel.id)
            .where(WorkoutSessionModel.user_id == user_id)
            .order_by(WorkoutSessionModel.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if session_id is not None:
            stmt = stmt.where(WorkoutSessionModel.id == session_id)
        if workout_id is not None:
            stmt = stmt.where(WorkoutSessionModel.workout_id == str(workout_id.value))
        if day_id is not None:
            stmt = stmt.where(WorkoutSessionModel.training_day_id == str(day_id.value))
        # "status" is derived — there is no status column. in_progress means
        # the session was never completed.
        if status == "in_progress":
            stmt = stmt.where(WorkoutSessionModel.completed_at.is_(None))
        elif status == "completed":
            stmt = stmt.where(WorkoutSessionModel.completed_at.is_not(None))
        # Date bounds are UTC day boundaries; upper bound is exclusive of the
        # day AFTER date_to so the full date_to day is included.
        if date_from is not None:
            stmt = stmt.where(
                WorkoutSessionModel.started_at
                >= datetime.combine(date_from, time.min, tzinfo=UTC)
            )
        if date_to is not None:
            stmt = stmt.where(
                WorkoutSessionModel.started_at
                < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
            )
        rows = (await self._session.execute(stmt)).all()

        # Query 2 — all logs for the page's sessions with exercise names,
        # one IN query. Outer join to the catalog: workout_exercises.exercise_id
        # is a soft reference (see models.py) — legacy rows can hold free-text
        # ids with no catalog row, and those logs must not be dropped.
        session_ids = [row.id for row in rows]
        logs_by_session: dict[str, list[SessionLogSnapshot]] = {
            sid: [] for sid in session_ids
        }
        if session_ids:
            logs_stmt = (
                select(
                    WorkoutLogModel.id,
                    WorkoutLogModel.session_id,
                    WorkoutLogModel.workout_exercise_id,
                    WorkoutLogModel.set_number,
                    WorkoutLogModel.reps_completed,
                    WorkoutLogModel.weight_kg,
                    WorkoutExerciseModel.exercise_id,
                    ExerciseModel.name.label("exercise_name"),
                    ExerciseModel.muscle_group.label("muscle_group"),
                )
                .join(
                    WorkoutExerciseModel,
                    WorkoutLogModel.workout_exercise_id == WorkoutExerciseModel.id,
                )
                .outerjoin(
                    ExerciseModel,
                    WorkoutExerciseModel.exercise_id == ExerciseModel.id,
                )
                .where(WorkoutLogModel.session_id.in_(session_ids))
                .order_by(WorkoutLogModel.set_number)
            )
            for log_row in (await self._session.execute(logs_stmt)).all():
                logs_by_session[log_row.session_id].append(
                    SessionLogSnapshot(
                        id=log_row.id,
                        workout_exercise_id=log_row.workout_exercise_id,
                        exercise_name=(
                            log_row.exercise_name
                            if log_row.exercise_name is not None
                            else log_row.exercise_id
                        ),
                        muscle_group=log_row.muscle_group,
                        set_number=log_row.set_number,
                        reps_completed=log_row.reps_completed,
                        weight_kg=log_row.weight_kg,
                    )
                )

        return [
            SessionSnapshot(
                id=row.id,
                workout_id=row.workout_id,
                training_day_id=row.training_day_id,
                workout_name=row.workout_name,
                day_of_week=row.day_of_week,
                started_at=row.started_at,
                completed_at=row.completed_at,
                logs=tuple(logs_by_session[row.id]),
                pr_count=row.pr_count,
            )
            for row in rows
        ]

    async def count_history_for_user(
        self,
        user_id: str,
        workout_id: WorkoutId | None,
        day_id: TrainingDayId | None,
        status: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> int:
        """Return the total row count matching the same filters as list_history_for_user."""
        stmt = (
            select(func.count())
            .select_from(WorkoutSessionModel)
            .where(WorkoutSessionModel.user_id == user_id)
        )
        if workout_id is not None:
            stmt = stmt.where(WorkoutSessionModel.workout_id == str(workout_id.value))
        if day_id is not None:
            stmt = stmt.where(WorkoutSessionModel.training_day_id == str(day_id.value))
        if status == "in_progress":
            stmt = stmt.where(WorkoutSessionModel.completed_at.is_(None))
        elif status == "completed":
            stmt = stmt.where(WorkoutSessionModel.completed_at.is_not(None))
        if date_from is not None:
            stmt = stmt.where(
                WorkoutSessionModel.started_at
                >= datetime.combine(date_from, time.min, tzinfo=UTC)
            )
        if date_to is not None:
            stmt = stmt.where(
                WorkoutSessionModel.started_at
                < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
            )
        result = await self._session.execute(stmt)
        return result.scalar_one()
