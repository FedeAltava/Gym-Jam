"""ReorderExercisesUseCase — application layer."""
from returns.result import Failure, Result, Success

from backend.src.application.commands import ReorderExercisesCommand
from backend.src.application.dtos import TrainingDayDTO
from backend.src.application.errors import (
    ApplicationError,
    DomainViolationError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.validators import DayOfWeekValidator
from backend.src.domain.errors.training_day_errors import DayNotInWorkoutError
from backend.src.domain.errors.workout_exercise_errors import ReorderMismatchError
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutExerciseId, WorkoutId


class ReorderExercisesUseCase:
    def __init__(self, repo: WorkoutRepository) -> None:
        self._repo = repo

    def execute(self, cmd: ReorderExercisesCommand) -> Result[TrainingDayDTO, ApplicationError]:
        # 1. Validate day
        day_result = DayOfWeekValidator.validate(cmd.day_of_week)
        if isinstance(day_result, Failure):
            return day_result

        day = day_result.unwrap()

        # 2. Parse ordered_exercise_ids
        ordered_ids: list[WorkoutExerciseId] = []
        for raw_id in cmd.ordered_exercise_ids:
            id_result = WorkoutExerciseId.from_string(raw_id)
            if isinstance(id_result, Failure):
                return Failure(DomainViolationError(
                    domain_error=ValueError(raw_id),
                    message=f"Invalid workout exercise id: {raw_id}",
                ))
            ordered_ids.append(id_result.unwrap())

        # 3. Load workout
        workout_id_result = WorkoutId.from_string(cmd.workout_id)
        if isinstance(workout_id_result, Failure):
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))
        workout_id = workout_id_result.unwrap()
        workout = self._repo.get_by_id(workout_id)
        if workout is None:
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))

        # 4. Authorize
        if workout.user_id != cmd.user_id:
            return Failure(UnauthorizedError(user_id=cmd.user_id, workout_id=cmd.workout_id))

        # 5. Mutate
        try:
            workout.reorder_exercises_in_day(day, ordered_ids)
        except (ReorderMismatchError, DayNotInWorkoutError) as e:
            return Failure(DomainViolationError(domain_error=e, message=str(e)))

        # 6. Save
        self._repo.save(workout)

        # 7. Return DTO
        training_day = workout.get_training_days()[day]
        return Success(TrainingDayDTO.from_entity(training_day))
