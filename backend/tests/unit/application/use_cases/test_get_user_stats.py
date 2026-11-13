"""Unit tests for GetUserStatsUseCase — streak algorithm and stat mapping."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from returns.result import Success

from backend.src.application.commands import GetUserStatsQuery
from backend.src.application.dtos import UserStatsDTO
from backend.src.application.use_cases.get_user_stats import GetUserStatsUseCase
from backend.src.domain.repositories.stats_repository import StatsAggregates
from backend.tests.unit.application.use_cases.in_memory_stats_repository import (
    InMemoryStatsRepository,
)

# Fixed anchor week (2026-07-06 is a Monday).
MONDAY = date(2026, 7, 6)
TUESDAY = date(2026, 7, 7)
WEDNESDAY = date(2026, 7, 8)
THURSDAY = date(2026, 7, 9)
FRIDAY = date(2026, 7, 10)

QUERY = GetUserStatsQuery(user_id="user-1")
WEEK = timedelta(days=7)
_NAMES = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")


def on_their_day(*dates: date) -> set[tuple[date, str]]:
    """Sessions done on the date of their own routine day."""
    return {(d, _NAMES[d.weekday()]) for d in dates}


@pytest.fixture
def stats_repo() -> InMemoryStatsRepository:
    return InMemoryStatsRepository()


@pytest.fixture
def use_case(stats_repo: InMemoryStatsRepository) -> GetUserStatsUseCase:
    return GetUserStatsUseCase(stats_repo)


# ── Streak ────────────────────────────────────────────────────────────────────


async def test_streak_zero_when_no_active_workout(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = []
    stats_repo.completed_days = on_their_day(MONDAY, WEDNESDAY)

    result = await use_case.execute(QUERY, today=FRIDAY)

    assert isinstance(result, Success)
    assert result.unwrap().streak == 0


async def test_streak_zero_when_no_sessions(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = ["MONDAY", "WEDNESDAY", "FRIDAY"]
    stats_repo.completed_days = set()

    result = await use_case.execute(QUERY, today=FRIDAY)

    assert isinstance(result, Success)
    assert result.unwrap().streak == 0


async def test_streak_counts_consecutive_plan_days(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = ["MONDAY", "WEDNESDAY", "FRIDAY"]
    stats_repo.completed_days = on_their_day(MONDAY, WEDNESDAY, FRIDAY)

    result = await use_case.execute(QUERY, today=FRIDAY)

    # Previous week's Friday (2026-07-03) has no session → walk stops at 3.
    assert result.unwrap().streak == 3


async def test_streak_breaks_on_a_plan_day_missed_in_a_past_week(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = ["MONDAY", "WEDNESDAY", "FRIDAY"]
    # Last week's Wednesday missed; this week only Monday so far.
    stats_repo.completed_days = on_their_day(MONDAY - WEEK, FRIDAY - WEEK, MONDAY)

    result = await use_case.execute(QUERY, today=WEDNESDAY)

    # This week: Monday counts, today's Wednesday is pending. Last week:
    # Friday counts, then the missed Wednesday ends the streak.
    assert result.unwrap().streak == 2


async def test_a_routine_day_done_on_another_date_keeps_the_streak(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = ["MONDAY", "WEDNESDAY", "FRIDAY"]
    # Monday's routine day done on Tuesday.
    stats_repo.completed_days = {(TUESDAY, "MONDAY")} | on_their_day(WEDNESDAY, FRIDAY)

    result = await use_case.execute(QUERY, today=FRIDAY)

    assert result.unwrap().streak == 3


async def test_days_still_pending_this_week_do_not_break_the_streak(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = ["MONDAY", "WEDNESDAY", "FRIDAY"]
    # Last week complete; this week Monday done, Wednesday not done yet.
    stats_repo.completed_days = on_their_day(MONDAY - WEEK, WEDNESDAY - WEEK, FRIDAY - WEEK, MONDAY)

    result = await use_case.execute(QUERY, today=THURSDAY)

    # Wednesday can still be done this week, so it does not end the streak.
    assert result.unwrap().streak == 4


async def test_two_routine_days_on_the_same_date_both_count(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = ["MONDAY", "WEDNESDAY", "FRIDAY"]
    stats_repo.completed_days = {(TUESDAY, "MONDAY"), (TUESDAY, "WEDNESDAY")}

    result = await use_case.execute(QUERY, today=WEDNESDAY)

    assert result.unwrap().streak == 2


async def test_streak_ignores_non_plan_days(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = ["MONDAY", "WEDNESDAY"]
    stats_repo.completed_days = on_their_day(MONDAY, WEDNESDAY)

    # Today is Thursday: Thu (non-plan) and Tue (non-plan) have no sessions —
    # neither breaks the streak.
    result = await use_case.execute(QUERY, today=THURSDAY)

    assert result.unwrap().streak == 2


async def test_streak_today_pending_does_not_break(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = ["MONDAY", "WEDNESDAY", "FRIDAY"]
    stats_repo.completed_days = on_their_day(MONDAY, WEDNESDAY)  # Friday not trained YET

    result = await use_case.execute(QUERY, today=FRIDAY)

    # Today is a plan day without a session, but the day is not over —
    # skip it instead of breaking (ADR 10).
    assert result.unwrap().streak == 2


async def test_streak_caps_at_365_days(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = [
        "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY",
    ]
    stats_repo.completed_days = on_their_day(*(FRIDAY - timedelta(days=i) for i in range(500)))

    result = await use_case.execute(QUERY, today=FRIDAY)

    assert result.unwrap().streak == 365


# ── Weekly window and aggregate mapping ───────────────────────────────────────


async def test_weekly_window_starts_monday_utc(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    await use_case.execute(QUERY, today=FRIDAY)

    assert stats_repo.weekly_start_seen == datetime(2026, 7, 6, 0, 0, tzinfo=UTC)


async def test_stats_dto_maps_aggregates(
    use_case: GetUserStatsUseCase, stats_repo: InMemoryStatsRepository
) -> None:
    stats_repo.plan_days = ["FRIDAY"]
    stats_repo.completed_days = on_their_day(FRIDAY)
    stats_repo.aggregates = StatsAggregates(
        total_sessions=12,
        total_prs=4,
        weekly_volume_kg=1234.5,
        weekly_sessions=3,
        weekly_prs=2,
    )

    result = await use_case.execute(QUERY, today=FRIDAY)

    assert result.unwrap() == UserStatsDTO(
        total_sessions=12,
        streak=1,
        total_prs=4,
        weekly_volume_kg=1234.5,
        weekly_sessions=3,
        weekly_prs=2,
    )


async def test_zero_state_new_user_returns_all_zeros(
    use_case: GetUserStatsUseCase,
) -> None:
    result = await use_case.execute(QUERY, today=TUESDAY)

    assert isinstance(result, Success)
    assert result.unwrap() == UserStatsDTO(
        total_sessions=0,
        streak=0,
        total_prs=0,
        weekly_volume_kg=0.0,
        weekly_sessions=0,
        weekly_prs=0,
    )
