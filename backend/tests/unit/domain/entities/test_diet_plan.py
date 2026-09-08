"""Unit tests for DietPlan entity — RED phase."""
from __future__ import annotations

from datetime import UTC, datetime

from backend.src.domain.entities.diet_plan import DietPlan
from backend.src.domain.value_objects.diet_plan_id import DietPlanId

_SAMPLE_MENU: dict = {
    "title": "Plan Semana 1",
    "calories": 2000,
    "shared": {
        "desayuno": [{"name": "Avena", "ingredients": ["avena", "leche"]}],
        "almuerzo_options": [],
        "merienda": [],
    },
    "days": [
        {
            "day": "lunes",
            "comida": {"name": "Pollo", "ingredients": ["pollo", "arroz"], "is_free": False},
            "cena": {"name": "Ensalada", "ingredients": ["lechuga"], "is_free": False},
        }
    ],
}


def test_diet_plan_construction_with_all_fields() -> None:
    plan_id = DietPlanId.generate()
    uploaded = datetime.now(UTC)
    plan = DietPlan(
        id=plan_id,
        user_id="user-1",
        title="Plan Semana 1",
        calories=2000,
        menu=_SAMPLE_MENU,
        uploaded_at=uploaded,
    )
    assert plan.id == plan_id
    assert plan.user_id == "user-1"
    assert plan.title == "Plan Semana 1"
    assert plan.calories == 2000
    assert plan.menu == _SAMPLE_MENU
    assert plan.uploaded_at == uploaded


def test_diet_plan_calories_can_be_none() -> None:
    plan = DietPlan(
        id=DietPlanId.generate(),
        user_id="user-1",
        title="Plan Sin Calorias",
        calories=None,
        menu=_SAMPLE_MENU,
        uploaded_at=datetime.now(UTC),
    )
    assert plan.calories is None


def test_diet_plan_equality_by_id() -> None:
    plan_id = DietPlanId.generate()
    uploaded = datetime.now(UTC)
    plan_a = DietPlan(id=plan_id, user_id="user-1", title="A", calories=None, menu={}, uploaded_at=uploaded)
    plan_b = DietPlan(id=plan_id, user_id="user-2", title="B", calories=2000, menu={}, uploaded_at=uploaded)
    assert plan_a == plan_b


def test_diet_plan_different_ids_are_not_equal() -> None:
    uploaded = datetime.now(UTC)
    plan_a = DietPlan(id=DietPlanId.generate(), user_id="user-1", title="A", calories=None, menu={}, uploaded_at=uploaded)
    plan_b = DietPlan(id=DietPlanId.generate(), user_id="user-1", title="A", calories=None, menu={}, uploaded_at=uploaded)
    assert plan_a != plan_b
