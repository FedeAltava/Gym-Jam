"""CardioEntry entity — treadmill cardio recorded within a WorkoutSession."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

from backend.src.domain.errors.session_errors import InvalidCardioEntry
from backend.src.domain.value_objects.cardio_entry_id import CardioEntryId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId

# Upper bounds catch typos (and keep integers inside the DB column range).
MAX_DURATION_MINUTES = 1440
MAX_CALORIES = 20000
MAX_INCLINE_PERCENT = 40.0


def _check_positive(name: str, value: float | None, maximum: float | None = None) -> None:
    if value is None:
        return
    if not math.isfinite(value) or value <= 0:
        raise InvalidCardioEntry(f"{name} must be greater than 0.")
    if maximum is not None and value > maximum:
        raise InvalidCardioEntry(f"{name} must be at most {maximum:g}.")


@dataclass(frozen=True, eq=False)
class CardioEntry:
    # Always treadmill cardio: every value is optional, but at least one is set.
    id: CardioEntryId
    session_id: WorkoutSessionId
    duration_minutes: int | None
    distance_km: float | None
    speed_kmh: float | None
    incline_percent: float | None
    calories: int | None
    created_at: datetime

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CardioEntry):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def record(
        cls,
        session_id: WorkoutSessionId,
        *,
        duration_minutes: int | None = None,
        distance_km: float | None = None,
        speed_kmh: float | None = None,
        incline_percent: float | None = None,
        calories: int | None = None,
    ) -> CardioEntry:
        values = (duration_minutes, distance_km, speed_kmh, incline_percent, calories)
        if all(value is None for value in values):
            raise InvalidCardioEntry("Fill in at least one cardio value.")
        _check_positive("duration_minutes", duration_minutes, MAX_DURATION_MINUTES)
        _check_positive("distance_km", distance_km)
        _check_positive("speed_kmh", speed_kmh)
        _check_positive("calories", calories, MAX_CALORIES)
        if incline_percent is not None and not (
            math.isfinite(incline_percent) and 0 <= incline_percent <= MAX_INCLINE_PERCENT
        ):
            raise InvalidCardioEntry(f"incline_percent must be between 0 and {MAX_INCLINE_PERCENT:g}.")
        return cls(
            id=CardioEntryId.generate(),
            session_id=session_id,
            duration_minutes=duration_minutes,
            distance_km=distance_km,
            speed_kmh=speed_kmh,
            incline_percent=incline_percent,
            calories=calories,
            created_at=datetime.now(UTC),
        )
