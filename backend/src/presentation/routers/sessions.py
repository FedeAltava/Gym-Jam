"""Sessions router — application layer entry point for workout session endpoints."""
from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from returns.result import Failure
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.commands import (
    CompleteWorkoutSessionCommand,
    DeleteExerciseLogCommand,
    DeleteWorkoutSessionCommand,
    GetSessionHistoryQuery,
    GetSessionsForDayCommand,
    LogExerciseSetCommand,
    StartWorkoutSessionCommand,
    UpdateExerciseLogCommand,
)
from backend.src.application.use_cases.complete_workout_session import CompleteWorkoutSessionUseCase
from backend.src.application.use_cases.delete_exercise_log import DeleteExerciseLogUseCase
from backend.src.application.use_cases.delete_workout_session import DeleteWorkoutSessionUseCase
from backend.src.application.use_cases.get_session_history import GetSessionHistoryUseCase
from backend.src.application.use_cases.get_sessions_for_day import GetSessionsForDayUseCase
from backend.src.application.use_cases.log_exercise_set import LogExerciseSetUseCase
from backend.src.application.use_cases.start_workout_session import StartWorkoutSessionUseCase
from backend.src.application.use_cases.update_exercise_log import UpdateExerciseLogUseCase
from backend.src.infrastructure.database import get_session
from backend.src.presentation.dependencies import (
    get_complete_session_uc,
    get_current_user_id,
    get_delete_log_uc,
    get_delete_session_uc,
    get_get_sessions_for_day_uc,
    get_log_exercise_set_uc,
    get_session_history_uc,
    get_start_session_uc,
    get_update_log_uc,
)
from backend.src.presentation.schemas.session_schemas import (
    ExerciseLogResponse,
    LogSetRequest,
    SessionHistoryItemResponse,
    UpdateLogRequest,
    WorkoutSessionResponse,
)

router = APIRouter(redirect_slashes=False)


@router.post(
    "/workouts/{workout_id}/days/{day_id}/sessions",
    status_code=201,
    response_model=WorkoutSessionResponse,
)
async def start_session(
    workout_id: str,
    day_id: str,
    uc: StartWorkoutSessionUseCase = Depends(get_start_session_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> WorkoutSessionResponse:
    cmd = StartWorkoutSessionCommand(
        user_id=user_id,
        workout_id=workout_id,
        training_day_id=day_id,
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return WorkoutSessionResponse.from_dto(result.unwrap())


@router.get(
    "/workouts/{workout_id}/days/{day_id}/sessions",
    status_code=200,
    response_model=list[WorkoutSessionResponse],
)
async def get_sessions_for_day(
    workout_id: str,
    day_id: str,
    uc: GetSessionsForDayUseCase = Depends(get_get_sessions_for_day_uc),
    user_id: str = Depends(get_current_user_id),
) -> list[WorkoutSessionResponse]:
    cmd = GetSessionsForDayCommand(
        user_id=user_id,
        workout_id=workout_id,
        training_day_id=day_id,
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    return [WorkoutSessionResponse.from_dto(dto) for dto in result.unwrap()]


# Router is mounted with prefix="" (see main.py), so this is GET /sessions.
@router.get(
    "/sessions",
    status_code=200,
    response_model=list[SessionHistoryItemResponse],
)
async def get_session_history(
    workout_id: str | None = None,
    day_id: str | None = None,
    status: Literal["completed", "in_progress"] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    uc: GetSessionHistoryUseCase = Depends(get_session_history_uc),
    user_id: str = Depends(get_current_user_id),
) -> list[SessionHistoryItemResponse]:
    query = GetSessionHistoryQuery(
        user_id=user_id,
        workout_id=workout_id,
        day_id=day_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    result = await uc.execute(query)
    if isinstance(result, Failure):
        raise result.failure()
    return [SessionHistoryItemResponse.from_dto(dto) for dto in result.unwrap()]


@router.post(
    "/sessions/{session_id}/logs",
    status_code=201,
    response_model=ExerciseLogResponse,
)
async def log_exercise_set(
    session_id: str,
    body: LogSetRequest,
    uc: LogExerciseSetUseCase = Depends(get_log_exercise_set_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ExerciseLogResponse:
    cmd = LogExerciseSetCommand(
        user_id=user_id,
        session_id=session_id,
        workout_exercise_id=body.workout_exercise_id,
        set_number=body.set_number,
        reps_completed=body.reps_completed,
        weight_kg=body.weight_kg,
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return ExerciseLogResponse.from_dto(result.unwrap())


@router.patch(
    "/sessions/{session_id}/logs/{log_id}",
    status_code=200,
    response_model=ExerciseLogResponse,
)
async def update_exercise_log(
    session_id: str,
    log_id: str,
    body: UpdateLogRequest,
    uc: UpdateExerciseLogUseCase = Depends(get_update_log_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ExerciseLogResponse:
    cmd = UpdateExerciseLogCommand(
        user_id=user_id,
        session_id=session_id,
        log_id=log_id,
        reps_completed=body.reps_completed,
        weight_kg=body.weight_kg,
        # model_fields_set = fields explicitly present in the request body.
        # Lets the use case distinguish "omitted" from "sent as null" so an
        # explicit weight_kg: null clears the stored weight.
        fields_set=frozenset(body.model_fields_set),
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return ExerciseLogResponse.from_dto(result.unwrap())


@router.delete(
    "/sessions/{session_id}/logs/{log_id}",
    status_code=204,
)
async def delete_exercise_log(
    session_id: str,
    log_id: str,
    uc: DeleteExerciseLogUseCase = Depends(get_delete_log_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    cmd = DeleteExerciseLogCommand(user_id=user_id, session_id=session_id, log_id=log_id)
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()


@router.post(
    "/sessions/{session_id}/complete",
    status_code=200,
    response_model=WorkoutSessionResponse,
)
async def complete_session(
    session_id: str,
    uc: CompleteWorkoutSessionUseCase = Depends(get_complete_session_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> WorkoutSessionResponse:
    cmd = CompleteWorkoutSessionCommand(user_id=user_id, session_id=session_id)
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return WorkoutSessionResponse.from_dto(result.unwrap())


@router.delete(
    "/sessions/{session_id}",
    status_code=204,
)
async def delete_session(
    session_id: str,
    uc: DeleteWorkoutSessionUseCase = Depends(get_delete_session_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    cmd = DeleteWorkoutSessionCommand(user_id=user_id, session_id=session_id)
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
