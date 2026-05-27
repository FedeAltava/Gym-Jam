"""Training day domain events."""
from dataclasses import dataclass

from backend.src.domain.events.base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class TrainingDayAddedEvent(DomainEvent):
    training_day_id: str
    workout_id: str
    day: str


@dataclass(frozen=True, kw_only=True)
class TrainingDayRemovedEvent(DomainEvent):
    training_day_id: str
    workout_id: str
    day: str


@dataclass(frozen=True, kw_only=True)
class ExerciseAddedToDayEvent(DomainEvent):
    training_day_id: str
    workout_exercise_id: str
    exercise_id: str
    order: int


@dataclass(frozen=True, kw_only=True)
class ExerciseRemovedFromDayEvent(DomainEvent):
    training_day_id: str
    workout_exercise_id: str
    exercise_id: str
