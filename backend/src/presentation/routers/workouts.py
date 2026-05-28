from fastapi import APIRouter, Depends, Response
from returns.result import Failure
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.commands import (
    AddExerciseToWorkoutCommand,
    AddTrainingDayCommand,
    CreateWorkoutCommand,
    GetWorkoutWithDaysQuery,
    RemoveExerciseFromWorkoutCommand,
    RemoveTrainingDayCommand,
    ReorderExercisesCommand,
)
from backend.src.application.use_cases.get_workouts_by_user import GetWorkoutsByUserQuery
from backend.src.application.use_cases.add_exercise_to_workout import AddExerciseToWorkoutUseCase
from backend.src.application.use_cases.add_training_day import AddTrainingDayUseCase
from backend.src.application.use_cases.create_workout import CreateWorkoutUseCase
from backend.src.application.use_cases.get_workout_with_days import GetWorkoutWithDaysUseCase
from backend.src.application.use_cases.get_workouts_by_user import GetWorkoutsByUserUseCase
from backend.src.application.use_cases.remove_exercise_from_workout import RemoveExerciseFromWorkoutUseCase
from backend.src.application.use_cases.remove_training_day import RemoveTrainingDayUseCase
from backend.src.application.use_cases.reorder_exercises import ReorderExercisesUseCase
from backend.src.presentation.dependencies import (
    get_add_exercise_uc,
    get_add_training_day_uc,
    get_create_workout_uc,
    get_current_user_id,
    get_get_workout_uc,
    get_get_workouts_by_user_uc,
    get_remove_exercise_uc,
    get_remove_training_day_uc,
    get_reorder_exercises_uc,
    get_session,
)
from backend.src.presentation.schemas.workout_schemas import (
    AddExerciseRequest,
    AddTrainingDayRequest,
    CreateWorkoutRequest,
    ReorderExercisesRequest,
    TrainingDayResponse,
    WorkoutExerciseResponse,
    WorkoutResponse,
)

router = APIRouter(redirect_slashes=False)


@router.post("", status_code=201, response_model=WorkoutResponse)
async def create_workout(
    body: CreateWorkoutRequest,
    uc: CreateWorkoutUseCase = Depends(get_create_workout_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> WorkoutResponse:
    cmd = CreateWorkoutCommand(
        user_id=user_id,
        name=body.name,
        description=body.description,
        training_days=tuple(body.training_days),
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return WorkoutResponse.from_dto(result.unwrap())


@router.get("", status_code=200, response_model=list[WorkoutResponse])
async def list_workouts(
    uc: GetWorkoutsByUserUseCase = Depends(get_get_workouts_by_user_uc),
    user_id: str = Depends(get_current_user_id),
) -> list[WorkoutResponse]:
    result = await uc.execute(GetWorkoutsByUserQuery(user_id=user_id))
    if isinstance(result, Failure):
        raise result.failure()
    return [WorkoutResponse.from_dto(dto) for dto in result.unwrap()]


@router.get("/{workout_id}", status_code=200, response_model=WorkoutResponse)
async def get_workout(
    workout_id: str,
    uc: GetWorkoutWithDaysUseCase = Depends(get_get_workout_uc),
    user_id: str = Depends(get_current_user_id),
) -> WorkoutResponse:
    query = GetWorkoutWithDaysQuery(workout_id=workout_id, user_id=user_id)
    result = await uc.execute(query)
    if isinstance(result, Failure):
        raise result.failure()
    return WorkoutResponse.from_dto(result.unwrap())


@router.post("/{workout_id}/training-days", status_code=201, response_model=TrainingDayResponse)
async def add_training_day(
    workout_id: str,
    body: AddTrainingDayRequest,
    uc: AddTrainingDayUseCase = Depends(get_add_training_day_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> TrainingDayResponse:
    cmd = AddTrainingDayCommand(
        workout_id=workout_id,
        user_id=user_id,
        day_of_week=body.day_of_week.upper(),
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return TrainingDayResponse.from_dto(result.unwrap())


@router.delete("/{workout_id}/training-days/{day}", status_code=204)
async def remove_training_day(
    workout_id: str,
    day: str,
    uc: RemoveTrainingDayUseCase = Depends(get_remove_training_day_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    cmd = RemoveTrainingDayCommand(
        workout_id=workout_id,
        user_id=user_id,
        day_of_week=day.upper(),
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return Response(status_code=204)


@router.post("/{workout_id}/training-days/{day}/exercises", status_code=201, response_model=WorkoutExerciseResponse)
async def add_exercise(
    workout_id: str,
    day: str,
    body: AddExerciseRequest,
    uc: AddExerciseToWorkoutUseCase = Depends(get_add_exercise_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> WorkoutExerciseResponse:
    cmd = AddExerciseToWorkoutCommand(
        workout_id=workout_id,
        user_id=user_id,
        day_of_week=day.upper(),
        exercise_id=body.exercise_id,
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return WorkoutExerciseResponse.from_dto(result.unwrap())


@router.delete("/{workout_id}/training-days/{day}/exercises/{exercise_id}", status_code=204)
async def remove_exercise(
    workout_id: str,
    day: str,
    exercise_id: str,
    uc: RemoveExerciseFromWorkoutUseCase = Depends(get_remove_exercise_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    cmd = RemoveExerciseFromWorkoutCommand(
        workout_id=workout_id,
        user_id=user_id,
        day_of_week=day.upper(),
        workout_exercise_id=exercise_id,
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return Response(status_code=204)


@router.put("/{workout_id}/training-days/{day}/exercises/reorder", status_code=200, response_model=TrainingDayResponse)
async def reorder_exercises(
    workout_id: str,
    day: str,
    body: ReorderExercisesRequest,
    uc: ReorderExercisesUseCase = Depends(get_reorder_exercises_uc),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> TrainingDayResponse:
    cmd = ReorderExercisesCommand(
        workout_id=workout_id,
        user_id=user_id,
        day_of_week=day.upper(),
        ordered_exercise_ids=tuple(body.ordered_exercise_ids),
    )
    result = await uc.execute(cmd)
    if isinstance(result, Failure):
        raise result.failure()
    await session.commit()
    return TrainingDayResponse.from_dto(result.unwrap())
