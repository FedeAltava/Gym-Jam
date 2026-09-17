"""ClaudePdfParser — infrastructure implementation of DietParser using Anthropic SDK."""
from __future__ import annotations

import base64
import json

import anthropic
from pydantic import ValidationError

from backend.src.application.errors import DietPlanProcessingError
from backend.src.application.services.diet_parser import DietParser, ParsedMenu

_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 4096
_PROMPT = """\
Extract the weekly meal plan from this PDF and return ONLY valid JSON with no markdown, no explanation, matching exactly this schema:
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
Weekend days (sábado, domingo) should have is_free: true for comida and cena when the PDF marks them as libre/free.
"""


class ClaudePdfParser(DietParser):
    """Calls Claude API with a base64-encoded PDF to extract a weekly menu dict."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        # Defer client construction so that DI succeeds at boot time when the
        # key is absent; the error surfaces at parse() call time instead.
        self._client: anthropic.AsyncAnthropic | None = (
            anthropic.AsyncAnthropic(api_key=api_key) if api_key else None
        )

    async def parse(self, pdf_bytes: bytes) -> dict:
        if self._client is None:
            raise DietPlanProcessingError(
                reason="ANTHROPIC_API_KEY is not configured. Set the ANTHROPIC_API_KEY environment variable."
            )
        pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

        try:
            response = await self._client.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": _PROMPT,
                            },
                        ],
                    }
                ],
            )
        except anthropic.APIError as exc:
            raise DietPlanProcessingError(reason=f"Anthropic API error: {exc}") from exc

        raw_text = response.content[0].text if response.content else ""

        try:
            raw_dict: dict = json.loads(raw_text)
        except (json.JSONDecodeError, ValueError) as exc:
            raise DietPlanProcessingError(
                reason=f"Claude returned non-JSON response: {raw_text[:200]}"
            ) from exc

        try:
            ParsedMenu.model_validate(raw_dict)
        except ValidationError as exc:
            raise DietPlanProcessingError(
                reason=f"Claude response does not match schema: {exc}"
            ) from exc

        return raw_dict
