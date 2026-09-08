"""Unit tests for GetDietPlanUseCase — RED phase."""
from __future__ import annotations

from datetime import UTC, datetime

from returns.result import Failure, Success

from backend.src.application.commands import GetDietPlanQuery
from backend.src.application.dtos import DietPlanDTO
from backend.src.application.errors import DietPlanNotFoundError
from backend.src.application.use_cases.get_diet_plan import GetDietPlanUseCase
from backend.src.domain.entities.diet_plan import DietPlan
from backend.src.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.src.domain.value_objects.diet_plan_id import DietPlanId

_NOW = datetime.now(UTC)
_MENU: dict = {
    "title": "Plan",
    "calories": 1800,
    "shared": {"desayuno": [], "almuerzo_options": [], "merienda": []},
    "days": [],
}


class FakeRepo(DietPlanRepository):
    def __init__(self, plan: DietPlan | None = None) -> None:
        self._plan = plan

    async def save(self, plan: DietPlan) -> None:
        pass

    async def get_by_id_for_user(self, id: DietPlanId, user_id: str) -> DietPlan | None:
        if self._plan and self._plan.id == id and self._plan.user_id == user_id:
            return self._plan
        return None

    async def list_by_user(self, user_id: str) -> list[DietPlan]:
        return []


async def test_get_existing_plan_returns_dto() -> None:
    plan_id = DietPlanId.generate()
    plan = DietPlan(id=plan_id, user_id="user-1", title="Plan", calories=1800, menu=_MENU, uploaded_at=_NOW)
    repo = FakeRepo(plan=plan)
    uc = GetDietPlanUseCase(repo=repo)

    result = await uc.execute(GetDietPlanQuery(user_id="user-1", diet_plan_id=str(plan_id.value)))

    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, DietPlanDTO)
    assert dto.title == "Plan"
    assert dto.calories == 1800


async def test_get_plan_wrong_user_returns_not_found() -> None:
    plan_id = DietPlanId.generate()
    plan = DietPlan(id=plan_id, user_id="user-1", title="Plan", calories=None, menu=_MENU, uploaded_at=_NOW)
    repo = FakeRepo(plan=plan)
    uc = GetDietPlanUseCase(repo=repo)

    result = await uc.execute(GetDietPlanQuery(user_id="user-2", diet_plan_id=str(plan_id.value)))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DietPlanNotFoundError)


async def test_get_nonexistent_plan_returns_not_found() -> None:
    repo = FakeRepo(plan=None)
    uc = GetDietPlanUseCase(repo=repo)

    result = await uc.execute(GetDietPlanQuery(user_id="user-1", diet_plan_id=str(DietPlanId.generate().value)))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DietPlanNotFoundError)
