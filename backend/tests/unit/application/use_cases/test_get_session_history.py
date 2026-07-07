"""Unit tests for GetSessionHistoryUseCase."""
from __future__ import annotations

from datetime import date

import pytest
from returns.result import Success

from backend.src.application.commands import GetSessionHistoryQuery
from backend.src.application.dtos import SessionHistoryItemDTO, SessionHistoryLogDTO
from backend.src.application.use_cases.get_session_history import GetSessionHistoryUseCase
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)


def _make_history_item(
    item_id: str = "session-1",
    status: str = "completed",
    logs: tuple[SessionHistoryLogDTO, ...] = (),
) -> SessionHistoryItemDTO:
    return SessionHistoryItemDTO(
        id=item_id,
        workout_id="workout-1",
        training_day_id="day-1",
        workout_name="Push Day",
        day_of_week="MONDAY",
        started_at="2026-07-01T10:00:00+00:00",
        completed_at="2026-07-01T11:00:00+00:00" if status == "completed" else None,
        status=status,
        logs=logs,
    )


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def use_case(session_repo: InMemorySessionRepository) -> GetSessionHistoryUseCase:
    return GetSessionHistoryUseCase(session_repo)


async def test_history_empty_returns_empty_list(
    use_case: GetSessionHistoryUseCase,
) -> None:
    query = GetSessionHistoryQuery(user_id="user-1")
    result = await use_case.execute(query)
    assert isinstance(result, Success)
    assert result.unwrap() == []


async def test_history_passes_filter_params_to_repo(
    use_case: GetSessionHistoryUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    query = GetSessionHistoryQuery(
        user_id="user-1",
        workout_id="workout-1",
        day_id="day-1",
        status="completed",
        date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 30),
        limit=5,
        offset=10,
    )
    result = await use_case.execute(query)
    assert isinstance(result, Success)
    assert session_repo.last_history_call == {
        "user_id": "user-1",
        "workout_id": "workout-1",
        "day_id": "day-1",
        "status": "completed",
        "date_from": date(2026, 6, 1),
        "date_to": date(2026, 6, 30),
        "limit": 5,
        "offset": 10,
    }


async def test_history_defaults_pagination_and_null_filters(
    use_case: GetSessionHistoryUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    query = GetSessionHistoryQuery(user_id="user-1")
    await use_case.execute(query)
    assert session_repo.last_history_call == {
        "user_id": "user-1",
        "workout_id": None,
        "day_id": None,
        "status": None,
        "date_from": None,
        "date_to": None,
        "limit": 20,
        "offset": 0,
    }


async def test_history_propagates_repo_results_as_dtos(
    use_case: GetSessionHistoryUseCase,
    session_repo: InMemorySessionRepository,
) -> None:
    log = SessionHistoryLogDTO(
        id="log-1",
        workout_exercise_id="we-1",
        exercise_name="Bench Press",
        set_number=1,
        reps_completed=10,
        weight_kg=80.0,
    )
    newer = _make_history_item(item_id="session-2", status="in_progress")
    older = _make_history_item(item_id="session-1", status="completed", logs=(log,))
    session_repo.seed_history([newer, older])

    result = await use_case.execute(GetSessionHistoryQuery(user_id="user-1"))
    assert isinstance(result, Success)
    items = result.unwrap()
    assert [i.id for i in items] == ["session-2", "session-1"]
    assert items[0].status == "in_progress"
    assert items[0].completed_at is None
    assert items[1].logs[0].exercise_name == "Bench Press"
    assert items[1].logs[0].weight_kg == 80.0
