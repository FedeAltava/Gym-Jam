"""Unit tests for DeleteDietPlanUseCase."""
from __future__ import annotations

from datetime import UTC, datetime

from returns.result import Failure, Success

from backend.src.application.commands import DeleteDietPlanCommand
from backend.src.application.errors import DietPlanNotFoundError
from backend.src.application.use_cases.delete_diet_plan import DeleteDietPlanUseCase
from backend.src.domain.entities.diet_plan import DietPlan
from backend.src.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.src.domain.value_objects.diet_plan_id import DietPlanId

_MENU: dict = {
    "title": "Plan",
    "calories": 1800,
    "shared": {"desayuno": [], "almuerzo_options": [], "merienda": []},
    "days": [],
}


class FakeRepo(DietPlanRepository):
    def __init__(self, plans: list[DietPlan] | None = None) -> None:
        self.plans = list(plans or [])

    async def save(self, plan: DietPlan) -> None:
        self.plans.append(plan)

    async def get_by_id_for_user(self, id: DietPlanId, user_id: str) -> DietPlan | None:
        return next((p for p in self.plans if p.id == id and p.user_id == user_id), None)

    async def list_by_user(self, user_id: str) -> list[DietPlan]:
        return [p for p in self.plans if p.user_id == user_id]

    async def delete_for_user(self, id: DietPlanId, user_id: str) -> bool:
        before = len(self.plans)
        self.plans = [p for p in self.plans if not (p.id == id and p.user_id == user_id)]
        return len(self.plans) < before


def _plan(user_id: str = "user-1") -> DietPlan:
    return DietPlan(
        id=DietPlanId.generate(),
        user_id=user_id,
        title="Plan",
        calories=1800,
        menu=_MENU,
        uploaded_at=datetime.now(UTC),
    )


async def test_delete_own_plan_succeeds_and_removes_it() -> None:
    plan = _plan()
    repo = FakeRepo([plan])
    uc = DeleteDietPlanUseCase(repo=repo)

    result = await uc.execute(DeleteDietPlanCommand(user_id="user-1", diet_plan_id=str(plan.id.value)))

    assert isinstance(result, Success)
    assert repo.plans == []


async def test_delete_other_users_plan_returns_not_found_and_keeps_it() -> None:
    plan = _plan(user_id="user-1")
    repo = FakeRepo([plan])
    uc = DeleteDietPlanUseCase(repo=repo)

    result = await uc.execute(DeleteDietPlanCommand(user_id="user-2", diet_plan_id=str(plan.id.value)))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DietPlanNotFoundError)
    assert repo.plans == [plan]


async def test_delete_nonexistent_plan_returns_not_found() -> None:
    uc = DeleteDietPlanUseCase(repo=FakeRepo())

    result = await uc.execute(
        DeleteDietPlanCommand(user_id="user-1", diet_plan_id=str(DietPlanId.generate().value))
    )

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DietPlanNotFoundError)


async def test_delete_malformed_id_returns_not_found() -> None:
    uc = DeleteDietPlanUseCase(repo=FakeRepo())

    result = await uc.execute(DeleteDietPlanCommand(user_id="user-1", diet_plan_id="not-a-uuid"))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DietPlanNotFoundError)
