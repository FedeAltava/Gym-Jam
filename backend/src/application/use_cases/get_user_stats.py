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
        """Consecutive plan-days with a completed session, walking back from
        today. Non-plan days never break the streak; the first plan day
        without a session ends it — except today, whose session may simply
        not have happened yet.
        """
        plan_days = set(await self._stats_repo.get_active_plan_days(user_id))
        if not plan_days:
            return 0

        since = today - timedelta(days=STREAK_LOOKBACK_DAYS - 1)
        completed = await self._stats_repo.get_completed_session_dates(
            user_id, since
        )

        streak = 0
        for offset in range(STREAK_LOOKBACK_DAYS):
            day = today - timedelta(days=offset)
            if _DAY_NAMES[day.weekday()] not in plan_days:
                continue  # rest day — does not affect the streak
            if day in completed:
                streak += 1
            elif day == today:
                continue  # today's plan session still pending — don't break
            else:
                break  # missed plan day — streak ends here
        return streak
