"""Workout domain events — FASE 3."""
from __future__ import annotations

from dataclasses import dataclass

from backend.src.domain.events.base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class WorkoutCreatedEvent(DomainEvent):
    workout_id: str
    user_id: str
    name: str
    training_days: list[str]  # DayOfWeek.value strings
