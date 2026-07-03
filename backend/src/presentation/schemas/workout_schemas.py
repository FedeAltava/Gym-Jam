from __future__ import annotations

from pydantic import BaseModel, Field

from backend.src.application.dtos import TrainingDayDTO, WorkoutExerciseDTO, WorkoutWithDaysDTO

# ── Request schemas ──────────────────────────────────────────────────────────


class CreateWorkoutRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    training_days: list[str] = []


class AddTrainingDayRequest(BaseModel):
    day_of_week: str


class AddExerciseRequest(BaseModel):
    exercise_id: str
    sets: int = Field(default=3, ge=1)
    reps_per_set: int = Field(default=10, ge=1)
    weight_kg: float | None = Field(default=None, ge=0.0)


class ReorderExercisesRequest(BaseModel):
    ordered_exercise_ids: list[str] = Field(max_length=50)

# ── Response schemas ─────────────────────────────────────────────────────────

class WorkoutExerciseResponse(BaseModel):
    id: str
    exercise_id: str
    order: int
    sets: int
    reps_per_set: int
    weight_kg: float | None

    @classmethod
    def from_dto(cls, dto: WorkoutExerciseDTO) -> WorkoutExerciseResponse:
        return cls(
            id=dto.id,
            exercise_id=dto.exercise_id,
            order=dto.order,
            sets=dto.sets,
            reps_per_set=dto.reps_per_set,
            weight_kg=dto.weight_kg,
        )

class TrainingDayResponse(BaseModel):
    id: str
    day_of_week: str
    exercises: list[WorkoutExerciseResponse]

    @classmethod
    def from_dto(cls, dto: TrainingDayDTO) -> TrainingDayResponse:
        return cls(
            id=dto.id,
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
