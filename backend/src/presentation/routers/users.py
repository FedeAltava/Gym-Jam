"""Users router — per-user preference and stats endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from returns.result import Failure
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.commands import (
    GetUserStatsQuery,
    UpdateUserPreferencesCommand,
)
from backend.src.application.use_cases.get_user_stats import GetUserStatsUseCase
from backend.src.application.use_cases.update_user_preferences import UpdateUserPreferencesUseCase
from backend.src.infrastructure.database import get_session
from backend.src.presentation.dependencies import (
    get_current_user_id,
    get_update_preferences_uc,
    get_user_stats_uc,
)
from backend.src.presentation.schemas.auth_schemas import UserResponse
from backend.src.presentation.schemas.user_schemas import (
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


@router.get("/users/me/stats", response_model=UserStatsResponse)
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
