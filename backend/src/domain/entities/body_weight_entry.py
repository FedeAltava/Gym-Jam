"""BodyWeightEntry — one body weight measurement per user and day."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from returns.result import Failure, Result, Success

MAX_WEIGHT_KG = 400.0


class BodyWeightError(Enum):
    INVALID_WEIGHT = "INVALID_WEIGHT"
    DATE_IN_FUTURE = "DATE_IN_FUTURE"


@dataclass(frozen=True)
class BodyWeightEntry:
    # (user_id, measured_on) identifies the entry: recording the same day
    # again replaces its weight.
    user_id: str
    measured_on: date
    weight_kg: float

    @classmethod
    def record(
        cls,
        user_id: str,
        measured_on: date,
        weight_kg: float,
        latest_allowed: date,
    ) -> Result["BodyWeightEntry", BodyWeightError]:
        if not 0 < weight_kg <= MAX_WEIGHT_KG:
            return Failure(BodyWeightError.INVALID_WEIGHT)
        if measured_on > latest_allowed:
            return Failure(BodyWeightError.DATE_IN_FUTURE)
        return Success(cls(user_id=user_id, measured_on=measured_on, weight_kg=weight_kg))
