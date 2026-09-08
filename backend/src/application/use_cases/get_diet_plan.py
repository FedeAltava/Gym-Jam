"""GetDietPlanUseCase — fetch a single diet plan by id (with ownership check)."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import GetDietPlanQuery
from backend.src.application.dtos import DietPlanDTO
from backend.src.application.errors import ApplicationError, DietPlanNotFoundError
from backend.src.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.src.domain.value_objects.diet_plan_id import DietPlanId


class GetDietPlanUseCase:
    def __init__(self, repo: DietPlanRepository) -> None:
        self._repo = repo

    async def execute(self, query: GetDietPlanQuery) -> Result[DietPlanDTO, ApplicationError]:
        id_result = DietPlanId.from_string(query.diet_plan_id)
        if isinstance(id_result, Failure):
            return Failure(DietPlanNotFoundError(diet_plan_id=query.diet_plan_id))

        plan_id = id_result.unwrap()
        plan = await self._repo.get_by_id_for_user(plan_id, query.user_id)
        if plan is None:
            return Failure(DietPlanNotFoundError(diet_plan_id=query.diet_plan_id))

        return Success(DietPlanDTO.from_aggregate(plan))
