"""DietPlanId frozen dataclass with Result-based factory — domain value object."""
import uuid
from dataclasses import dataclass
from enum import Enum

from returns.result import Failure, Result, Success

_NIL = uuid.UUID(int=0)


class DietPlanIdError(Enum):
    INVALID_FORMAT = "INVALID_FORMAT"
    NIL_UUID = "NIL_UUID"


@dataclass(frozen=True)
class DietPlanId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> "DietPlanId":
        return cls(value=uuid.uuid4())

    @classmethod
    def from_string(cls, raw: str) -> Result["DietPlanId", DietPlanIdError]:
        try:
            parsed = uuid.UUID(raw)
        except ValueError:
            return Failure(DietPlanIdError.INVALID_FORMAT)
        if parsed == _NIL:
            return Failure(DietPlanIdError.NIL_UUID)
        return Success(cls(value=parsed))
