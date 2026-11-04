"""WorkoutSession aggregate root — owns ExerciseLog children."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from returns.result import Failure, Result, Success

from backend.src.domain.entities.exercise_log import ExerciseLog
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.errors.session_errors import (
    ExerciseHasLoggedSets,
    InvalidRepsCompleted,
    LogNotFound,
    SessionAlreadyCompleted,
    SetAlreadyLogged,
    SetExceedsPlan,
)
from backend.src.domain.value_objects.exercise_log_id import ExerciseLogId
from backend.src.domain.value_objects.training_day_id import TrainingDayId
from backend.src.domain.value_objects.workout_exercise_id import WorkoutExerciseId
from backend.src.domain.value_objects.workout_id import WorkoutId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


@dataclass(eq=False)
class WorkoutSession:
    id: WorkoutSessionId
    user_id: str
    workout_id: WorkoutId
    training_day_id: TrainingDayId
    started_at: datetime
    completed_at: datetime | None = field(default=None)
    _logs: list[ExerciseLog] = field(default_factory=list, repr=False)
    # Planned slot -> catalog exercise done instead, for this session only.
    _swaps: dict[WorkoutExerciseId, str] = field(default_factory=dict, repr=False)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WorkoutSession):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def status(self) -> str:
        return "completed" if self.completed_at is not None else "in_progress"

    @property
    def logs(self) -> list[ExerciseLog]:
        return list(self._logs)

    @property
    def swaps(self) -> dict[WorkoutExerciseId, str]:
        return dict(self._swaps)

    def log_set(
        self,
        exercise: WorkoutExercise,
        set_number: int,
        reps_completed: int,
        weight_kg: float | None,
    ) -> ExerciseLog:
        if self.completed_at is not None:
            raise SessionAlreadyCompleted()

        if set_number < 1:
            raise SetExceedsPlan(set_number=set_number, max_sets=exercise.sets)

        if reps_completed < 1:
            raise InvalidRepsCompleted(reps=reps_completed)

        for existing_log in self._logs:
            if (
                existing_log.workout_exercise_id == exercise.id
                and existing_log.set_number == set_number
            ):
                raise SetAlreadyLogged(
                    workout_exercise_id=str(exercise.id.value),
                    set_number=set_number,
                )

        log = ExerciseLog(
            id=ExerciseLogId.generate(),
            session_id=self.id,
            workout_exercise_id=exercise.id,
            set_number=set_number,
            reps_completed=reps_completed,
            weight_kg=weight_kg,
        )
        self._logs.append(log)
        return log

    def remove_log(self, log_id: ExerciseLogId) -> Result[None, LogNotFound]:
        # No completed-session guard on purpose: log edits on completed
        # sessions are allowed (consistent with UpdateExerciseLogUseCase).
        log = next((entry for entry in self._logs if entry.id == log_id), None)
        if log is None:
            return Failure(LogNotFound(log_id=str(log_id.value)))
        self._logs.remove(log)
        return Success(None)

    def swap_exercise(self, exercise: WorkoutExercise, exercise_id: str) -> None:
        """Do `exercise_id` instead of the planned exercise in this session.

        Swapping back to the planned exercise removes the swap. Logged sets
        would silently change exercise, so a slot with sets cannot be swapped.
        """
        if self.completed_at is not None:
            raise SessionAlreadyCompleted()

        if any(log.workout_exercise_id == exercise.id for log in self._logs):
            raise ExerciseHasLoggedSets(workout_exercise_id=str(exercise.id.value))

        if exercise_id == exercise.exercise_id:
            self._swaps.pop(exercise.id, None)
        else:
            self._swaps[exercise.id] = exercise_id

    def complete(self) -> None:
        if self.completed_at is None:
            self.completed_at = datetime.now(UTC)
