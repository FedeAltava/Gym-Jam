"""Unit tests for ListDietPlansUseCase — RED phase."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.src.application.commands import ListDietPlansQuery
from backend.src.application.dtos import DietPlanSummaryDTO
from backend.src.application.use_cases.list_diet_plans import ListDietPlansUseCase
from backend.src.domain.entities.diet_plan import DietPlan
from backend.src.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.src.domain.value_objects.diet_plan_id import DietPlanId

_NOW = datetime.now(UTC)
_MENU: dict = {"title": "x", "calories": None, "shared": {"desayuno": [], "almuerzo_options": [], "merienda": []}, "days": []}


class FakeRepo(DietPlanRepository):
    def __init__(self, plans: list[DietPlan]) -> None:
        self._plans = plans

    async def save(self, plan: DietPlan) -> None:
        pass

    async def get_by_id_for_user(self, id: DietPlanId, user_id: str) -> DietPlan | None:
        return None

    async def list_by_user(self, user_id: str) -> list[DietPlan]:
        return [p for p in self._plans if p.user_id == user_id]


def _make_plan(user_id: str, title: str, uploaded_at: datetime) -> DietPlan:
    return DietPlan(
        id=DietPlanId.generate(),
        user_id=user_id,
        title=title,
        calories=None,
        menu=_MENU,
        uploaded_at=uploaded_at,
    )


async def test_list_returns_summaries_for_user() -> None:
    plan = _make_plan("user-1", "Plan A", _NOW)
    repo = FakeRepo([plan])
    uc = ListDietPlansUseCase(repo=repo)

    result = await uc.execute(ListDietPlansQuery(user_id="user-1"))

    assert len(result) == 1
    assert isinstance(result[0], DietPlanSummaryDTO)
    assert result[0].title == "Plan A"
    assert result[0].user_id == "user-1"


async def test_list_returns_empty_for_user_with_no_plans() -> None:
    repo = FakeRepo([])
    uc = ListDietPlansUseCase(repo=repo)

    result = await uc.execute(ListDietPlansQuery(user_id="user-x"))

    assert result == []


async def test_list_isolates_by_user() -> None:
    plan_a = _make_plan("user-a", "Plan A1", _NOW)
    plan_b = _make_plan("user-b", "Plan B1", _NOW - timedelta(hours=1))
    repo = FakeRepo([plan_a, plan_b])
    uc = ListDietPlansUseCase(repo=repo)

    result = await uc.execute(ListDietPlansQuery(user_id="user-a"))

    assert len(result) == 1
    assert result[0].user_id == "user-a"
