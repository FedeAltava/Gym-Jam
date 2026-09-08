"""Pydantic request/response schemas for the nutrition endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from backend.src.application.dtos import DietPlanDTO, DietPlanSummaryDTO


class DietPlanResponse(BaseModel):
    """Full diet plan including the weekly menu JSON."""

    id: str
    user_id: str
    title: str
    calories: int | None
    menu_json: dict
    uploaded_at: datetime

    @classmethod
    def from_dto(cls, dto: DietPlanDTO) -> "DietPlanResponse":
        return cls(
            id=dto.id,
            user_id=dto.user_id,
            title=dto.title,
            calories=dto.calories,
            menu_json=dto.menu_json,
            uploaded_at=dto.uploaded_at,
        )


class DietPlanSummaryResponse(BaseModel):
    """Lightweight summary — no menu_json — used in list responses."""

    id: str
    user_id: str
    title: str
    calories: int | None
    uploaded_at: datetime

    @classmethod
    def from_dto(cls, dto: DietPlanSummaryDTO) -> "DietPlanSummaryResponse":
        return cls(
            id=dto.id,
            user_id=dto.user_id,
            title=dto.title,
            calories=dto.calories,
            uploaded_at=dto.uploaded_at,
        )
