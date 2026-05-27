"""WorkoutName frozen dataclass with Result-based factory — domain value object."""
from dataclasses import dataclass
from enum import Enum

from returns.result import Failure, Result, Success


class WorkoutNameError(Enum):
    EMPTY = "EMPTY"
    TOO_SHORT = "TOO_SHORT"
    TOO_LONG = "TOO_LONG"
    LEADING_TRAILING_WHITESPACE = "LEADING_TRAILING_WHITESPACE"
    CONSECUTIVE_SPACES = "CONSECUTIVE_SPACES"


@dataclass(frozen=True)
class WorkoutName:
    value: str

    @classmethod
    def create(cls, raw: str) -> Result["WorkoutName", WorkoutNameError]:
        if not raw or not raw.strip():
            return Failure(WorkoutNameError.EMPTY)
        if raw != raw.strip():
            return Failure(WorkoutNameError.LEADING_TRAILING_WHITESPACE)
        if len(raw) < 2:
            return Failure(WorkoutNameError.TOO_SHORT)
        if len(raw) > 100:
            return Failure(WorkoutNameError.TOO_LONG)
        if "  " in raw:
            return Failure(WorkoutNameError.CONSECUTIVE_SPACES)
        return Success(cls(value=raw))
