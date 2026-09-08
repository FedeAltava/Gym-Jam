"""Unit tests for UploadDietPlanUseCase — RED phase."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import UploadDietPlanCommand
from backend.src.application.dtos import DietPlanDTO
from backend.src.application.errors import DietPlanProcessingError
from backend.src.application.services.diet_parser import DietParser
from backend.src.application.use_cases.upload_diet_plan import UploadDietPlanUseCase
from backend.src.domain.entities.diet_plan import DietPlan
from backend.src.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.src.domain.value_objects.diet_plan_id import DietPlanId

_VALID_MENU: dict = {
    "title": "Plan Semana",
    "calories": 2000,
    "shared": {
        "desayuno": [{"name": "Avena", "ingredients": ["avena"]}],
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

_SMALL_PDF = b"%PDF-1.4 fake content"
_10MB_PLUS_1 = b"x" * (10 * 1024 * 1024 + 1)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeDietParser(DietParser):
    def __init__(self, result: dict | Exception) -> None:
        self._result = result

    async def parse(self, pdf_bytes: bytes) -> dict:
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class FakeDietPlanRepository(DietPlanRepository):
    def __init__(self) -> None:
        self.saved: list[DietPlan] = []

    async def save(self, plan: DietPlan) -> None:
        self.saved.append(plan)

    async def get_by_id_for_user(self, id: DietPlanId, user_id: str) -> DietPlan | None:
        return None

    async def list_by_user(self, user_id: str) -> list[DietPlan]:
        return []


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_upload_happy_path_returns_dto_and_saves_plan() -> None:
    repo = FakeDietPlanRepository()
    parser = FakeDietParser(_VALID_MENU)
    uc = UploadDietPlanUseCase(repo=repo, parser=parser)

    cmd = UploadDietPlanCommand(user_id="user-1", pdf_bytes=_SMALL_PDF, filename="plan.pdf")
    result = await uc.execute(cmd)

    assert isinstance(result, Success)
    dto = result.unwrap()
    assert isinstance(dto, DietPlanDTO)
    assert dto.user_id == "user-1"
    assert dto.title == "Plan Semana"
    assert dto.calories == 2000
    assert len(repo.saved) == 1


async def test_upload_parse_failure_returns_error_and_does_not_save() -> None:
    repo = FakeDietPlanRepository()
    parser = FakeDietParser(DietPlanProcessingError(reason="Claude returned garbage"))
    uc = UploadDietPlanUseCase(repo=repo, parser=parser)

    cmd = UploadDietPlanCommand(user_id="user-1", pdf_bytes=_SMALL_PDF, filename="plan.pdf")
    result = await uc.execute(cmd)

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DietPlanProcessingError)
    assert len(repo.saved) == 0


async def test_upload_file_too_large_returns_error_without_calling_parser() -> None:
    repo = FakeDietPlanRepository()
    # parser should never be called
    parser = FakeDietParser(_VALID_MENU)
    uc = UploadDietPlanUseCase(repo=repo, parser=parser)

    cmd = UploadDietPlanCommand(user_id="user-1", pdf_bytes=_10MB_PLUS_1, filename="big.pdf")
    result = await uc.execute(cmd)

    assert isinstance(result, Failure)
    assert len(repo.saved) == 0


async def test_upload_wrong_mime_type_returns_error() -> None:
    repo = FakeDietPlanRepository()
    parser = FakeDietParser(_VALID_MENU)
    uc = UploadDietPlanUseCase(repo=repo, parser=parser)

    cmd = UploadDietPlanCommand(
        user_id="user-1",
        pdf_bytes=b"GIF89a...",
        filename="image.gif",
    )
    result = await uc.execute(cmd)

    assert isinstance(result, Failure)
    assert len(repo.saved) == 0
