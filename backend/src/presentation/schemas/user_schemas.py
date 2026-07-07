"""User schemas — request/response models for user preference endpoints."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class UserPreferencesRequest(BaseModel):
    """Partial update: omitted/None fields are left unchanged."""

    rest_seconds: int | None = Field(None, ge=0, le=600)
    units: Literal["kg", "lb"] | None = None
