from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.src.infrastructure.database import get_session
from backend.src.infrastructure.persistence.workout_repository import SqlAlchemyWorkoutRepository
from backend.src.application.use_cases.create_workout import CreateWorkoutUseCase
from backend.src.application.use_cases.add_training_day import AddTrainingDayUseCase
from backend.src.application.use_cases.remove_training_day import RemoveTrainingDayUseCase
from backend.src.application.use_cases.add_exercise_to_workout import AddExerciseToWorkoutUseCase
from backend.src.application.use_cases.remove_exercise_from_workout import RemoveExerciseFromWorkoutUseCase
from backend.src.application.use_cases.reorder_exercises import ReorderExercisesUseCase
from backend.src.application.use_cases.get_workout_with_days import GetWorkoutWithDaysUseCase
from backend.src.application.use_cases.get_workouts_by_user import GetWorkoutsByUserUseCase


def get_current_user_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


def get_workout_repository(session: AsyncSession = Depends(get_session)) -> SqlAlchemyWorkoutRepository:
    return SqlAlchemyWorkoutRepository(session)


def get_create_workout_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> CreateWorkoutUseCase:
    return CreateWorkoutUseCase(repo)


def get_add_training_day_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> AddTrainingDayUseCase:
    return AddTrainingDayUseCase(repo)


def get_remove_training_day_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> RemoveTrainingDayUseCase:
    return RemoveTrainingDayUseCase(repo)


def get_add_exercise_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> AddExerciseToWorkoutUseCase:
    return AddExerciseToWorkoutUseCase(repo)


def get_remove_exercise_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> RemoveExerciseFromWorkoutUseCase:
    return RemoveExerciseFromWorkoutUseCase(repo)


def get_reorder_exercises_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> ReorderExercisesUseCase:
    return ReorderExercisesUseCase(repo)


def get_get_workout_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> GetWorkoutWithDaysUseCase:
    return GetWorkoutWithDaysUseCase(repo)


def get_get_workouts_by_user_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> GetWorkoutsByUserUseCase:
    return GetWorkoutsByUserUseCase(repo)
