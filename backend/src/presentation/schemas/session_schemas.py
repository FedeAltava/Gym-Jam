"""Session request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field

from backend.src.application.dtos import (
    ExerciseLogDTO,
    PaginatedSessionHistoryDTO,
    SessionHistoryItemDTO,
    SessionHistoryLogDTO,
    WorkoutSessionDTO,
)


# ── Request schemas ───────────────────────────────────────────────────────────


class LogSetRequest(BaseModel):
    workout_exercise_id: str
    set_number: int = Field(ge=1)
    reps_completed: int = Field(ge=1)
    # Optional: bodyweight exercises log sets without external weight.
    weight_kg: float | None = Field(default=None, ge=0.0)


class UpdateLogRequest(BaseModel):
    # Omitted field = no change. Explicit `"weight_kg": null` = clear the
    # weight (bodyweight set). The router forwards `model_fields_set` so the
    # use case can tell both cases apart.
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
    # Whole seconds between started_at and completed_at; null in progress.
    duration_seconds: int | None
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
            duration_seconds=dto.duration_seconds,
            logs=[ExerciseLogResponse.from_dto(log) for log in dto.logs],
        )


class SessionHistoryLogResponse(BaseModel):
    id: str
    workout_exercise_id: str
    exercise_name: str
    muscle_group: str | None
    set_number: int
    reps_completed: int
    weight_kg: float | None

    @classmethod
    def from_dto(cls, dto: SessionHistoryLogDTO) -> "SessionHistoryLogResponse":
        return cls(
            id=dto.id,
            workout_exercise_id=dto.workout_exercise_id,
            exercise_name=dto.exercise_name,
            muscle_group=dto.muscle_group,
            set_number=dto.set_number,
            reps_completed=dto.reps_completed,
            weight_kg=dto.weight_kg,
        )


class SessionHistoryItemResponse(BaseModel):
    id: str
    workout_id: str
    training_day_id: str
    workout_name: str
    day_of_week: str
    started_at: str
    completed_at: str | None
    status: str  # "completed" | "in_progress" — derived from completed_at
    # PRs achieved in this session — drives the PR badge in Historial.
    pr_count: int
    # Whole seconds between started_at and completed_at; null in progress.
    duration_seconds: int | None
    logs: list[SessionHistoryLogResponse]

    @classmethod
    def from_dto(cls, dto: SessionHistoryItemDTO) -> "SessionHistoryItemResponse":
        return cls(
            id=dto.id,
            workout_id=dto.workout_id,
            training_day_id=dto.training_day_id,
            workout_name=dto.workout_name,
            day_of_week=dto.day_of_week,
            started_at=dto.started_at,
            completed_at=dto.completed_at,
            status=dto.status,
            pr_count=dto.pr_count,
            duration_seconds=dto.duration_seconds,
            logs=[SessionHistoryLogResponse.from_dto(log) for log in dto.logs],
        )


class PaginatedSessionHistoryResponse(BaseModel):
    items: list[SessionHistoryItemResponse]
    total: int
    page: int
    page_size: int

    @classmethod
    def from_dto(cls, dto: PaginatedSessionHistoryDTO) -> "PaginatedSessionHistoryResponse":
        return cls(
            items=[SessionHistoryItemResponse.from_dto(item) for item in dto.items],
            total=dto.total,
            page=dto.page,
            page_size=dto.page_size,
        )
