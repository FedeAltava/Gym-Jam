"""DeleteDietPlanUseCase — delete a diet plan (and its group variants) owned by the requesting user."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import DeleteDietPlanCommand
from backend.src.application.errors import ApplicationError, DietPlanNotFoundError
from backend.src.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.src.domain.value_objects.diet_plan_id import DietPlanId


class DeleteDietPlanUseCase:
    def __init__(self, repo: DietPlanRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: DeleteDietPlanCommand) -> Result[None, ApplicationError]:
        id_result = DietPlanId.from_string(cmd.diet_plan_id)
        if isinstance(id_result, Failure):
            return Failure(DietPlanNotFoundError(diet_plan_id=cmd.diet_plan_id))

        # Missing and foreign plans are indistinguishable to the caller (both 404),
        # so ownership leaks nothing about other users' plans.
        plan = await self._repo.get_by_id_for_user(id_result.unwrap(), cmd.user_id)
        if plan is None:
            return Failure(DietPlanNotFoundError(diet_plan_id=cmd.diet_plan_id))

        # A grouped plan is one variant of a menu: deleting it deletes the menu.
        if plan.group_id is not None:
            await self._repo.delete_group_for_user(plan.group_id, cmd.user_id)
        else:
            await self._repo.delete_for_user(plan.id, cmd.user_id)

        return Success(None)
