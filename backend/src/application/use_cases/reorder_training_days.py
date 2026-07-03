"""ReorderTrainingDaysUseCase — application layer."""
from returns.result import Failure, Result, Success

from backend.src.application.commands import ReorderTrainingDaysCommand
from backend.src.application.dtos import WorkoutWithDaysDTO
from backend.src.application.errors import (
    ApplicationError,
    DomainViolationError,
    UnauthorizedError,
    WorkoutNotFoundError,
)
from backend.src.domain.errors.workout_exercise_errors import ReorderMismatchError
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.value_objects import TrainingDayId, WorkoutId


class ReorderTrainingDaysUseCase:
    def __init__(self, repo: WorkoutRepository) -> None:
        self._repo = repo

    async def execute(
        self, cmd: ReorderTrainingDaysCommand
    ) -> Result[WorkoutWithDaysDTO, ApplicationError]:
        # 1. Parse workout id
        workout_id_result = WorkoutId.from_string(cmd.workout_id)
        if isinstance(workout_id_result, Failure):
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))
        workout_id = workout_id_result.unwrap()

        # 2. Load workout
        workout = await self._repo.get_by_id(workout_id)
        if workout is None:
            return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))

        # 3. Authorize
        if workout.user_id != cmd.user_id:
            return Failure(UnauthorizedError(user_id=cmd.user_id, workout_id=cmd.workout_id))

        # 4. Parse ordered day ids
        ordered_ids: list[TrainingDayId] = []
        for raw_id in cmd.ordered_day_ids:
            id_result = TrainingDayId.from_string(raw_id)
            if isinstance(id_result, Failure):
                return Failure(WorkoutNotFoundError(workout_id=cmd.workout_id))
            ordered_ids.append(id_result.unwrap())

        # 5. Mutate
        try:
            workout.reorder_training_days(ordered_ids)
        except ReorderMismatchError as e:
            return Failure(DomainViolationError(domain_error=e, message=str(e)))

        # 6. Save
        await self._repo.save(workout)

        # 7. Return full workout DTO (reordering changes the whole workout shape)
        return Success(WorkoutWithDaysDTO.from_aggregate(workout))
