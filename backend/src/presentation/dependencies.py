from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.infrastructure.database import get_session
from backend.src.infrastructure.auth.jwt import create_access_token, decode_access_token
from backend.src.infrastructure.auth.password import hash_password, verify_password
from backend.src.infrastructure.auth.refresh_tokens import (
    generate_refresh_token,
    hash_refresh_token,
)
from backend.src.infrastructure.config import settings
from backend.src.infrastructure.persistence.models import UserModel
from backend.src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from backend.src.infrastructure.persistence.password_reset_token_repository import (
    SqlAlchemyPasswordResetTokenRepository,
)
from backend.src.infrastructure.persistence.exercise_repository import SqlAlchemyExerciseRepository
from backend.src.infrastructure.persistence.refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from backend.src.infrastructure.persistence.workout_repository import SqlAlchemyWorkoutRepository
from backend.src.infrastructure.persistence.session_repository import SqlAlchemySessionRepository
from backend.src.infrastructure.persistence.personal_record_repository import (
    SqlAlchemyPersonalRecordRepository,
)
from backend.src.infrastructure.persistence.stats_repository import (
    SqlAlchemyStatsRepository,
)
from backend.src.domain.repositories.workout_repository import WorkoutRepository
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.repositories.personal_record_repository import PersonalRecordRepository
from backend.src.domain.repositories.stats_repository import StatsRepository
from backend.src.application.services.token_issuer import TokenIssuer
from backend.src.application.use_cases.create_workout import CreateWorkoutUseCase
from backend.src.application.use_cases.logout import LogoutUseCase
from backend.src.application.use_cases.refresh_session import RefreshSessionUseCase
from backend.src.application.use_cases.list_exercises import ListExercisesUseCase
from backend.src.application.use_cases.add_training_day import AddTrainingDayUseCase
from backend.src.application.use_cases.remove_training_day import RemoveTrainingDayUseCase
from backend.src.application.use_cases.add_exercise_to_workout import AddExerciseToWorkoutUseCase
from backend.src.application.use_cases.remove_exercise_from_workout import RemoveExerciseFromWorkoutUseCase
from backend.src.application.use_cases.reorder_exercises import ReorderExercisesUseCase
from backend.src.application.use_cases.reorder_training_days import ReorderTrainingDaysUseCase
from backend.src.application.use_cases.get_workout_with_days import GetWorkoutWithDaysUseCase
from backend.src.application.use_cases.get_workouts_by_user import GetWorkoutsByUserUseCase
from backend.src.application.use_cases.delete_workout import DeleteWorkoutUseCase
from backend.src.application.use_cases.rename_workout import RenameWorkoutUseCase
from backend.src.application.use_cases.set_workout_active import SetWorkoutActiveUseCase
from backend.src.application.use_cases.start_workout_session import StartWorkoutSessionUseCase
from backend.src.application.use_cases.log_exercise_set import LogExerciseSetUseCase
from backend.src.application.use_cases.update_exercise_log import UpdateExerciseLogUseCase
from backend.src.application.use_cases.complete_workout_session import CompleteWorkoutSessionUseCase
from backend.src.application.use_cases.delete_exercise_log import DeleteExerciseLogUseCase
from backend.src.application.use_cases.delete_workout_session import DeleteWorkoutSessionUseCase
from backend.src.application.use_cases.get_sessions_for_day import GetSessionsForDayUseCase
from backend.src.application.use_cases.get_session_history import GetSessionHistoryUseCase
from backend.src.application.use_cases.get_user_stats import GetUserStatsUseCase
from backend.src.application.use_cases.forgot_password import ForgotPasswordUseCase
from backend.src.application.use_cases.reset_password import ResetPasswordUseCase
from backend.src.application.use_cases.change_password import ChangePasswordUseCase
from backend.src.application.use_cases.update_user_preferences import UpdateUserPreferencesUseCase
from backend.src.application.use_cases.register_user import RegisterUserUseCase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _create_user_model(user_id: str, email: str, hashed_password: str) -> UserModel:
    return UserModel(id=user_id, email=email, hashed_password=hashed_password)


def get_user_repository(session: AsyncSession = Depends(get_session)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> UserModel:
    user_id = decode_access_token(token)
    user = await user_repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> UserModel | None:
    if token is None:
        return None
    try:
        return await get_current_user(token, user_repo)
    except HTTPException:
        return None


def get_current_user_id(user: UserModel = Depends(get_current_user)) -> str:
    return user.id


def get_workout_repository(session: AsyncSession = Depends(get_session)) -> SqlAlchemyWorkoutRepository:
    return SqlAlchemyWorkoutRepository(session)


def get_exercise_repository(session: AsyncSession = Depends(get_session)) -> SqlAlchemyExerciseRepository:
    return SqlAlchemyExerciseRepository(session)


def get_refresh_token_repository(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyRefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(session)


def get_password_reset_token_repository(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyPasswordResetTokenRepository:
    return SqlAlchemyPasswordResetTokenRepository(session)


def get_token_issuer(
    repo: SqlAlchemyRefreshTokenRepository = Depends(get_refresh_token_repository),
) -> TokenIssuer:
    return TokenIssuer(
        repo,
        hash_token=hash_refresh_token,
        generate_token=generate_refresh_token,
        create_access_token=create_access_token,
        refresh_token_ttl=timedelta(days=settings.refresh_token_expire_days),
    )


def get_refresh_session_uc(
    repo: SqlAlchemyRefreshTokenRepository = Depends(get_refresh_token_repository),
    token_issuer: TokenIssuer = Depends(get_token_issuer),
) -> RefreshSessionUseCase:
    return RefreshSessionUseCase(
        repo,
        hash_token=hash_refresh_token,
        token_issuer=token_issuer,
        reuse_grace_period=timedelta(seconds=settings.refresh_token_reuse_grace_seconds),
    )


def get_logout_uc(
    repo: SqlAlchemyRefreshTokenRepository = Depends(get_refresh_token_repository),
) -> LogoutUseCase:
    return LogoutUseCase(repo, hash_token=hash_refresh_token)


def get_list_exercises_uc(
    exercise_repo: SqlAlchemyExerciseRepository = Depends(get_exercise_repository),
) -> ListExercisesUseCase:
    return ListExercisesUseCase(exercise_repo)


def get_create_workout_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> CreateWorkoutUseCase:
    return CreateWorkoutUseCase(repo)


def get_add_training_day_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> AddTrainingDayUseCase:
    return AddTrainingDayUseCase(repo)


def get_remove_training_day_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> RemoveTrainingDayUseCase:
    return RemoveTrainingDayUseCase(repo)


def get_add_exercise_uc(
    repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository),
    exercise_repo: SqlAlchemyExerciseRepository = Depends(get_exercise_repository),
) -> AddExerciseToWorkoutUseCase:
    return AddExerciseToWorkoutUseCase(repo, exercise_repo)


def get_remove_exercise_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> RemoveExerciseFromWorkoutUseCase:
    return RemoveExerciseFromWorkoutUseCase(repo)


def get_reorder_exercises_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> ReorderExercisesUseCase:
    return ReorderExercisesUseCase(repo)


def get_reorder_training_days_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> ReorderTrainingDaysUseCase:
    return ReorderTrainingDaysUseCase(repo)


def get_get_workout_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> GetWorkoutWithDaysUseCase:
    return GetWorkoutWithDaysUseCase(repo)


def get_get_workouts_by_user_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> GetWorkoutsByUserUseCase:
    return GetWorkoutsByUserUseCase(repo)


def get_delete_workout_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> DeleteWorkoutUseCase:
    return DeleteWorkoutUseCase(repo)


def get_rename_workout_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> RenameWorkoutUseCase:
    return RenameWorkoutUseCase(repo)


def get_set_workout_active_uc(repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository)) -> SetWorkoutActiveUseCase:
    return SetWorkoutActiveUseCase(repo)


def get_session_repository(session: AsyncSession = Depends(get_session)) -> SessionRepository:
    return SqlAlchemySessionRepository(session)


def get_start_session_uc(
    workout_repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
) -> StartWorkoutSessionUseCase:
    return StartWorkoutSessionUseCase(workout_repo, session_repo)


def get_log_exercise_set_uc(
    workout_repo: SqlAlchemyWorkoutRepository = Depends(get_workout_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
) -> LogExerciseSetUseCase:
    return LogExerciseSetUseCase(workout_repo, session_repo)


def get_update_log_uc(
    session_repo: SessionRepository = Depends(get_session_repository),
) -> UpdateExerciseLogUseCase:
    return UpdateExerciseLogUseCase(session_repo)


def get_personal_record_repository(
    session: AsyncSession = Depends(get_session),
) -> PersonalRecordRepository:
    return SqlAlchemyPersonalRecordRepository(session)


def get_complete_session_uc(
    session_repo: SessionRepository = Depends(get_session_repository),
    pr_repo: PersonalRecordRepository = Depends(get_personal_record_repository),
) -> CompleteWorkoutSessionUseCase:
    return CompleteWorkoutSessionUseCase(session_repo, pr_repo)


def get_delete_log_uc(
    session_repo: SessionRepository = Depends(get_session_repository),
) -> DeleteExerciseLogUseCase:
    return DeleteExerciseLogUseCase(session_repo)


def get_delete_session_uc(
    session_repo: SessionRepository = Depends(get_session_repository),
) -> DeleteWorkoutSessionUseCase:
    return DeleteWorkoutSessionUseCase(session_repo)


def get_get_sessions_for_day_uc(
    session_repo: SessionRepository = Depends(get_session_repository),
    workout_repo: WorkoutRepository = Depends(get_workout_repository),
) -> GetSessionsForDayUseCase:
    return GetSessionsForDayUseCase(session_repo, workout_repo)


def get_session_history_uc(
    session_repo: SessionRepository = Depends(get_session_repository),
) -> GetSessionHistoryUseCase:
    return GetSessionHistoryUseCase(session_repo)


def get_stats_repository(session: AsyncSession = Depends(get_session)) -> StatsRepository:
    return SqlAlchemyStatsRepository(session)


def get_user_stats_uc(
    stats_repo: StatsRepository = Depends(get_stats_repository),
) -> GetUserStatsUseCase:
    return GetUserStatsUseCase(stats_repo)


def get_forgot_password_uc(
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
    token_repo: SqlAlchemyPasswordResetTokenRepository = Depends(get_password_reset_token_repository),
) -> ForgotPasswordUseCase:
    return ForgotPasswordUseCase(
        user_repo=user_repo,
        token_repo=token_repo,
        base_url=settings.app_base_url,
    )


def get_reset_password_uc(
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
    token_repo: SqlAlchemyPasswordResetTokenRepository = Depends(get_password_reset_token_repository),
    refresh_token_repo: SqlAlchemyRefreshTokenRepository = Depends(get_refresh_token_repository),
) -> ResetPasswordUseCase:
    return ResetPasswordUseCase(
        user_repo=user_repo,
        token_repo=token_repo,
        refresh_token_repo=refresh_token_repo,
        hash_password=hash_password,
    )


def get_change_password_uc(
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
    refresh_token_repo: SqlAlchemyRefreshTokenRepository = Depends(get_refresh_token_repository),
) -> ChangePasswordUseCase:
    return ChangePasswordUseCase(
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
        hash_password=hash_password,
        verify_password=verify_password,
    )


def get_update_preferences_uc(
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> UpdateUserPreferencesUseCase:
    return UpdateUserPreferencesUseCase(user_repo=user_repo)


def get_register_user_uc(
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        user_repo=user_repo,
        create_user=_create_user_model,
        hash_password=hash_password,
    )
