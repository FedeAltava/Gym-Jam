"""Tests for WorkoutCreatedEvent — FASE 3, Slice 1."""
import dataclasses
import uuid
from datetime import datetime

import pytest

from backend.src.domain.events.workout_events import WorkoutCreatedEvent


def test_workout_created_event_auto_generates_event_id() -> None:
    """Each instance gets a unique UUID event_id from DomainEvent base."""
    e1 = WorkoutCreatedEvent(
        workout_id="w-001",
        user_id="u-001",
        name="Push Day",
        training_days=["Monday", "Thursday"],
    )
    e2 = WorkoutCreatedEvent(
        workout_id="w-002",
        user_id="u-001",
        name="Pull Day",
        training_days=["Tuesday"],
    )
    assert isinstance(e1.event_id, uuid.UUID)
    assert isinstance(e2.event_id, uuid.UUID)
    assert e1.event_id != e2.event_id


def test_workout_created_event_auto_sets_occurred_at() -> None:
    """occurred_at is set automatically to a timezone-aware datetime."""
    event = WorkoutCreatedEvent(
        workout_id="w-001",
        user_id="u-001",
        name="Push Day",
        training_days=["Monday"],
    )
    assert isinstance(event.occurred_at, datetime)
    assert event.occurred_at.tzinfo is not None


def test_workout_created_event_stores_payload_fields() -> None:
    """All domain payload fields are stored and accessible."""
    event = WorkoutCreatedEvent(
        workout_id="w-123",
        user_id="u-456",
        name="Leg Day",
        training_days=["Wednesday", "Saturday"],
    )
    assert event.workout_id == "w-123"
    assert event.user_id == "u-456"
    assert event.name == "Leg Day"
    assert event.training_days == ["Wednesday", "Saturday"]


def test_workout_created_event_is_frozen() -> None:
    """WorkoutCreatedEvent is immutable — mutation raises an error."""
    event = WorkoutCreatedEvent(
        workout_id="w-001",
        user_id="u-001",
        name="Push Day",
        training_days=["Monday"],
    )
    with pytest.raises((AttributeError, TypeError)):
        event.workout_id = "w-999"  # type: ignore[misc]


def test_workout_created_event_training_days_is_list_of_strings() -> None:
    """training_days holds a list of DayOfWeek.value strings."""
    event = WorkoutCreatedEvent(
        workout_id="w-001",
        user_id="u-001",
        name="Full Body",
        training_days=["Monday", "Wednesday", "Friday"],
    )
    assert isinstance(event.training_days, list)
    assert all(isinstance(day, str) for day in event.training_days)
    assert len(event.training_days) == 3
