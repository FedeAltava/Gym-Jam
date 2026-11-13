"""Domain read models (projections) — no business logic, no application layer dependency.

These are query-side snapshots used by the session repository port to return
enriched read data without coupling the domain layer to application DTOs.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LastSetSnapshot:
    """The latest logged set with a given set number of a catalog exercise."""

    exercise_id: str
    set_number: int
    reps_completed: int
    weight_kg: float | None


@dataclass(frozen=True)
class SessionLogSnapshot:
    id: str
    workout_exercise_id: str
    # Catalog exercise actually done for this set (a swap replaces the plan's).
    exercise_id: str
    exercise_name: str
    muscle_group: str | None
    set_number: int
    reps_completed: int
    weight_kg: float | None


@dataclass(frozen=True)
class SessionRecordSnapshot:
    """A personal record set in a session: the exact set that holds it."""

    exercise_id: str
    weight_kg: float
    reps: int


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
    # Number of records the session holds; always len(records).
    pr_count: int = 0
    records: tuple[SessionRecordSnapshot, ...] = ()
