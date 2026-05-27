"""TrainingDay entity — aggregate root managing WorkoutExercise children."""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.errors.workout_exercise_errors import (
    DuplicateExerciseInDayError,
    ExerciseNotFoundInDayError,
    ReorderMismatchError,
)
from backend.src.domain.events.base import DomainEvent
from backend.src.domain.events.training_day_events import (
    ExerciseAddedToDayEvent,
    ExerciseRemovedFromDayEvent,
)
from backend.src.domain.value_objects import (
    DayOfWeek,
    TrainingDayId,
    WorkoutExerciseId,
    WorkoutId,
)


@dataclass(eq=False)
class TrainingDay:
    id: TrainingDayId
    workout_id: WorkoutId
    day: DayOfWeek
    _exercises: list[WorkoutExercise] = field(default_factory=list, repr=False)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TrainingDay):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def exercises(self) -> list[WorkoutExercise]:
        return sorted(self._exercises, key=lambda e: e.order)

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    def add_exercise(
        self,
        exercise_id: str,
        workout_exercise_id: WorkoutExerciseId | None = None,
    ) -> WorkoutExercise:
        for ex in self._exercises:
            if ex.exercise_id == exercise_id:
                raise DuplicateExerciseInDayError(exercise_id=exercise_id, day=self.day.value)
        ex_id = workout_exercise_id or WorkoutExerciseId.generate()
        order = len(self._exercises) + 1
        exercise = WorkoutExercise(
            id=ex_id,
            workout_id=self.workout_id,
            day=self.day,
            exercise_id=exercise_id,
            order=order,
        )
        self._exercises.append(exercise)
        self._events.append(
            ExerciseAddedToDayEvent(
                training_day_id=str(self.id.value),
                workout_exercise_id=str(ex_id.value),
                exercise_id=exercise_id,
                order=order,
            )
        )
        return exercise

    def remove_exercise(self, workout_exercise_id: WorkoutExerciseId) -> None:
        for i, ex in enumerate(self._exercises):
            if ex.id == workout_exercise_id:
                exercise_id = ex.exercise_id
                self._exercises.pop(i)
                self._events.append(
                    ExerciseRemovedFromDayEvent(
                        training_day_id=str(self.id.value),
                        workout_exercise_id=str(workout_exercise_id.value),
                        exercise_id=exercise_id,
                    )
                )
                return
        raise ExerciseNotFoundInDayError(workout_exercise_id=str(workout_exercise_id.value))

    def reorder_exercises(self, ordered_ids: list[WorkoutExerciseId]) -> None:
        existing = {ex.id for ex in self._exercises}
        provided = set(ordered_ids)
        if provided != existing:
            raise ReorderMismatchError(
                missing=existing - provided,
                extra=provided - existing,
            )
        for pos, ex_id in enumerate(ordered_ids, start=1):
            ex = next(e for e in self._exercises if e.id == ex_id)
            ex.order = pos
