from __future__ import annotations
from pydantic import BaseModel
from backend.src.application.dtos import WorkoutWithDaysDTO, TrainingDayDTO, WorkoutExerciseDTO

# ── Request schemas ──────────────────────────────────────────────────────────

class CreateWorkoutRequest(BaseModel):
    name: str
    description: str | None = None
    training_days: list[str] = []

class AddTrainingDayRequest(BaseModel):
    day_of_week: str

class AddExerciseRequest(BaseModel):
    exercise_id: str

class ReorderExercisesRequest(BaseModel):
    ordered_exercise_ids: list[str]

# ── Response schemas ─────────────────────────────────────────────────────────

class WorkoutExerciseResponse(BaseModel):
    id: str
    exercise_id: str
    order: int

    @classmethod
    def from_dto(cls, dto: WorkoutExerciseDTO) -> WorkoutExerciseResponse:
        return cls(id=dto.id, exercise_id=dto.exercise_id, order=dto.order)

class TrainingDayResponse(BaseModel):
    day_of_week: str
    exercises: list[WorkoutExerciseResponse]

    @classmethod
    def from_dto(cls, dto: TrainingDayDTO) -> TrainingDayResponse:
        return cls(
            day_of_week=dto.day_of_week,
            exercises=[WorkoutExerciseResponse.from_dto(e) for e in dto.exercises],
        )

class WorkoutResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None
    is_active: bool
    training_days: list[TrainingDayResponse]

    @classmethod
    def from_dto(cls, dto: WorkoutWithDaysDTO) -> WorkoutResponse:
        return cls(
            id=dto.id,
            user_id=dto.user_id,
            name=dto.name,
            description=dto.description,
            is_active=dto.is_active,
            training_days=[TrainingDayResponse.from_dto(d) for d in dto.training_days],
        )
