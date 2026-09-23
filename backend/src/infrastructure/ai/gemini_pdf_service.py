"""GeminiPdfParser — infrastructure implementation of DietParser using Google Gemini SDK."""
from __future__ import annotations

import asyncio
import json

from google import genai
from google.genai import types
from pydantic import ValidationError

from backend.src.application.errors import DietPlanProcessingError
from backend.src.application.services.diet_parser import DietParser, ParsedMenu

# Fall back in order on 503/404. Gemini capacity outages are per-model, so a wider
# model list recovers faster than retrying the same overloaded model.
_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash-lite",
]
_MAX_RETRIES = 2
_RETRY_DELAY = 2.0  # seconds between retries

_PROMPT = """\
Extract the weekly meal plan from this PDF and return ONLY valid JSON with no markdown, \
no explanation, matching exactly this schema:
{
  "title": "<plan title>",
  "calories": <int or null>,
  "shared": {
    "desayuno": [{"name": "...", "ingredients": ["..."]}],
    "almuerzo_options": [{"name": "...", "ingredients": ["..."]}],
    "merienda": [{"name": "...", "ingredients": ["..."]}]
  },
  "days": [
    {
      "day": "lunes",
      "comida": {"name": "...", "ingredients": ["..."], "is_free": false},
      "cena": {"name": "...", "ingredients": ["..."], "is_free": false}
    }
  ]
}
Weekend days (sábado, domingo) should have is_free: true for comida and cena when the PDF \
marks them as libre/free.
"""


class GeminiPdfParser(DietParser):
    """Calls Gemini API with inline PDF bytes to extract a weekly menu dict."""

    def __init__(self, api_key: str) -> None:
        self._client: genai.Client | None = (
            genai.Client(api_key=api_key) if api_key else None
        )

    async def parse(self, pdf_bytes: bytes) -> dict:
        if self._client is None:
            raise DietPlanProcessingError(
                reason="GEMINI_API_KEY is not configured. Set the GEMINI_API_KEY environment variable."
            )

        pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
        last_exc: Exception | None = None

        for model in _MODELS:
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    response = await self._client.aio.models.generate_content(
                        model=model,
                        contents=[pdf_part, _PROMPT],
                    )
                    raw_text = response.text or ""

                    # Strip markdown code fences if Gemini wraps the JSON
                    if raw_text.startswith("```"):
                        parts = raw_text.split("```")
                        raw_text = parts[1].removeprefix("json").strip() if len(parts) > 1 else raw_text

                    raw_dict: dict = json.loads(raw_text)
                    ParsedMenu.model_validate(raw_dict)
                    return raw_dict

                except (json.JSONDecodeError, ValueError, ValidationError) as exc:
                    # Bad output — no point retrying the same model
                    last_exc = exc
                    break
                except Exception as exc:
                    last_exc = exc
                    is_last = attempt == _MAX_RETRIES
                    if not is_last:
                        await asyncio.sleep(_RETRY_DELAY * attempt)

        raise DietPlanProcessingError(
            reason=f"Gemini API unavailable after retries: {last_exc}"
        )
