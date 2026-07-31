"""Unit tests for GetSessionHistoryUseCase."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from returns.result import Success

from backend.src.application.commands import GetSessionHistoryQuery
from backend.src.application.dtos import PaginatedSessionHistoryDTO, SessionHistoryLogDTO
from backend.src.application.use_cases.get_session_history import GetSessionHistoryUseCase
from backend.src.domain.read_models import SessionLogSnapshot, SessionSnapshot
from backend.tests.unit.application.use_cases.in_memory_session_repository import (
    InMemorySessionRepository,
)

_STARTED = datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc)
_COMPLETED = datetime(2026, 7, 1, 11, 0, 0, tzinfo=timezone.utc)


def _make_snapshot(
    item_id: str = "session-1",
    status: str = "completed",
    logs: tuple[SessionLogSnapshot, ...] = (),
) -> SessionSnapshot:
    return SessionSnapshot(
        id=item_id,
        workout_id="workout-1",
        training_day_id="day-1",
        workout_name="Push Day",
        day_of_week="MONDAY",
        started_at=_STARTED,
        completed_at=_COMPLETED if status == "completed" else None,
        logs=logs,
    )


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def use_case(session_repo: InMemorySessionRepository) -> GetSessionHistoryUseCase:
    return GetSessionHistoryUseCase(session_repo)


async def test_history_empty_returns_paginated_dto(
    use_case: GetSessionHistoryUseCase,
) -> None:
    query = GetSessionHistoryQuery(user_id="user-1")
    result = await use_case.execute(query)
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, PaginatedSessionHistoryDTO)
    assert dto.items == ()
    assert dto.total == 0
    assert dto.page == 1
    assert dto.page_size == 20


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
    log_snap = SessionLogSnapshot(
        id="log-1",
        workout_exercise_id="we-1",
        exercise_name="Bench Press",
        muscle_group="Pecho",
        set_number=1,
        reps_completed=10,
        weight_kg=80.0,
    )
    newer = _make_snapshot(item_id="session-2", status="in_progress")
    older = _make_snapshot(item_id="session-1", status="completed", logs=(log_snap,))
    session_repo.seed_history([newer, older])

    result = await use_case.execute(GetSessionHistoryQuery(user_id="user-1"))
    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, PaginatedSessionHistoryDTO)
    assert dto.total == 2
    items = dto.items
    assert [i.id for i in items] == ["session-2", "session-1"]
    assert items[0].status == "in_progress"
    assert items[0].completed_at is None
    assert items[1].logs[0].exercise_name == "Bench Press"
    assert items[1].logs[0].weight_kg == 80.0
