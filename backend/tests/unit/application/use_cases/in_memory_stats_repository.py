"""In-memory implementation of StatsRepository for use case unit tests."""
from __future__ import annotations

from datetime import date, datetime

from backend.src.domain.repositories.stats_repository import (
    StatsAggregates,
    StatsRepository,
)


class InMemoryStatsRepository(StatsRepository):
    def __init__(self) -> None:
        # day_of_week values ("MONDAY".."SUNDAY") of the active workout.
        self.plan_days: list[str] = []
        # UTC dates with at least one completed session (seeded per test).
        self.completed_dates: set[date] = set()
        self.aggregates = StatsAggregates(
            total_sessions=0,
            total_prs=0,
            weekly_volume_kg=0.0,
            weekly_sessions=0,
            weekly_prs=0,
        )
        # Recorded arguments — let tests assert the computed windows.
        self.since_seen: date | None = None
        self.weekly_start_seen: datetime | None = None

    async def get_active_plan_days(self, user_id: str) -> list[str]:
        return list(self.plan_days)

    async def get_completed_session_dates(
        self, user_id: str, since: date
    ) -> set[date]:
        self.since_seen = since
        return {d for d in self.completed_dates if d >= since}

    async def get_aggregates(
        self, user_id: str, weekly_start: datetime
    ) -> StatsAggregates:
        self.weekly_start_seen = weekly_start
        return self.aggregates
