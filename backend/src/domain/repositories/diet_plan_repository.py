"""DietPlanRepository port — abstract base class for persistence."""
from abc import ABC, abstractmethod

from backend.src.domain.entities.diet_plan import DietPlan
from backend.src.domain.value_objects.diet_plan_id import DietPlanId


class DietPlanRepository(ABC):
    @abstractmethod
    async def save(self, plan: DietPlan) -> None: ...

    @abstractmethod
    async def get_by_id_for_user(self, id: DietPlanId, user_id: str) -> DietPlan | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[DietPlan]: ...
