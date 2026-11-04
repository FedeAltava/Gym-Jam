"""Unit tests for BodyWeightEntry.record() validation."""
from __future__ import annotations

from datetime import date

from returns.result import Failure, Success

from backend.src.domain.entities.body_weight_entry import BodyWeightEntry, BodyWeightError

TODAY = date(2026, 11, 4)


def test_record_returns_entry_for_valid_weight_and_date() -> None:
    result = BodyWeightEntry.record(user_id="u1", measured_on=TODAY, weight_kg=84.7, latest_allowed=TODAY)

    assert result == Success(BodyWeightEntry(user_id="u1", measured_on=TODAY, weight_kg=84.7))


def test_record_accepts_past_dates_and_the_upper_bound() -> None:
    result = BodyWeightEntry.record(user_id="u1", measured_on=date(2025, 1, 1), weight_kg=400, latest_allowed=TODAY)

    assert isinstance(result, Success)


def test_record_rejects_non_positive_weight() -> None:
    for weight in (0, -1.5):
        result = BodyWeightEntry.record(user_id="u1", measured_on=TODAY, weight_kg=weight, latest_allowed=TODAY)
        assert result == Failure(BodyWeightError.INVALID_WEIGHT)


def test_record_rejects_weight_above_400_kg() -> None:
    result = BodyWeightEntry.record(user_id="u1", measured_on=TODAY, weight_kg=400.1, latest_allowed=TODAY)

    assert result == Failure(BodyWeightError.INVALID_WEIGHT)


def test_record_rejects_dates_after_the_latest_allowed_day() -> None:
    result = BodyWeightEntry.record(user_id="u1", measured_on=date(2026, 11, 5), weight_kg=80, latest_allowed=TODAY)

    assert result == Failure(BodyWeightError.DATE_IN_FUTURE)
