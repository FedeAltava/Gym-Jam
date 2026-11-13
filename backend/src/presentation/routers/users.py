"""Users router — per-user preference and stats endpoints."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from returns.result import Failure
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.commands import (
    DeleteBodyWeightCommand,
    GetUserStatsQuery,
    RecordBodyWeightCommand,
    UpdateUserPreferencesCommand,
)
from backend.src.application.use_cases.body_weight import (
    DeleteBodyWeightUseCase,
    ListBodyWeightUseCase,
    RecordBodyWeightUseCase,
)
from backend.src.application.use_cases.get_user_stats import GetUserStatsUseCase
from backend.src.application.use_cases.update_user_preferences import UpdateUserPreferencesUseCase
from backend.src.infrastructure.database import get_session
from backend.src.presentation.dependencies import (
    complete_idle_sessions,
    get_current_user_id,
    get_delete_body_weight_uc,
    get_list_body_weight_uc,
    get_record_body_weight_uc,
    get_update_preferences_uc,
    get_user_stats_uc,
)
from backend.src.presentation.schemas.auth_schemas import UserResponse
from backend.src.presentation.schemas.user_schemas import (
    BodyWeightEntryResponse,
    BodyWeightRequest,
    UserPreferencesRequest,
    UserStatsResponse,
)

router = APIRouter(redirect_slashes=False)


@router.patch("/users/me/preferences", response_model=UserResponse)
async def update_preferences(
    body: UserPreferencesRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    uc: UpdateUserPreferencesUseCase = Depends(get_update_preferences_uc),
) -> UserResponse:
    cmd = UpdateUserPreferencesCommand(
        user_id=user_id,
        rest_seconds=body.rest_seconds,
        units=body.units,
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise HTTPException(status_code=404, detail=result.failure().message)
    await session.commit()
    user = result.unwrap()
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        rest_seconds=user.rest_seconds,
        units=user.units,
    )


# Idle sessions are completed first so the streak and totals include them.
@router.get("/users/me/stats", response_model=UserStatsResponse, dependencies=[Depends(complete_idle_sessions)])
async def get_user_stats(
    user_id: str = Depends(get_current_user_id),
    uc: GetUserStatsUseCase = Depends(get_user_stats_uc),
) -> UserStatsResponse:
    result = await uc.execute(GetUserStatsQuery(user_id=user_id))
    if isinstance(result, Failure):
        raise HTTPException(status_code=500, detail=str(result.failure()))
    stats = result.unwrap()
    return UserStatsResponse(
        total_sessions=stats.total_sessions,
        streak=stats.streak,
        total_prs=stats.total_prs,
        weekly_volume_kg=stats.weekly_volume_kg,
        weekly_sessions=stats.weekly_sessions,
        weekly_prs=stats.weekly_prs,
    )


@router.get("/users/me/body-weight", response_model=list[BodyWeightEntryResponse])
async def list_body_weight(
    user_id: str = Depends(get_current_user_id),
    uc: ListBodyWeightUseCase = Depends(get_list_body_weight_uc),
) -> list[BodyWeightEntryResponse]:
    """The user's weigh-ins, newest day first."""
    result = await uc.execute(user_id=user_id)
    if isinstance(result, Failure):
        raise result.failure()
    return [BodyWeightEntryResponse.from_dto(dto) for dto in result.unwrap()]


@router.put("/users/me/body-weight/{measured_on}", response_model=BodyWeightEntryResponse)
async def record_body_weight(
    measured_on: date,
    body: BodyWeightRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    uc: RecordBodyWeightUseCase = Depends(get_record_body_weight_uc),
) -> BodyWeightEntryResponse:
    """Record the weight for a day; a day that already has one is replaced."""
    cmd = RecordBodyWeightCommand(user_id=user_id, measured_on=measured_on, weight_kg=body.weight_kg)
    # The repository flushes the upsert, so a concurrent first insert for the
    # same day fails inside execute(), not only at commit.
    try:
        result = await uc.execute(cmd)
        if isinstance(result, Failure):
            raise result.failure()
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Body weight for this day changed concurrently")
    return BodyWeightEntryResponse.from_dto(result.unwrap())


@router.delete("/users/me/body-weight/{measured_on}", status_code=204)
async def delete_body_weight(
    measured_on: date,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    uc: DeleteBodyWeightUseCase = Depends(get_delete_body_weight_uc),
) -> None:
    result = await uc.execute(DeleteBodyWeightCommand(user_id=user_id, measured_on=measured_on))
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
