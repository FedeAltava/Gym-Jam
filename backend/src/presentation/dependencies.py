from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.src.infrastructure.database import get_session
from backend.src.infrastructure.auth.jwt import decode_access_token
from backend.src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from backend.src.infrastructure.persistence.models import UserModel
from backend.src.infrastructure.persistence.workout_repository import SqlAlchemyWorkoutRepository
from backend.src.application.use_cases.create_workout import CreateWorkoutUseCase
from backend.src.application.use_cases.add_training_day import AddTrainingDayUseCase
from backend.src.application.use_cases.remove_training_day import RemoveTrainingDayUseCase
from backend.src.application.use_cases.add_exercise_to_workout import AddExerciseToWorkoutUseCase
from backend.src.application.use_cases.remove_exercise_from_workout import RemoveExerciseFromWorkoutUseCase
from backend.src.application.use_cases.reorder_exercises import ReorderExercisesUseCase
from backend.src.application.use_cases.get_workout_with_days import GetWorkoutWithDaysUseCase
from backend.src.application.use_cases.get_workouts_by_user import GetWorkoutsByUserUseCase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
_user_repo = SqlAlchemyUserRepository()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> UserModel:
    user_id = decode_access_token(token)  # raises 401 on invalid/expired token
    user = await _user_repo.find_by_id(user_id, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user_id(user: UserModel = Depends(get_current_user)) -> str:
    return user.id


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
