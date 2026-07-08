"""SqlAlchemyStatsRepository — infrastructure layer."""
from __future__ import annotations

from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.repositories.stats_repository import (
    StatsAggregates,
    StatsRepository,
)
from backend.src.infrastructure.persistence.models import (
    PersonalRecordModel,
    TrainingDayModel,
    WorkoutLogModel,
    WorkoutModel,
    WorkoutSessionModel,
)


class SqlAlchemyStatsRepository(StatsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_plan_days(self, user_id: str) -> list[str]:
        stmt = (
            select(TrainingDayModel.day_of_week)
            .join(WorkoutModel, TrainingDayModel.workout_id == WorkoutModel.id)
            .where(
                WorkoutModel.user_id == user_id,
                WorkoutModel.is_active.is_(True),
            )
            .distinct()
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_completed_session_dates(
        self, user_id: str, since: date
    ) -> set[date]:
        stmt = select(WorkoutSessionModel.started_at).where(
            WorkoutSessionModel.user_id == user_id,
            WorkoutSessionModel.completed_at.is_not(None),
            WorkoutSessionModel.started_at
            >= datetime.combine(since, time.min, tzinfo=UTC),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        # SQLite returns naive datetimes (stored as UTC); normalize either way.
        return {
            (dt.astimezone(UTC) if dt.tzinfo is not None else dt).date()
            for dt in rows
        }

    async def get_aggregates(
        self, user_id: str, weekly_start: datetime
    ) -> StatsAggregates:
        completed = (
            WorkoutSessionModel.user_id == user_id,
            WorkoutSessionModel.completed_at.is_not(None),
        )

        total_sessions = (
            await self._session.execute(
                select(func.count()).select_from(WorkoutSessionModel).where(*completed)
            )
        ).scalar_one()

        weekly_sessions = (
            await self._session.execute(
                select(func.count())
                .select_from(WorkoutSessionModel)
                .where(*completed, WorkoutSessionModel.started_at >= weekly_start)
            )
        ).scalar_one()

        # SUM skips rows whose product is NULL, so bodyweight logs
        # (weight_kg IS NULL) contribute 0 by construction.
        weekly_volume = (
            await self._session.execute(
                select(
                    func.coalesce(
                        func.sum(
                            WorkoutLogModel.weight_kg * WorkoutLogModel.reps_completed
                        ),
                        0.0,
                    )
                )
                .select_from(WorkoutLogModel)
                .join(
                    WorkoutSessionModel,
                    WorkoutLogModel.session_id == WorkoutSessionModel.id,
                )
                .where(*completed, WorkoutSessionModel.started_at >= weekly_start)
            )
        ).scalar_one()

        total_prs = (
            await self._session.execute(
                select(func.count())
                .select_from(PersonalRecordModel)
                .where(PersonalRecordModel.user_id == user_id)
            )
        ).scalar_one()

        weekly_prs = (
            await self._session.execute(
                select(func.count())
                .select_from(PersonalRecordModel)
                .where(
                    PersonalRecordModel.user_id == user_id,
                    PersonalRecordModel.achieved_at >= weekly_start,
                )
            )
        ).scalar_one()

        return StatsAggregates(
            total_sessions=total_sessions,
            total_prs=total_prs,
            weekly_volume_kg=float(weekly_volume),
            weekly_sessions=weekly_sessions,
            weekly_prs=weekly_prs,
        )
