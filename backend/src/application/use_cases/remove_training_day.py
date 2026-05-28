"""RemoveTrainingDayUseCase — application layer."""
from returns.result import Failure, Result, Success

from backend.src.application.commands import RemoveTrainingDayCommand
from backend.src.application.errors import (
    ApplicationError,
    DomainViolationError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.validators import DayOfWeekValidator
from backend.src.domain.errors.training_day_errors import (
    CannotRemoveDayWithExercisesError,
    DayNotInWorkoutError,
)
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutId


class RemoveTrainingDayUseCase:
    def __init__(self, repo: WorkoutRepository) -> None:
        self._repo = repo

    def execute(self, cmd: RemoveTrainingDayCommand) -> Result[None, ApplicationError]:
        # 1. Validate day
        day_result = DayOfWeekValidator.validate(cmd.day_of_week)
        if isinstance(day_result, Failure):
            return day_result

        day = day_result.unwrap()

        # 2. Load workout
        workout_id = WorkoutId.from_string(cmd.workout_id).unwrap()
        workout = self._repo.get_by_id(workout_id)
        if workout is None:
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))

        # 3. Authorize
        if workout.user_id != cmd.user_id:
            return Failure(UnauthorizedError(user_id=cmd.user_id, workout_id=cmd.workout_id))

        # 4. Mutate
        try:
            workout.remove_training_day(day)
        except (DayNotInWorkoutError, CannotRemoveDayWithExercisesError) as e:
            return Failure(DomainViolationError(domain_error=e, message=str(e)))

        # 5. Save
        self._repo.save(workout)

        return Success(None)
