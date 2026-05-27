"""Tests for domain events — FASE 2."""
import uuid
from datetime import datetime

import pytest

from backend.src.domain.events.base import DomainEvent
from backend.src.domain.events.training_day_events import (
    ExerciseAddedToDayEvent,
    ExerciseRemovedFromDayEvent,
    TrainingDayAddedEvent,
    TrainingDayRemovedEvent,
)


# ── DomainEvent base ─────────────────────────────────────────────────────────


def test_domain_event_auto_generates_event_id() -> None:
    """Concrete subclass gets a UUID event_id automatically."""
    event = TrainingDayAddedEvent(
        training_day_id="td-001",
        workout_id="w-001",
        day="Monday",
    )
    assert isinstance(event.event_id, uuid.UUID)


def test_domain_event_auto_generates_occurred_at() -> None:
    event = TrainingDayAddedEvent(
        training_day_id="td-001",
        workout_id="w-001",
        day="Monday",
    )
    assert isinstance(event.occurred_at, datetime)
    assert event.occurred_at.tzinfo is not None  # timezone-aware


def test_domain_event_ids_are_unique_per_instance() -> None:
    e1 = TrainingDayAddedEvent(training_day_id="td-001", workout_id="w-001", day="Monday")
    e2 = TrainingDayAddedEvent(training_day_id="td-001", workout_id="w-001", day="Monday")
    assert e1.event_id != e2.event_id


def test_domain_event_is_immutable() -> None:
    event = TrainingDayAddedEvent(training_day_id="td-001", workout_id="w-001", day="Monday")
    with pytest.raises((AttributeError, TypeError)):
        event.training_day_id = "other"  # type: ignore[misc]


# ── TrainingDayAddedEvent ────────────────────────────────────────────────────


def test_training_day_added_event_fields() -> None:
    event = TrainingDayAddedEvent(
        training_day_id="td-001",
        workout_id="w-001",
        day="Monday",
    )
    assert event.training_day_id == "td-001"
    assert event.workout_id == "w-001"
    assert event.day == "Monday"


# ── TrainingDayRemovedEvent ──────────────────────────────────────────────────


def test_training_day_removed_event_fields() -> None:
    event = TrainingDayRemovedEvent(
        training_day_id="td-002",
        workout_id="w-001",
        day="Tuesday",
    )
    assert event.training_day_id == "td-002"
    assert event.workout_id == "w-001"
    assert event.day == "Tuesday"


# ── ExerciseAddedToDayEvent ──────────────────────────────────────────────────


def test_exercise_added_to_day_event_fields() -> None:
    event = ExerciseAddedToDayEvent(
        training_day_id="td-001",
        workout_exercise_id="we-001",
        exercise_id="ex-001",
        order=1,
    )
    assert event.training_day_id == "td-001"
    assert event.workout_exercise_id == "we-001"
    assert event.exercise_id == "ex-001"
    assert event.order == 1


def test_exercise_added_to_day_event_different_order() -> None:
    event = ExerciseAddedToDayEvent(
        training_day_id="td-001",
        workout_exercise_id="we-002",
        exercise_id="ex-002",
        order=3,
    )
    assert event.order == 3


# ── ExerciseRemovedFromDayEvent ──────────────────────────────────────────────


def test_exercise_removed_from_day_event_fields() -> None:
    event = ExerciseRemovedFromDayEvent(
        training_day_id="td-001",
        workout_exercise_id="we-001",
        exercise_id="ex-001",
    )
    assert event.training_day_id == "td-001"
    assert event.workout_exercise_id == "we-001"
    assert event.exercise_id == "ex-001"
