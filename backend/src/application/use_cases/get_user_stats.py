"""GetUserStatsUseCase — streak + weekly/total training stats (ADR 10)."""
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from returns.result import Result, Success

from backend.src.application.commands import GetUserStatsQuery
from backend.src.application.dtos import UserStatsDTO
from backend.src.application.errors import ApplicationError
from backend.src.domain.repositories.stats_repository import StatsRepository

# The streak walk never looks further back than a year — keeps the walk and
# the completed-dates query bounded regardless of account age.
STREAK_LOOKBACK_DAYS = 365

# date.weekday() → day_of_week value used by training_days rows.
_DAY_NAMES = (
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
)


class GetUserStatsUseCase:
    def __init__(self, stats_repo: StatsRepository) -> None:
        self._stats_repo = stats_repo

    async def execute(
        self, query: GetUserStatsQuery, today: date | None = None
    ) -> Result[UserStatsDTO, ApplicationError]:
        # `today` is injectable for tests; production derives it from UTC.
        if today is None:
            today = datetime.now(UTC).date()

        # Current calendar week = Monday 00:00 UTC of the week containing today.
        monday = today - timedelta(days=today.weekday())
        weekly_start = datetime.combine(monday, time.min, tzinfo=UTC)

        streak = await self._compute_streak(query.user_id, today)
        agg = await self._stats_repo.get_aggregates(query.user_id, weekly_start)

        return Success(
            UserStatsDTO(
                total_sessions=agg.total_sessions,
                streak=streak,
                total_prs=agg.total_prs,
                weekly_volume_kg=agg.weekly_volume_kg,
                weekly_sessions=agg.weekly_sessions,
                weekly_prs=agg.weekly_prs,
            )
        )

    async def _compute_streak(self, user_id: str, today: date) -> int:
        """Consecutive routine days trained, walking back plan day by plan day.

        A plan day of a week counts as trained when a completed session of
        that routine day (its training day's day_of_week) started in that
        week, on whatever date: a Monday trained on Tuesday still counts.
        Plan days of the current week not trained yet never break the
        streak, since they can still be trained this week; the first plan
        day missed in a past week ends it. Non-plan days are ignored.
        """
        plan_days = set(await self._stats_repo.get_active_plan_days(user_id))
        if not plan_days:
            return 0

        since = today - timedelta(days=STREAK_LOOKBACK_DAYS - 1)
        trained = {
            (_monday_of(day), routine_day)
            for day, routine_day in await self._stats_repo.get_completed_session_days(user_id, since)
        }
        this_monday = _monday_of(today)

        streak = 0
        day = this_monday + timedelta(days=6)
        while day >= since:
            name = _DAY_NAMES[day.weekday()]
            if name in plan_days:
                week = _monday_of(day)
                if (week, name) in trained:
                    streak += 1
                elif week != this_monday:
                    break  # missed in a finished week — streak ends here
            day -= timedelta(days=1)
        return streak


def _monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())
