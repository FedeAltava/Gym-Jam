"""Workout aggregate root — FASE 3."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from returns.result import Failure, Result, Success

from backend.src.domain.entities.training_day import TrainingDay
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.errors.training_day_errors import (
    CannotRemoveDayWithExercisesError,
    DayAlreadyInWorkoutError,
    DayNotInWorkoutError,
)
from backend.src.domain.events.base import DomainEvent
from backend.src.domain.events.training_day_events import (
    TrainingDayAddedEvent,
    TrainingDayRemovedEvent,
)
from backend.src.domain.events.workout_events import WorkoutCreatedEvent
from backend.src.domain.value_objects import (
    DayOfWeek,
    TrainingDayId,
    WorkoutExerciseId,
    WorkoutId,
    WorkoutName,
    WorkoutNameError,
)


@dataclass(eq=False)
class Workout:
    id: WorkoutId
    user_id: str
    name: WorkoutName
    description: str | None
    is_active: bool
    created_at: datetime
    _training_days: dict[DayOfWeek, TrainingDay] = field(default_factory=dict, repr=False)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Workout):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def create(
        cls,
        user_id: str,
        name: str,
        description: str | None = None,
        training_days: list[DayOfWeek] | None = None,
        workout_id: WorkoutId | None = None,
        created_at: datetime | None = None,
    ) -> Result["Workout", WorkoutNameError]:
        name_result = WorkoutName.create(name)
        if isinstance(name_result, Failure):
            return name_result

        wid = workout_id or WorkoutId.generate()
        now = created_at or datetime.now(UTC)
        days = training_days or []

        td_dict: dict[DayOfWeek, TrainingDay] = {}
        for day in days:
            td_dict[day] = TrainingDay(
                id=TrainingDayId.generate(),
                workout_id=wid,
                day=day,
            )

        workout = cls(
            id=wid,
            user_id=user_id,
            name=name_result.unwrap(),
            description=description,
            is_active=True,
            created_at=now,
            _training_days=td_dict,
            _events=[],
        )
        workout._events.append(
            WorkoutCreatedEvent(
                workout_id=str(wid.value),
                user_id=user_id,
                name=name,
                training_days=[d.value for d in days],
            )
        )
        return Success(workout)

    def add_training_day(self, day: DayOfWeek) -> None:
        if day in self._training_days:
            raise DayAlreadyInWorkoutError(day=day.value, workout_id=str(self.id.value))
        td = TrainingDay(id=TrainingDayId.generate(), workout_id=self.id, day=day)
        self._training_days[day] = td
        self._events.append(
            TrainingDayAddedEvent(
                training_day_id=str(td.id.value),
                workout_id=str(self.id.value),
                day=day.value,
            )
        )

    def remove_training_day(self, day: DayOfWeek) -> None:
        if day not in self._training_days:
            raise DayNotInWorkoutError(day=day.value, workout_id=str(self.id.value))
        td = self._training_days[day]
        if td.exercises:
            raise CannotRemoveDayWithExercisesError(day=day.value, exercise_count=len(td.exercises))
        del self._training_days[day]
        self._events.append(
            TrainingDayRemovedEvent(
                training_day_id=str(td.id.value),
                workout_id=str(self.id.value),
                day=day.value,
            )
        )

    def add_exercise_to_day(
        self,
        day: DayOfWeek,
        exercise_id: str,
        workout_exercise_id: WorkoutExerciseId | None = None,
    ) -> WorkoutExercise:
        if day not in self._training_days:
            raise DayNotInWorkoutError(day=day.value, workout_id=str(self.id.value))
        return self._training_days[day].add_exercise(exercise_id, workout_exercise_id)

    def remove_exercise_from_day(self, day: DayOfWeek, workout_exercise_id: WorkoutExerciseId) -> None:
        if day not in self._training_days:
            raise DayNotInWorkoutError(day=day.value, workout_id=str(self.id.value))
        self._training_days[day].remove_exercise(workout_exercise_id)

    def reorder_exercises_in_day(self, day: DayOfWeek, ordered_ids: list[WorkoutExerciseId]) -> None:
        if day not in self._training_days:
            raise DayNotInWorkoutError(day=day.value, workout_id=str(self.id.value))
        self._training_days[day].reorder_exercises(ordered_ids)

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    def get_exercises_for_day(self, day: DayOfWeek) -> list[WorkoutExercise]:
        if day not in self._training_days:
            raise DayNotInWorkoutError(day=day.value, workout_id=str(self.id.value))
        return self._training_days[day].exercises

    def get_training_days(self) -> dict[DayOfWeek, TrainingDay]:
        return dict(self._training_days)

    def get_training_days_list(self) -> list[DayOfWeek]:
        return list(self._training_days.keys())

    def pull_events(self) -> list[DomainEvent]:
        events: list[DomainEvent] = list(self._events)
        self._events.clear()
        for td in self._training_days.values():
            events.extend(td.pull_events())
        return events
