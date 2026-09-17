"""ListDietPlansUseCase — return all diet plans for a user (newest first)."""
from __future__ import annotations

from backend.src.application.commands import ListDietPlansQuery
from backend.src.application.dtos import DietPlanSummaryDTO
from backend.src.domain.repositories.diet_plan_repository import DietPlanRepository


class ListDietPlansUseCase:
    def __init__(self, repo: DietPlanRepository) -> None:
        self._repo = repo

    async def execute(self, query: ListDietPlansQuery) -> list[DietPlanSummaryDTO]:
        plans = await self._repo.list_by_user(query.user_id)
        return [DietPlanSummaryDTO.from_aggregate(plan) for plan in plans]
