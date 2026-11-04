"""Unit tests for the body weight use cases (record, list, delete)."""
from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import DeleteBodyWeightCommand, RecordBodyWeightCommand
from backend.src.application.dtos import BodyWeightEntryDTO
from backend.src.application.errors import BodyWeightEntryNotFoundError, InvalidBodyWeightError
from backend.src.application.use_cases.body_weight import (
    DeleteBodyWeightUseCase,
    ListBodyWeightUseCase,
    RecordBodyWeightUseCase,
)
from backend.tests.unit.application.use_cases.in_memory_body_weight_repository import (
    InMemoryBodyWeightRepository,
)

# 23:30 UTC on Nov 4 is already Nov 5 in Spain (UTC+1).
NOW = datetime(2026, 11, 4, 23, 30, tzinfo=UTC)


@pytest.fixture
def repo() -> InMemoryBodyWeightRepository:
    return InMemoryBodyWeightRepository()


@pytest.fixture
def record(repo: InMemoryBodyWeightRepository) -> RecordBodyWeightUseCase:
    return RecordBodyWeightUseCase(repo, clock=lambda: NOW)


async def test_record_stores_the_entry(record: RecordBodyWeightUseCase, repo: InMemoryBodyWeightRepository) -> None:
    result = await record.execute(RecordBodyWeightCommand(user_id="u1", measured_on=date(2026, 11, 4), weight_kg=84.7))

    assert result == Success(BodyWeightEntryDTO(measured_on="2026-11-04", weight_kg=84.7))
    assert [(e.measured_on, e.weight_kg) for e in await repo.list_by_user("u1")] == [(date(2026, 11, 4), 84.7)]


async def test_recording_the_same_day_again_replaces_the_weight(
    record: RecordBodyWeightUseCase, repo: InMemoryBodyWeightRepository
) -> None:
    await record.execute(RecordBodyWeightCommand(user_id="u1", measured_on=date(2026, 11, 4), weight_kg=84.7))

    await record.execute(RecordBodyWeightCommand(user_id="u1", measured_on=date(2026, 11, 4), weight_kg=84.2))

    assert [(e.measured_on, e.weight_kg) for e in await repo.list_by_user("u1")] == [(date(2026, 11, 4), 84.2)]


async def test_record_accepts_the_next_utc_day_for_users_ahead_of_utc(record: RecordBodyWeightUseCase) -> None:
    result = await record.execute(RecordBodyWeightCommand(user_id="u1", measured_on=date(2026, 11, 5), weight_kg=84.0))

    assert isinstance(result, Success)


async def test_record_rejects_a_future_date(record: RecordBodyWeightUseCase, repo: InMemoryBodyWeightRepository) -> None:
    result = await record.execute(RecordBodyWeightCommand(user_id="u1", measured_on=date(2026, 11, 6), weight_kg=84.0))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidBodyWeightError)
    assert await repo.list_by_user("u1") == []


async def test_record_rejects_an_invalid_weight(record: RecordBodyWeightUseCase, repo: InMemoryBodyWeightRepository) -> None:
    result = await record.execute(RecordBodyWeightCommand(user_id="u1", measured_on=date(2026, 11, 4), weight_kg=0))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), InvalidBodyWeightError)
    assert await repo.list_by_user("u1") == []


async def test_list_returns_only_the_users_entries_newest_first(
    record: RecordBodyWeightUseCase, repo: InMemoryBodyWeightRepository
) -> None:
    for user_id, day, weight in [("u1", 1, 85.0), ("u1", 3, 84.5), ("u2", 2, 60.0), ("u1", 2, 84.8)]:
        await record.execute(RecordBodyWeightCommand(user_id=user_id, measured_on=date(2026, 11, day), weight_kg=weight))

    result = await ListBodyWeightUseCase(repo).execute(user_id="u1")

    assert result == Success(
        (
            BodyWeightEntryDTO(measured_on="2026-11-03", weight_kg=84.5),
            BodyWeightEntryDTO(measured_on="2026-11-02", weight_kg=84.8),
            BodyWeightEntryDTO(measured_on="2026-11-01", weight_kg=85.0),
        )
    )


async def test_delete_removes_the_entry(record: RecordBodyWeightUseCase, repo: InMemoryBodyWeightRepository) -> None:
    await record.execute(RecordBodyWeightCommand(user_id="u1", measured_on=date(2026, 11, 4), weight_kg=84.7))

    result = await DeleteBodyWeightUseCase(repo).execute(DeleteBodyWeightCommand(user_id="u1", measured_on=date(2026, 11, 4)))

    assert result == Success(None)
    assert await repo.list_by_user("u1") == []


async def test_delete_missing_or_foreign_entry_is_not_found(
    record: RecordBodyWeightUseCase, repo: InMemoryBodyWeightRepository
) -> None:
    await record.execute(RecordBodyWeightCommand(user_id="u2", measured_on=date(2026, 11, 4), weight_kg=60.0))

    result = await DeleteBodyWeightUseCase(repo).execute(DeleteBodyWeightCommand(user_id="u1", measured_on=date(2026, 11, 4)))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), BodyWeightEntryNotFoundError)
    assert len(await repo.list_by_user("u2")) == 1
