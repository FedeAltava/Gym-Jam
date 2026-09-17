"""HTTP tests for nutrition endpoints — PR 2 TDD (T26)."""
from __future__ import annotations

import io
from unittest.mock import AsyncMock


from backend.src.application.dtos import DietPlanDTO, DietPlanSummaryDTO
from backend.src.application.errors import DietPlanNotFoundError, DietPlanProcessingError
from backend.src.application.use_cases.get_diet_plan import GetDietPlanUseCase
from backend.src.application.use_cases.list_diet_plans import ListDietPlansUseCase
from backend.src.application.use_cases.upload_diet_plan import UploadDietPlanUseCase
from backend.src.presentation.dependencies import (
    get_upload_diet_plan_use_case,
    get_list_diet_plans_use_case,
    get_get_diet_plan_use_case,
)
from datetime import datetime, timezone


# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_PLAN_ID = "00000000-0000-0000-0000-000000000099"
USER_1 = "00000000-0000-0000-0000-000000000001"

SAMPLE_MENU = {
    "title": "Weekly Plan",
    "calories": 2000,
    "shared": {
        "desayuno": [{"name": "Oatmeal", "ingredients": ["oats", "milk"]}],
        "almuerzo_options": [{"name": "Salad", "ingredients": ["lettuce"]}],
        "merienda": [{"name": "Fruit", "ingredients": ["apple"]}],
    },
    "days": [
        {
            "day": "lunes",
            "comida": {"name": "Chicken", "ingredients": ["chicken"], "is_free": False},
            "cena": {"name": "Soup", "ingredients": ["broth"], "is_free": False},
        },
        {
            "day": "sábado",
            "comida": {"name": "Free", "ingredients": [], "is_free": True},
            "cena": {"name": "Free", "ingredients": [], "is_free": True},
        },
    ],
}

SAMPLE_DTO = DietPlanDTO(
    id=VALID_PLAN_ID,
    user_id=USER_1,
    title="Weekly Plan",
    calories=2000,
    menu_json=SAMPLE_MENU,
    uploaded_at=datetime(2026, 9, 8, 12, 0, 0, tzinfo=timezone.utc),
)

SAMPLE_SUMMARY_DTO = DietPlanSummaryDTO(
    id=VALID_PLAN_ID,
    user_id=USER_1,
    title="Weekly Plan",
    calories=2000,
    uploaded_at=datetime(2026, 9, 8, 12, 0, 0, tzinfo=timezone.utc),
)


def _make_upload_uc(return_value):
    """Return a factory that produces a mock UploadDietPlanUseCase."""
    mock_uc = AsyncMock(spec=UploadDietPlanUseCase)
    mock_uc.execute.return_value = return_value

    def _factory():
        return mock_uc

    return _factory


def _make_list_uc(return_value):
    mock_uc = AsyncMock(spec=ListDietPlansUseCase)
    mock_uc.execute.return_value = return_value

    def _factory():
        return mock_uc

    return _factory


def _make_get_uc(return_value):
    mock_uc = AsyncMock(spec=GetDietPlanUseCase)
    mock_uc.execute.return_value = return_value

    def _factory():
        return mock_uc

    return _factory


def _pdf_file(size: int = 1024, content_type: str = "application/pdf") -> tuple:
    """Return (filename, file_obj, content_type) suitable for httpx multipart."""
    data = b"%PDF-1.4 fake" + b"x" * size
    return ("file", ("diet.pdf", io.BytesIO(data), content_type))


# ── POST /nutrition/menus ─────────────────────────────────────────────────────


async def test_upload_diet_plan_happy_path_returns_201(client) -> None:
    """POST /nutrition/menus with a valid PDF and mocked UC → 201 with plan data."""
    from returns.result import Success

    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_upload_diet_plan_use_case] = _make_upload_uc(Success(SAMPLE_DTO))

    r = await client.post(
        "/nutrition/menus",
        files=[_pdf_file()],
    )

    app.dependency_overrides.pop(get_upload_diet_plan_use_case, None)

    assert r.status_code == 201
    data = r.json()
    assert data["id"] == VALID_PLAN_ID
    assert data["title"] == "Weekly Plan"
    assert data["calories"] == 2000
    assert "menu_json" in data
    assert "uploaded_at" in data


async def test_upload_diet_plan_wrong_mimetype_returns_415(client) -> None:
    """Non-PDF file → 415 before calling the use case."""
    r = await client.post(
        "/nutrition/menus",
        files=[_pdf_file(content_type="image/jpeg")],
    )

    assert r.status_code == 415


async def test_upload_diet_plan_file_too_large_returns_413(client) -> None:
    """File exceeding 10 MB → 413."""
    # 10 MB + 1 byte
    r = await client.post(
        "/nutrition/menus",
        files=[_pdf_file(size=10 * 1024 * 1024 + 1)],
    )

    assert r.status_code == 413


async def test_upload_diet_plan_requires_auth(auth_client) -> None:
    """Unauthenticated POST → 401."""
    r = await auth_client.post(
        "/nutrition/menus",
        files=[_pdf_file()],
    )

    assert r.status_code == 401


async def test_upload_diet_plan_processing_error_returns_422(client) -> None:
    """When UC returns a processing error → 422."""
    from returns.result import Failure

    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_upload_diet_plan_use_case] = _make_upload_uc(
        Failure(DietPlanProcessingError("bad JSON"))
    )

    r = await client.post(
        "/nutrition/menus",
        files=[_pdf_file()],
    )

    app.dependency_overrides.pop(get_upload_diet_plan_use_case, None)

    assert r.status_code == 422


# ── GET /nutrition/menus ──────────────────────────────────────────────────────


async def test_list_diet_plans_returns_200_with_summaries(client) -> None:
    """GET /nutrition/menus → 200 list of summaries."""
    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_list_diet_plans_use_case] = _make_list_uc([SAMPLE_SUMMARY_DTO])

    r = await client.get("/nutrition/menus")

    app.dependency_overrides.pop(get_list_diet_plans_use_case, None)

    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["id"] == VALID_PLAN_ID
    assert data[0]["title"] == "Weekly Plan"
    assert "menu_json" not in data[0]


async def test_list_diet_plans_empty_returns_empty_array(client) -> None:
    """GET /nutrition/menus with no plans → 200 []."""
    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_list_diet_plans_use_case] = _make_list_uc([])

    r = await client.get("/nutrition/menus")

    app.dependency_overrides.pop(get_list_diet_plans_use_case, None)

    assert r.status_code == 200
    # Prove the empty list comes from real logic (UC returned []):
    assert r.json() == []


async def test_list_diet_plans_requires_auth(auth_client) -> None:
    """Unauthenticated GET /nutrition/menus → 401."""
    r = await auth_client.get("/nutrition/menus")

    assert r.status_code == 401


# ── GET /nutrition/menus/{id} ─────────────────────────────────────────────────


async def test_get_diet_plan_found_returns_200(client) -> None:
    """GET /nutrition/menus/{id} for owned plan → 200 with full menu_json."""
    from returns.result import Success

    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_get_diet_plan_use_case] = _make_get_uc(Success(SAMPLE_DTO))

    r = await client.get(f"/nutrition/menus/{VALID_PLAN_ID}")

    app.dependency_overrides.pop(get_get_diet_plan_use_case, None)

    assert r.status_code == 200
    data = r.json()
    assert data["id"] == VALID_PLAN_ID
    assert "menu_json" in data
    assert data["menu_json"]["title"] == "Weekly Plan"


async def test_get_diet_plan_not_found_returns_404(client) -> None:
    """GET /nutrition/menus/{id} when plan not owned by user → 404."""
    from returns.result import Failure

    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_get_diet_plan_use_case] = _make_get_uc(
        Failure(DietPlanNotFoundError(VALID_PLAN_ID))
    )

    r = await client.get(f"/nutrition/menus/{VALID_PLAN_ID}")

    app.dependency_overrides.pop(get_get_diet_plan_use_case, None)

    assert r.status_code == 404


async def test_get_diet_plan_requires_auth(auth_client) -> None:
    """Unauthenticated GET /nutrition/menus/{id} → 401."""
    r = await auth_client.get(f"/nutrition/menus/{VALID_PLAN_ID}")

    assert r.status_code == 401


# ── Triangulation: summary omits menu_json, response includes it ─────────────


async def test_list_response_does_not_include_menu_json(client) -> None:
    """Summary items must NOT expose menu_json — it is the heavy field."""
    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_list_diet_plans_use_case] = _make_list_uc([SAMPLE_SUMMARY_DTO])

    r = await client.get("/nutrition/menus")

    app.dependency_overrides.pop(get_list_diet_plans_use_case, None)

    assert r.status_code == 200
    item = r.json()[0]
    # Summary MUST have these fields
    assert item["id"] == VALID_PLAN_ID
    assert item["calories"] == 2000
    # Summary MUST NOT include menu_json
    assert "menu_json" not in item


async def test_get_response_includes_full_menu_json(client) -> None:
    """Detail response MUST include menu_json with full nested structure."""
    from returns.result import Success

    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_get_diet_plan_use_case] = _make_get_uc(Success(SAMPLE_DTO))

    r = await client.get(f"/nutrition/menus/{VALID_PLAN_ID}")

    app.dependency_overrides.pop(get_get_diet_plan_use_case, None)

    assert r.status_code == 200
    data = r.json()
    # Full response MUST include menu_json with the expected nested keys
    menu = data["menu_json"]
    assert menu["calories"] == 2000
    assert "shared" in menu
    assert len(menu["days"]) == 2
    # Weekend day must be is_free: true
    saturday = next(d for d in menu["days"] if d["day"] == "sábado")
    assert saturday["comida"]["is_free"] is True
    assert saturday["cena"]["is_free"] is True
