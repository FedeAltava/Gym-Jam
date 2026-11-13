"""Unit tests for the estimated one-rep max rule (Epley) and the record comparison."""
from __future__ import annotations

import pytest

from backend.src.domain.estimated_one_rep_max import beats_record, estimated_one_rep_max


@pytest.mark.parametrize(
    ("weight_kg", "reps", "expected"),
    [
        (80.0, 10, 106.7),  # 80 × (1 + 10/30) ≈ 106.67
        (82.5, 3, 90.8),  # 82.5 × (1 + 3/30) = 90.75
        (80.0, 12, 112.0),  # 80 × (1 + 12/30) = 112
        (80.0, 8, 101.3),  # 80 × (1 + 8/30) ≈ 101.33
        (100.0, 1, 103.3),  # a single rep still adds 1/30
    ],
)
def test_epley_estimate(weight_kg: float, reps: int, expected: float) -> None:
    assert estimated_one_rep_max(weight_kg, reps) == pytest.approx(expected, abs=0.05)


def test_first_record_when_nothing_previous() -> None:
    assert beats_record(106.7, None) is True


def test_strictly_higher_estimate_is_a_record() -> None:
    assert beats_record(estimated_one_rep_max(80.0, 12), estimated_one_rep_max(80.0, 8)) is True


def test_lower_estimate_is_not_a_record() -> None:
    assert beats_record(estimated_one_rep_max(82.5, 3), estimated_one_rep_max(80.0, 10)) is False


def test_tie_after_rounding_to_a_tenth_is_not_a_record() -> None:
    # 106.66 and 106.71 both round to 106.7 kg → a tie, not a record.
    assert beats_record(106.71, 106.66) is False
    assert beats_record(106.7, 106.7) is False
    # One tenth more after rounding is a record.
    assert beats_record(106.76, 106.66) is True
