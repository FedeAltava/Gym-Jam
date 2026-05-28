from returns.result import Failure, Result, Success

from backend.src.application.errors import InvalidDayOfWeekError, InvalidWorkoutNameError
from backend.src.domain.value_objects import DayOfWeek
from backend.src.domain.value_objects.workout_name import WorkoutName


class DayOfWeekValidator:
    @staticmethod
    def validate(value: str) -> Result[DayOfWeek, InvalidDayOfWeekError]:
        try:
            return Success(DayOfWeek(value.upper()))
        except ValueError:
            return Failure(InvalidDayOfWeekError(value=value))


class CreateWorkoutValidator:
    @staticmethod
    def validate_name(value: str) -> Result[str, InvalidWorkoutNameError]:
        result = WorkoutName.create(value)
        if isinstance(result, Failure):
            error = result.failure()
            reason = error.value if hasattr(error, "value") else str(error)
            return Failure(InvalidWorkoutNameError(reason=reason))
        return Success(value)
