from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationError:
    pass


@dataclass(frozen=True)
class WorkoutNotFoundError(ApplicationError):
    workout_id: str


@dataclass(frozen=True)
class UnauthorizedError(ApplicationError):
    user_id: str
    workout_id: str


@dataclass(frozen=True)
class InvalidDayOfWeekError(ApplicationError):
    value: str


@dataclass(frozen=True)
class InvalidWorkoutNameError(ApplicationError):
    reason: str


@dataclass(frozen=True)
class DomainViolationError(ApplicationError):
    domain_error: Exception
    message: str
