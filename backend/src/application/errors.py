from dataclasses import dataclass, FrozenInstanceError


class ApplicationError(Exception):
    """Base class for all application-layer errors.

    Behaves like a frozen dataclass (fields cannot be mutated after __init__)
    while remaining a proper Exception (Python can set __traceback__ etc.).
    """

    def __setattr__(self, name: str, value: object) -> None:
        # Allow Python's exception bookkeeping attributes
        if name in ("__traceback__", "__cause__", "__context__", "__suppress_context__"):
            object.__setattr__(self, name, value)
        else:
            raise FrozenInstanceError("cannot assign to field " + repr(name))

    def __delattr__(self, name: str) -> None:
        raise FrozenInstanceError("cannot delete field " + repr(name))


def _frozen_init_setattr(self: object, name: str, value: object) -> None:
    """Used by dataclass __init__ to bypass the FrozenInstanceError guard."""
    object.__setattr__(self, name, value)


@dataclass
class WorkoutNotFoundError(ApplicationError):
    workout_id: str

    def __init__(self, workout_id: str) -> None:
        object.__setattr__(self, "workout_id", workout_id)


@dataclass
class UnauthorizedError(ApplicationError):
    user_id: str
    workout_id: str

    def __init__(self, user_id: str, workout_id: str) -> None:
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "workout_id", workout_id)


@dataclass
class InvalidDayOfWeekError(ApplicationError):
    value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "value", value)


@dataclass
class InvalidWorkoutNameError(ApplicationError):
    reason: str

    def __init__(self, reason: str) -> None:
        object.__setattr__(self, "reason", reason)


@dataclass
class DomainViolationError(ApplicationError):
    domain_error: Exception
    message: str

    def __init__(self, domain_error: Exception, message: str) -> None:
        object.__setattr__(self, "domain_error", domain_error)
        object.__setattr__(self, "message", message)


@dataclass
class InvalidCredentialsError(ApplicationError):
    message: str = "Invalid credentials"

    def __init__(self, message: str = "Invalid credentials") -> None:
        object.__setattr__(self, "message", message)


@dataclass
class EmailAlreadyExistsError(ApplicationError):
    email: str
    message: str = "Email already registered"

    def __init__(self, email: str, message: str = "Email already registered") -> None:
        object.__setattr__(self, "email", email)
        object.__setattr__(self, "message", message)
