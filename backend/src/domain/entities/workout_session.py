"""WorkoutSession aggregate root — owns ExerciseLog children."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from backend.src.domain.entities.exercise_log import ExerciseLog
from backend.src.domain.entities.workout_exercise import WorkoutExercise
from backend.src.domain.errors.session_errors import (
    InvalidRepsCompleted,
    SessionAlreadyCompleted,
    SetAlreadyLogged,
    SetExceedsPlan,
)
from backend.src.domain.value_objects.exercise_log_id import ExerciseLogId
from backend.src.domain.value_objects.training_day_id import TrainingDayId
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

    def log_set(
        self,
        exercise: WorkoutExercise,
        set_number: int,
        reps_completed: int,
        weight_kg: float | None,
    ) -> ExerciseLog:
        if self.completed_at is not None:
            raise SessionAlreadyCompleted()

        if set_number < 1 or set_number > exercise.sets:
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

    def complete(self) -> None:
        if self.completed_at is None:
            self.completed_at = datetime.now(UTC)

    def pull_events(self) -> list:
        return []
