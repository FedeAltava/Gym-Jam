"""SqlAlchemyDietPlanRepository — async SQLAlchemy implementation of DietPlanRepository."""
from __future__ import annotations

import json
from datetime import UTC

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.entities.diet_plan import DietPlan
from backend.src.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.src.domain.value_objects.diet_plan_id import DietPlanId
from backend.src.infrastructure.persistence.models import DietPlanModel


def _to_entity(model: DietPlanModel) -> DietPlan:
    menu_dict: dict = json.loads(model.menu_json)
    uploaded_at = model.uploaded_at
    # Ensure the datetime is timezone-aware (UTC) after reading from DB.
    if uploaded_at.tzinfo is None:
        uploaded_at = uploaded_at.replace(tzinfo=UTC)
    return DietPlan(
        id=DietPlanId.from_string(model.id).unwrap(),
        user_id=model.user_id,
        title=model.title,
        calories=model.calories,
        menu=menu_dict,
        uploaded_at=uploaded_at,
    )


class SqlAlchemyDietPlanRepository(DietPlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, plan: DietPlan) -> None:
        model = DietPlanModel(
            id=str(plan.id.value),
            user_id=plan.user_id,
            title=plan.title,
            calories=plan.calories,
            menu_json=json.dumps(plan.menu),
            uploaded_at=plan.uploaded_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_by_id_for_user(self, id: DietPlanId, user_id: str) -> DietPlan | None:
        result = await self._session.execute(
            select(DietPlanModel).where(
                DietPlanModel.id == str(id.value),
                DietPlanModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _to_entity(model)

    async def list_by_user(self, user_id: str) -> list[DietPlan]:
        result = await self._session.execute(
            select(DietPlanModel)
            .where(DietPlanModel.user_id == user_id)
            .order_by(DietPlanModel.uploaded_at.desc())
        )
        return [_to_entity(row) for row in result.scalars()]

    async def delete_for_user(self, id: DietPlanId, user_id: str) -> bool:
        result = await self._session.execute(
            delete(DietPlanModel).where(
                DietPlanModel.id == str(id.value),
                DietPlanModel.user_id == user_id,
            )
        )
        await self._session.flush()
        return result.rowcount > 0
