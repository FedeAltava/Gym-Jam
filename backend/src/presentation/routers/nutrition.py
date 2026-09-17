"""Nutrition router — PDF diet plan upload and retrieval endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from returns.result import Failure
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.commands import (
    GetDietPlanQuery,
    ListDietPlansQuery,
    UploadDietPlanCommand,
)
from backend.src.application.use_cases.get_diet_plan import GetDietPlanUseCase
from backend.src.application.use_cases.list_diet_plans import ListDietPlansUseCase
from backend.src.application.use_cases.upload_diet_plan import UploadDietPlanUseCase
from backend.src.infrastructure.database import get_session
from backend.src.presentation.dependencies import (
    get_current_user_id,
    get_get_diet_plan_use_case,
    get_list_diet_plans_use_case,
    get_upload_diet_plan_use_case,
)
from backend.src.presentation.schemas.nutrition_schemas import (
    DietPlanResponse,
    DietPlanSummaryResponse,
)

_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
_ACCEPTED_CONTENT_TYPE = "application/pdf"

router = APIRouter(redirect_slashes=False)


@router.post(
    "/menus",
    status_code=201,
    response_model=DietPlanResponse,
)
async def upload_diet_plan(
    file: UploadFile,
    uc: UploadDietPlanUseCase = Depends(get_upload_diet_plan_use_case),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> DietPlanResponse:
    # Guard: content-type must be PDF
    if file.content_type != _ACCEPTED_CONTENT_TYPE:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type '{file.content_type}'. Only application/pdf is accepted.",
        )

    # Guard: read bytes and enforce size limit
    pdf_bytes = await file.read()
    if len(pdf_bytes) > _MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of {_MAX_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    cmd = UploadDietPlanCommand(
        user_id=user_id,
        pdf_bytes=pdf_bytes,
        filename=file.filename or "upload.pdf",
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()

    await session.commit()
    return DietPlanResponse.from_dto(result.unwrap())


@router.get(
    "/menus",
    status_code=200,
    response_model=list[DietPlanSummaryResponse],
)
async def list_diet_plans(
    uc: ListDietPlansUseCase = Depends(get_list_diet_plans_use_case),
    user_id: str = Depends(get_current_user_id),
) -> list[DietPlanSummaryResponse]:
    query = ListDietPlansQuery(user_id=user_id)
    summaries = await uc.execute(query)
    return [DietPlanSummaryResponse.from_dto(dto) for dto in summaries]


@router.get(
    "/menus/{diet_plan_id}",
    status_code=200,
    response_model=DietPlanResponse,
)
async def get_diet_plan(
    diet_plan_id: str,
    uc: GetDietPlanUseCase = Depends(get_get_diet_plan_use_case),
    user_id: str = Depends(get_current_user_id),
) -> DietPlanResponse:
    query = GetDietPlanQuery(user_id=user_id, diet_plan_id=diet_plan_id)
    result = await uc.execute(query)
    if isinstance(result, Failure):
        raise result.failure()
    return DietPlanResponse.from_dto(result.unwrap())
