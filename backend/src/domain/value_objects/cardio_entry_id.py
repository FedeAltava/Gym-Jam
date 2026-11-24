"""CardioEntryId frozen dataclass with Result-based factory — domain value object."""
import uuid
from dataclasses import dataclass
from enum import Enum

from returns.result import Failure, Result, Success

_NIL = uuid.UUID(int=0)


class CardioEntryIdError(Enum):
    INVALID_FORMAT = "INVALID_FORMAT"
    NIL_UUID = "NIL_UUID"


@dataclass(frozen=True)
class CardioEntryId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> "CardioEntryId":
        return cls(value=uuid.uuid4())

    @classmethod
    def from_string(cls, raw: str) -> Result["CardioEntryId", CardioEntryIdError]:
        try:
            parsed = uuid.UUID(raw)
        except ValueError:
            return Failure(CardioEntryIdError.INVALID_FORMAT)
        if parsed == _NIL:
            return Failure(CardioEntryIdError.NIL_UUID)
        return Success(cls(value=parsed))
