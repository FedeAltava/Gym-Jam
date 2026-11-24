"""Unit tests for treadmill cardio on the WorkoutSession aggregate."""
from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest
from returns.result import Failure, Success

from backend.src.domain.errors.session_errors import CardioEntryNotFound, InvalidCardioEntry
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.value_objects import (
    CardioEntryId,
    TrainingDayId,
    WorkoutId,
    WorkoutSessionId,
)


def _make_session(*, completed_at: datetime | None = None) -> WorkoutSession:
    return WorkoutSession(
        id=WorkoutSessionId.generate(),
        user_id="user-123",
        workout_id=WorkoutId.generate(),
        training_day_id=TrainingDayId.generate(),
        started_at=datetime.now(UTC),
        completed_at=completed_at,
    )


def test_add_cardio_records_every_value() -> None:
    session = _make_session()

    entry = session.add_cardio(
        duration_minutes=20,
        distance_km=2.5,
        speed_kmh=7.5,
        incline_percent=3.5,
        calories=250,
    )

    assert session.cardio == [entry]
    assert entry.session_id == session.id
    assert (entry.duration_minutes, entry.distance_km, entry.speed_kmh, entry.incline_percent, entry.calories) == (
        20,
        2.5,
        7.5,
        3.5,
        250,
    )
    assert entry.created_at.tzinfo is not None


def test_add_cardio_with_a_single_value_leaves_the_rest_empty() -> None:
    session = _make_session()

    entry = session.add_cardio(calories=120)

    assert entry.calories == 120
    assert (entry.duration_minutes, entry.distance_km, entry.speed_kmh, entry.incline_percent) == (
        None,
        None,
        None,
        None,
    )


def test_add_cardio_without_any_value_is_rejected() -> None:
    session = _make_session()

    with pytest.raises(InvalidCardioEntry):
        session.add_cardio()

    assert session.cardio == []


@pytest.mark.parametrize(
    "values",
    [
        {"duration_minutes": 0},
        {"duration_minutes": -5},
        {"duration_minutes": 1441},
        {"distance_km": 0.0},
        {"distance_km": -1.0},
        {"distance_km": math.inf},
        {"speed_kmh": 0.0},
        {"speed_kmh": math.nan},
        {"incline_percent": -0.5},
        {"incline_percent": 40.5},
        {"incline_percent": math.nan},
        {"calories": 0},
        {"calories": 20001},
    ],
)
def test_add_cardio_rejects_out_of_range_values(values: dict) -> None:
    session = _make_session()

    # Valid values alongside the bad one: the bad one alone must reject.
    with pytest.raises(InvalidCardioEntry):
        session.add_cardio(**{"duration_minutes": 20, "calories": 100, **values})

    assert session.cardio == []


@pytest.mark.parametrize("incline", [0.0, 40.0])
def test_add_cardio_accepts_incline_bounds(incline: float) -> None:
    session = _make_session()

    entry = session.add_cardio(incline_percent=incline)

    assert entry.incline_percent == incline


def test_add_cardio_accepts_upper_bounds() -> None:
    session = _make_session()

    entry = session.add_cardio(duration_minutes=1440, calories=20000)

    assert (entry.duration_minutes, entry.calories) == (1440, 20000)


def test_cardio_can_be_added_and_removed_on_a_completed_session() -> None:
    session = _make_session(completed_at=datetime.now(UTC))

    entry = session.add_cardio(duration_minutes=15)
    assert session.cardio == [entry]

    assert session.remove_cardio(entry.id) == Success(None)
    assert session.cardio == []


def test_remove_cardio_keeps_the_other_entries_in_order() -> None:
    session = _make_session()
    first = session.add_cardio(duration_minutes=10)
    second = session.add_cardio(duration_minutes=20)
    third = session.add_cardio(duration_minutes=30)

    session.remove_cardio(second.id)

    assert session.cardio == [first, third]


def test_remove_unknown_cardio_entry_fails() -> None:
    session = _make_session()
    session.add_cardio(duration_minutes=10)

    result = session.remove_cardio(CardioEntryId.generate())

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), CardioEntryNotFound)
    assert len(session.cardio) == 1
