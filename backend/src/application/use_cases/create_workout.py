"""CreateWorkoutUseCase — application layer."""
from returns.result import Failure, Result, Success

from backend.src.application.commands import CreateWorkoutCommand
from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.application.errors import ApplicationError, InvalidWorkoutNameError
from backend.src.application.validators import DayOfWeekValidator
from backend.src.domain.aggregates.workout import Workout
from backend.src.domain.repositories.workout_repository import WorkoutRepository


class CreateWorkoutUseCase:
    def __init__(self, repo: WorkoutRepository) -> None:
        self._repo = repo

    def execute(self, cmd: CreateWorkoutCommand) -> Result[WorkoutWithDaysDTO, ApplicationError]:
        # 1. Validate name is not empty/whitespace
        if not cmd.name or not cmd.name.strip():
            return Failure(InvalidWorkoutNameError(reason="Name cannot be empty or whitespace."))

        # 2. Validate and parse training_days strings
        days = []
        for day_str in cmd.training_days:
            day_result = DayOfWeekValidator.validate(day_str)
            if isinstance(day_result, Failure):
                return day_result
            days.append(day_result.unwrap())

        # 3. Create workout aggregate
        workout_result = Workout.create(
            user_id=cmd.user_id,
            name=cmd.name,
            description=cmd.description,
            training_days=days,
        )
        if isinstance(workout_result, Failure):
            return Failure(InvalidWorkoutNameError(reason=str(workout_result.failure())))

        workout = workout_result.unwrap()

        # 4. Save
        self._repo.save(workout)

        # 5. Return DTO
        return Success(WorkoutWithDaysDTO.from_aggregate(workout))
