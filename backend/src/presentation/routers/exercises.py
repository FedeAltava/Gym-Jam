from fastapi import APIRouter, Depends, HTTPException, Query
from returns.result import Failure

from backend.src.application.use_cases.get_last_sets import GetLastSetsUseCase
from backend.src.application.use_cases.list_exercises import ListExercisesUseCase
from backend.src.presentation.dependencies import (
    get_current_user_id,
    get_last_sets_uc,
    get_list_exercises_uc,
)
from backend.src.presentation.schemas.exercise_schemas import ExerciseResponse, LastSetResponse

# Upper bound on exercise ids per last-sets request (a day holds far fewer).
MAX_LAST_SETS_EXERCISES = 50

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


@router.get("/last-sets", status_code=200, response_model=list[LastSetResponse])
async def get_last_sets(
    exercise_id: list[str] = Query(default_factory=list),
    uc: GetLastSetsUseCase = Depends(get_last_sets_uc),
    user_id: str = Depends(get_current_user_id),
) -> list[LastSetResponse]:
    """Latest logged set per set number of each exercise, in any routine or day."""
    if len(exercise_id) > MAX_LAST_SETS_EXERCISES:
        raise HTTPException(
            status_code=422, detail=f"At most {MAX_LAST_SETS_EXERCISES} exercise_id values are allowed"
        )
    result = await uc.execute(user_id=user_id, exercise_ids=exercise_id)
    if isinstance(result, Failure):
        raise result.failure()
    return [LastSetResponse.from_dto(dto) for dto in result.unwrap()]
