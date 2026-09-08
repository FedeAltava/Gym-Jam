"""DietPlan aggregate root — represents an uploaded weekly meal plan."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backend.src.domain.value_objects.diet_plan_id import DietPlanId


@dataclass(eq=False)
class DietPlan:
    id: DietPlanId
    user_id: str
    title: str
    calories: int | None
    menu: dict
    uploaded_at: datetime

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DietPlan):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
