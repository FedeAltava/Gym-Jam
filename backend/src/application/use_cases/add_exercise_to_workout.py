"""AddExerciseToWorkoutUseCase — application layer."""
from returns.result import Failure, Result, Success

from backend.src.application.commands import AddExerciseToWorkoutCommand
from backend.src.application.dtos import WorkoutExerciseDTO
from backend.src.application.errors import (
    ApplicationError,
    DomainViolationError,
    ExerciseNotFoundError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.application.validators import DayOfWeekValidator
from backend.src.domain.errors.training_day_errors import (
    DayNotInWorkoutError,
)
from backend.src.domain.errors.workout_exercise_errors import DuplicateExerciseInDayError
from backend.src.domain.repositories.exercise_repository import ExerciseRepository
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import WorkoutId


class AddExerciseToWorkoutUseCase:
    def __init__(self, repo: WorkoutRepository, exercise_repo: ExerciseRepository) -> None:
        self._repo = repo
        self._exercise_repo = exercise_repo

    async def execute(self, cmd: AddExerciseToWorkoutCommand) -> Result[WorkoutExerciseDTO, ApplicationError]:
        # 1. Validate day
        day_result = DayOfWeekValidator.validate(cmd.day_of_week)
        if isinstance(day_result, Failure):
            return day_result

        day = day_result.unwrap()

        # 2. Load workout
        id_result = WorkoutId.from_string(cmd.workout_id)
        if isinstance(id_result, Failure):
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))
        workout_id = id_result.unwrap()
        workout = await self._repo.get_by_id(workout_id)
        if workout is None:
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))

        # 3. Authorize
        if workout.user_id != cmd.user_id:
            return Failure(UnauthorizedError(user_id=cmd.user_id, workout_id=cmd.workout_id))

        # 4. Validate exercise against the catalog
        if not await self._exercise_repo.exists(cmd.exercise_id):
            return Failure(ExerciseNotFoundError(exercise_id=cmd.exercise_id))

        # 5. Mutate
        try:
            exercise = workout.add_exercise_to_day(
                day,
                cmd.exercise_id,
                sets=cmd.sets,
                reps_per_set=cmd.reps_per_set,
                weight_kg=cmd.weight_kg,
            )
        except (DayNotInWorkoutError, DuplicateExerciseInDayError) as e:
            return Failure(DomainViolationError(domain_error=e, message=str(e)))

        # 6. Save
        await self._repo.save(workout)

        # 7. Return DTO
        return Success(WorkoutExerciseDTO.from_entity(exercise))
