"""WorkoutId frozen dataclass with Result-based factory — domain value object."""
import uuid
from dataclasses import dataclass
from enum import Enum

from returns.result import Failure, Result, Success

_NIL = uuid.UUID(int=0)


class WorkoutIdError(Enum):
    INVALID_FORMAT = "INVALID_FORMAT"
    NIL_UUID = "NIL_UUID"


@dataclass(frozen=True)
class WorkoutId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> "WorkoutId":
        return cls(value=uuid.uuid4())

    @classmethod
    def from_string(cls, raw: str) -> Result["WorkoutId", WorkoutIdError]:
        try:
            parsed = uuid.UUID(raw)
        except ValueError:
            return Failure(WorkoutIdError.INVALID_FORMAT)
        if parsed == _NIL:
            return Failure(WorkoutIdError.NIL_UUID)
        return Success(cls(value=parsed))
