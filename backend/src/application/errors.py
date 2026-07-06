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
        super().__init__(f"Workout '{workout_id}' not found.")


@dataclass
class UnauthorizedError(ApplicationError):
    user_id: str
    workout_id: str

    def __init__(self, user_id: str, workout_id: str) -> None:
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "workout_id", workout_id)
        super().__init__(f"User '{user_id}' is not authorized to access workout '{workout_id}'.")


@dataclass
class ExerciseNotFoundError(ApplicationError):
    exercise_id: str

    def __init__(self, exercise_id: str) -> None:
        object.__setattr__(self, "exercise_id", exercise_id)
        super().__init__(f"Exercise '{exercise_id}' not found.")


@dataclass
class InvalidDayOfWeekError(ApplicationError):
    value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "value", value)
        super().__init__(f"Invalid day of week: '{value}'.")


@dataclass
class InvalidWorkoutNameError(ApplicationError):
    reason: str

    def __init__(self, reason: str) -> None:
        object.__setattr__(self, "reason", reason)
        super().__init__(reason)


@dataclass
class DomainViolationError(ApplicationError):
    domain_error: Exception
    message: str

    def __init__(self, domain_error: Exception, message: str) -> None:
        object.__setattr__(self, "domain_error", domain_error)
        object.__setattr__(self, "message", message)
        super().__init__(message)


@dataclass
class InvalidCredentialsError(ApplicationError):
    message: str = "Invalid credentials"

    def __init__(self, message: str = "Invalid credentials") -> None:
        object.__setattr__(self, "message", message)
        super().__init__(message)


@dataclass
class InvalidRefreshTokenError(ApplicationError):
    message: str = "Invalid refresh token"

    def __init__(self, message: str = "Invalid refresh token") -> None:
        object.__setattr__(self, "message", message)
        super().__init__(message)


@dataclass
class EmailAlreadyExistsError(ApplicationError):
    email: str
    message: str = "Email already registered"

    def __init__(self, email: str, message: str = "Email already registered") -> None:
        object.__setattr__(self, "email", email)
        object.__setattr__(self, "message", message)
        super().__init__(message)


@dataclass
class SessionNotFoundError(ApplicationError):
    session_id: str

    def __init__(self, session_id: str) -> None:
        object.__setattr__(self, "session_id", session_id)
        super().__init__(f"Session '{session_id}' not found.")


@dataclass
class LogNotFoundError(ApplicationError):
    log_id: str

    def __init__(self, log_id: str) -> None:
        object.__setattr__(self, "log_id", log_id)
        super().__init__(f"Log '{log_id}' not found.")


@dataclass
class SessionAlreadyCompletedError(ApplicationError):
    session_id: str

    def __init__(self, session_id: str) -> None:
        object.__setattr__(self, "session_id", session_id)
        super().__init__(f"Session '{session_id}' is already completed.")


@dataclass
class SetExceedsPlanError(ApplicationError):
    set_number: int
    max_sets: int

    def __init__(self, set_number: int, max_sets: int) -> None:
        object.__setattr__(self, "set_number", set_number)
        object.__setattr__(self, "max_sets", max_sets)
        super().__init__(f"Set {set_number} exceeds the planned maximum of {max_sets} sets.")


@dataclass
class SetAlreadyLoggedError(ApplicationError):
    workout_exercise_id: str
    set_number: int

    def __init__(self, workout_exercise_id: str, set_number: int) -> None:
        object.__setattr__(self, "workout_exercise_id", workout_exercise_id)
        object.__setattr__(self, "set_number", set_number)
        super().__init__(f"Set {set_number} for exercise '{workout_exercise_id}' has already been logged.")
