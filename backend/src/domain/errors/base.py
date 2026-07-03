"""Base domain error hierarchy."""


class DomainError(Exception):
    """Root base class for all domain errors."""
    pass


class TrainingDayError(DomainError):
    """Base class for training day related errors."""
    pass


class WorkoutExerciseError(DomainError):
    """Base class for workout exercise related errors."""
    pass


class SessionError(DomainError):
    """Base class for workout session related errors."""
    pass
