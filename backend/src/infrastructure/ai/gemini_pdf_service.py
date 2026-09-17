"""GeminiPdfParser — infrastructure implementation of DietParser using Google Gemini SDK."""
from __future__ import annotations

import json

from google import genai
from google.genai import types
from pydantic import ValidationError

from backend.src.application.errors import DietPlanProcessingError
from backend.src.application.services.diet_parser import DietParser, ParsedMenu

_MODEL = "gemini-flash-latest"
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

        try:
            response = await self._client.aio.models.generate_content(
                model=_MODEL,
                contents=[pdf_part, _PROMPT],
            )
        except Exception as exc:
            raise DietPlanProcessingError(reason=f"Gemini API error: {exc}") from exc

        raw_text = response.text or ""

        # Strip markdown code fences if Gemini wraps the JSON
        if raw_text.startswith("```"):
            parts = raw_text.split("```")
            raw_text = parts[1].removeprefix("json").strip() if len(parts) > 1 else raw_text

        try:
            raw_dict: dict = json.loads(raw_text)
        except (json.JSONDecodeError, ValueError) as exc:
            raise DietPlanProcessingError(
                reason=f"Gemini returned non-JSON response: {raw_text[:200]}"
            ) from exc

        try:
            ParsedMenu.model_validate(raw_dict)
        except ValidationError as exc:
            raise DietPlanProcessingError(
                reason=f"Gemini response does not match schema: {exc}"
            ) from exc

        return raw_dict
