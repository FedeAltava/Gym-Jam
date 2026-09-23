"""Unit tests for GeminiPdfParser model fallback behaviour."""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.src.application.errors import DietPlanProcessingError
from backend.src.infrastructure.ai import gemini_pdf_service
from backend.src.infrastructure.ai.gemini_pdf_service import GeminiPdfParser

_VALID_MENU = {
    "title": "Plan",
    "calories": 2000,
    "shared": {"desayuno": [], "almuerzo_options": [], "merienda": []},
    "days": [
        {
            "day": "lunes",
            "comida": {"name": "Pollo", "ingredients": ["pollo"], "is_free": False},
            "cena": {"name": "Pescado", "ingredients": ["merluza"], "is_free": False},
        }
    ],
}


def _parser_with(generate: AsyncMock) -> GeminiPdfParser:
    with patch.object(gemini_pdf_service.genai, "Client") as client_cls:
        client = MagicMock()
        client.aio.models.generate_content = generate
        client_cls.return_value = client
        return GeminiPdfParser(api_key="test-key")


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gemini_pdf_service.asyncio, "sleep", AsyncMock())


async def test_falls_back_to_next_model_when_first_is_unavailable() -> None:
    first_model = gemini_pdf_service._MODELS[0]

    async def fake_generate(model: str, contents: list) -> SimpleNamespace:
        if model == first_model:
            raise RuntimeError("503 UNAVAILABLE")
        return SimpleNamespace(text=json.dumps(_VALID_MENU))

    generate = AsyncMock(side_effect=fake_generate)
    parser = _parser_with(generate)

    result = await parser.parse(b"%PDF-1.4")

    assert result == _VALID_MENU
    called_models = [call.kwargs["model"] for call in generate.await_args_list]
    assert called_models[: gemini_pdf_service._MAX_RETRIES] == [first_model] * gemini_pdf_service._MAX_RETRIES
    assert called_models[-1] == gemini_pdf_service._MODELS[1]


async def test_raises_processing_error_when_every_model_is_unavailable() -> None:
    generate = AsyncMock(side_effect=RuntimeError("503 UNAVAILABLE"))
    parser = _parser_with(generate)

    with pytest.raises(DietPlanProcessingError):
        await parser.parse(b"%PDF-1.4")

    assert generate.await_count == len(gemini_pdf_service._MODELS) * gemini_pdf_service._MAX_RETRIES
