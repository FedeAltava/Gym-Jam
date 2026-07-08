"""StatsRepository ABC — port for aggregated training statistics."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class StatsAggregates:
    """Raw SQL aggregates for the stats endpoint.

    The streak is NOT here on purpose — it is a domain walk over plan days
    computed in the use case (ADR 10), fed by the two date-oriented port
    methods below.
    """

    total_sessions: int
    total_prs: int
    weekly_volume_kg: float
    weekly_sessions: int
    weekly_prs: int


class StatsRepository(ABC):
    @abstractmethod
    async def get_active_plan_days(self, user_id: str) -> list[str]:
        """Distinct day_of_week values ("MONDAY".."SUNDAY") across the
        user's ACTIVE workouts. Empty when the user has no active workout.
        """
        ...

    @abstractmethod
    async def get_completed_session_dates(
        self, user_id: str, since: date
    ) -> set[date]:
        """UTC calendar dates (of started_at) on which the user has at least
        one COMPLETED session, from `since` (inclusive) to today.
        """
        ...

    @abstractmethod
    async def get_aggregates(
        self, user_id: str, weekly_start: datetime
    ) -> StatsAggregates:
        """Count/sum aggregates. `weekly_start` is Monday 00:00 UTC of the
        current week; "weekly" figures cover [weekly_start, now]. Volume is
        SUM(weight_kg * reps_completed) over logs of completed sessions —
        NULL weights (bodyweight) contribute 0.
        """
        ...
