"""Domain read models (projections) — no business logic, no application layer dependency.

These are query-side snapshots used by the session repository port to return
enriched read data without coupling the domain layer to application DTOs.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SessionLogSnapshot:
    id: str
    workout_exercise_id: str
    exercise_name: str
    muscle_group: str | None
    set_number: int
    reps_completed: int
    weight_kg: float | None


@dataclass(frozen=True)
class SessionSnapshot:
    id: str
    workout_id: str
    training_day_id: str
    workout_name: str
    day_of_week: str
    started_at: datetime
    completed_at: datetime | None
    logs: tuple[SessionLogSnapshot, ...]
    pr_count: int = 0
