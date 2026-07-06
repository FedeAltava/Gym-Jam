from fastapi import APIRouter, Depends, Query
from returns.result import Failure

from backend.src.application.use_cases.list_exercises import ListExercisesUseCase
from backend.src.presentation.dependencies import (
    get_current_user_id,
    get_list_exercises_uc,
)
from backend.src.presentation.schemas.exercise_schemas import ExerciseResponse

router = APIRouter(redirect_slashes=False)


@router.get("", status_code=200, response_model=list[ExerciseResponse])
async def list_exercises(
    uc: ListExercisesUseCase = Depends(get_list_exercises_uc),
    user_id: str = Depends(get_current_user_id),
    muscle_group: str | None = Query(default=None),
) -> list[ExerciseResponse]:
    result = await uc.execute(muscle_group=muscle_group)
    if isinstance(result, Failure):
        raise result.failure()
    return [ExerciseResponse.from_dto(dto) for dto in result.unwrap()]
