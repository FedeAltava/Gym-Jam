"""Integration tests for SqlAlchemyDietPlanRepository — SQLite in-memory."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.src.domain.entities.diet_plan import DietPlan
from backend.src.domain.value_objects.diet_plan_id import DietPlanId
from backend.src.infrastructure.persistence.diet_plan_repository import SqlAlchemyDietPlanRepository

_MENU: dict = {
    "title": "Plan Prueba",
    "calories": 2000,
    "shared": {
        "desayuno": [{"name": "Avena", "ingredients": ["avena", "leche"]}],
        "almuerzo_options": [],
        "merienda": [],
    },
    "days": [
        {
            "day": "lunes",
            "comida": {"name": "Pollo", "ingredients": ["pollo"], "is_free": False},
            "cena": {"name": "Sopa", "ingredients": ["verduras"], "is_free": False},
        }
    ],
}


def _make_plan(user_id: str = "user-1", title: str = "Plan A", uploaded_at: datetime | None = None) -> DietPlan:
    return DietPlan(
        id=DietPlanId.generate(),
        user_id=user_id,
        title=title,
        calories=2000,
        menu=_MENU,
        uploaded_at=uploaded_at or datetime.now(UTC),
    )


async def test_save_and_get_by_id_for_user_roundtrip(session) -> None:
    repo = SqlAlchemyDietPlanRepository(session)
    plan = _make_plan()
    await repo.save(plan)

    loaded = await repo.get_by_id_for_user(plan.id, "user-1")

    assert loaded is not None
    assert loaded.id == plan.id
    assert loaded.title == "Plan A"
    assert loaded.calories == 2000
    assert loaded.menu == _MENU
    assert loaded.user_id == "user-1"


async def test_get_by_id_for_user_wrong_user_returns_none(session) -> None:
    repo = SqlAlchemyDietPlanRepository(session)
    plan = _make_plan(user_id="user-1")
    await repo.save(plan)

    result = await repo.get_by_id_for_user(plan.id, "user-2")

    assert result is None


async def test_get_by_id_for_user_unknown_id_returns_none(session) -> None:
    repo = SqlAlchemyDietPlanRepository(session)

    result = await repo.get_by_id_for_user(DietPlanId.generate(), "user-1")

    assert result is None


async def test_list_by_user_returns_all_user_plans(session) -> None:
    repo = SqlAlchemyDietPlanRepository(session)
    plan_a = _make_plan(user_id="user-a", title="Plan A")
    plan_b = _make_plan(user_id="user-a", title="Plan B")
    await repo.save(plan_a)
    await repo.save(plan_b)

    result = await repo.list_by_user("user-a")

    assert len(result) == 2
    titles = {p.title for p in result}
    assert titles == {"Plan A", "Plan B"}


async def test_list_by_user_returns_newest_first(session) -> None:
    repo = SqlAlchemyDietPlanRepository(session)
    now = datetime.now(UTC)
    older = _make_plan(user_id="user-order", title="Older", uploaded_at=now - timedelta(hours=2))
    newer = _make_plan(user_id="user-order", title="Newer", uploaded_at=now)
    await repo.save(older)
    await repo.save(newer)

    result = await repo.list_by_user("user-order")

    assert result[0].title == "Newer"
    assert result[1].title == "Older"


async def test_list_by_user_cross_user_isolation(session) -> None:
    repo = SqlAlchemyDietPlanRepository(session)
    plan_a = _make_plan(user_id="user-alice", title="Alice Plan")
    plan_b = _make_plan(user_id="user-bob", title="Bob Plan")
    await repo.save(plan_a)
    await repo.save(plan_b)

    alice_plans = await repo.list_by_user("user-alice")
    bob_plans = await repo.list_by_user("user-bob")

    assert len(alice_plans) == 1
    assert alice_plans[0].title == "Alice Plan"
    assert len(bob_plans) == 1
    assert bob_plans[0].title == "Bob Plan"


async def test_list_by_user_empty_returns_empty_list(session) -> None:
    repo = SqlAlchemyDietPlanRepository(session)

    result = await repo.list_by_user("user-with-no-plans")

    assert result == []
