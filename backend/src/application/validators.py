from returns.result import Failure, Result, Success

from backend.src.application.errors import InvalidDayOfWeekError
from backend.src.domain.value_objects import DayOfWeek


class DayOfWeekValidator:
    @staticmethod
    def validate(value: str) -> Result[DayOfWeek, InvalidDayOfWeekError]:
        try:
            return Success(DayOfWeek(value.upper()))
        except ValueError:
            return Failure(InvalidDayOfWeekError(value=value))
