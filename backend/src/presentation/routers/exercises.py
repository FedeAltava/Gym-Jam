from fastapi import APIRouter, Depends, Query
from returns.result import Failure
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.commands import CreateExerciseCommand, DeleteExerciseCommand
from backend.src.application.use_cases.create_exercise import CreateExerciseUseCase
from backend.src.application.use_cases.delete_exercise import DeleteExerciseUseCase
from backend.src.application.use_cases.list_exercises import ListExercisesUseCase
from backend.src.infrastructure.database import get_session
from backend.src.presentation.dependencies import (
    get_create_exercise_uc,
    get_current_user_id,
    get_delete_exercise_uc,
    get_list_exercises_uc,
)
from backend.src.presentation.schemas.exercise_schemas import (
    CreateExerciseRequest,
    ExerciseResponse,
)

router = APIRouter(redirect_slashes=False)


@router.get("", status_code=200, response_model=list[ExerciseResponse])
async def list_exercises(
    uc: ListExercisesUseCase = Depends(get_list_exercises_uc),
    user_id: str = Depends(get_current_user_id),
    muscle_group: str | None = Query(default=None),
) -> list[ExerciseResponse]:
    result = await uc.execute(muscle_group=muscle_group, user_id=user_id)
    if isinstance(result, Failure):
        raise result.failure()
    return [ExerciseResponse.from_dto(dto) for dto in result.unwrap()]


@router.post("", status_code=201, response_model=ExerciseResponse)
async def create_exercise(
    body: CreateExerciseRequest,
    uc: CreateExerciseUseCase = Depends(get_create_exercise_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ExerciseResponse:
    cmd = CreateExerciseCommand(
        user_id=user_id,
        name=body.name,
        muscle_group=body.muscle_group,
        is_bodyweight=body.is_bodyweight,
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return ExerciseResponse.from_dto(result.unwrap())


@router.delete("/{exercise_id}", status_code=204)
async def delete_exercise(
    exercise_id: str,
    uc: DeleteExerciseUseCase = Depends(get_delete_exercise_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    cmd = DeleteExerciseCommand(user_id=user_id, exercise_id=exercise_id)
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
