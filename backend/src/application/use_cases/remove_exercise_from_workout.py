"""RemoveExerciseFromWorkoutUseCase — application layer."""
from returns.result import Failure, Result, Success

from backend.src.application.commands import RemoveExerciseFromWorkoutCommand
from backend.src.application.errors import (
    ApplicationError,
    DomainViolationError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.validators import DayOfWeekValidator
from backend.src.domain.errors.training_day_errors import DayNotInWorkoutError
from backend.src.domain.errors.workout_exercise_errors import ExerciseNotFoundInDayError
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutExerciseId, WorkoutId


class RemoveExerciseFromWorkoutUseCase:
    def __init__(self, repo: WorkoutRepository) -> None:
        self._repo = repo

    def execute(self, cmd: RemoveExerciseFromWorkoutCommand) -> Result[None, ApplicationError]:
        # 1. Validate day
        day_result = DayOfWeekValidator.validate(cmd.day_of_week)
        if isinstance(day_result, Failure):
            return day_result

        day = day_result.unwrap()

        # 2. Parse workout_exercise_id
        we_id_result = WorkoutExerciseId.from_string(cmd.workout_exercise_id)
        if isinstance(we_id_result, Failure):
            return Failure(DomainViolationError(
                domain_error=ValueError(cmd.workout_exercise_id),
                message=f"Invalid workout exercise id: {cmd.workout_exercise_id}",
            ))

        we_id = we_id_result.unwrap()

        # 3. Load workout
        workout_id = WorkoutId.from_string(cmd.workout_id).unwrap()
        workout = self._repo.get_by_id(workout_id)
        if workout is None:
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))

        # 4. Authorize
        if workout.user_id != cmd.user_id:
            return Failure(UnauthorizedError(user_id=cmd.user_id, workout_id=cmd.workout_id))

        # 5. Mutate
        try:
            workout.remove_exercise_from_day(day, we_id)
        except (DayNotInWorkoutError, ExerciseNotFoundInDayError) as e:
            return Failure(DomainViolationError(domain_error=e, message=str(e)))

        # 6. Save
        self._repo.save(workout)

        return Success(None)
