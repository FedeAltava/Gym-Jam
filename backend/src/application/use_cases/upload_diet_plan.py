"""UploadDietPlanUseCase — parse a PDF diet plan and persist it."""
from __future__ import annotations

from datetime import UTC, datetime

from pydantic import ValidationError
from returns.result import Failure, Result, Success

from backend.src.application.commands import UploadDietPlanCommand
from backend.src.application.dtos import DietPlanDTO
from backend.src.application.errors import ApplicationError, DietPlanProcessingError
from backend.src.application.services.diet_parser import DietParser, ParsedMenu
from backend.src.domain.entities.diet_plan import DietPlan
from backend.src.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.src.domain.value_objects.diet_plan_id import DietPlanId

_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class UploadDietPlanUseCase:
    def __init__(self, repo: DietPlanRepository, parser: DietParser) -> None:
        self._repo = repo
        self._parser = parser

    async def execute(self, cmd: UploadDietPlanCommand) -> Result[DietPlanDTO, ApplicationError]:
        # 1. Validate file size
        if len(cmd.pdf_bytes) > _MAX_SIZE_BYTES:
            return Failure(
                DietPlanProcessingError(
                    reason=f"File exceeds maximum size of {_MAX_SIZE_BYTES // (1024 * 1024)} MB."
                )
            )

        # 2. Validate MIME type by filename extension
        if not cmd.filename.lower().endswith(".pdf"):
            return Failure(
                DietPlanProcessingError(
                    reason=f"File '{cmd.filename}' is not a PDF. Only PDF files are accepted."
                )
            )

        # 3. Call parser (DietParser port — may raise DietPlanProcessingError)
        try:
            raw_dict = await self._parser.parse(cmd.pdf_bytes)
        except DietPlanProcessingError as exc:
            return Failure(exc)

        # 4. Validate parsed output against schema
        try:
            parsed = ParsedMenu.model_validate(raw_dict)
        except ValidationError as exc:
            return Failure(
                DietPlanProcessingError(reason=f"Claude response does not match schema: {exc}")
            )

        # 5. Build entity
        plan = DietPlan(
            id=DietPlanId.generate(),
            user_id=cmd.user_id,
            title=parsed.title,
            calories=parsed.calories,
            menu=raw_dict,
            uploaded_at=datetime.now(UTC),
        )

        # 6. Persist
        await self._repo.save(plan)

        # 7. Return DTO
        return Success(DietPlanDTO.from_aggregate(plan))
