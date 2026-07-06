"""Session request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field

from backend.src.application.dtos import ExerciseLogDTO, WorkoutSessionDTO


# ── Request schemas ───────────────────────────────────────────────────────────


class LogSetRequest(BaseModel):
    workout_exercise_id: str
    set_number: int = Field(ge=1)
    reps_completed: int = Field(ge=1)
    # Optional: bodyweight exercises log sets without external weight.
    weight_kg: float | None = Field(default=None, ge=0.0)


class UpdateLogRequest(BaseModel):
    reps_completed: int | None = Field(default=None, ge=1)
    weight_kg: float | None = Field(default=None, ge=0.0)


# ── Response schemas ──────────────────────────────────────────────────────────


class ExerciseLogResponse(BaseModel):
    id: str
    session_id: str
    workout_exercise_id: str
    set_number: int
    reps_completed: int
    weight_kg: float | None

    @classmethod
    def from_dto(cls, dto: ExerciseLogDTO) -> "ExerciseLogResponse":
        return cls(
            id=dto.id,
            session_id=dto.session_id,
            workout_exercise_id=dto.workout_exercise_id,
            set_number=dto.set_number,
            reps_completed=dto.reps_completed,
            weight_kg=dto.weight_kg,
        )


class WorkoutSessionResponse(BaseModel):
    id: str
    user_id: str
    workout_id: str
    training_day_id: str
    started_at: str
    status: str
    completed_at: str | None
    logs: list[ExerciseLogResponse]

    @classmethod
    def from_dto(cls, dto: WorkoutSessionDTO) -> "WorkoutSessionResponse":
        return cls(
            id=dto.id,
            user_id=dto.user_id,
            workout_id=dto.workout_id,
            training_day_id=dto.training_day_id,
            started_at=dto.started_at,
            status=dto.status,
            completed_at=dto.completed_at,
            logs=[ExerciseLogResponse.from_dto(log) for log in dto.logs],
        )
