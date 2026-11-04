"""Body weight use cases — record, list and delete a user's weigh-ins."""
from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from returns.result import Failure, Result, Success

from backend.src.application.commands import DeleteBodyWeightCommand, RecordBodyWeightCommand
from backend.src.application.dtos import BodyWeightEntryDTO
from backend.src.application.errors import (
    ApplicationError,
    BodyWeightEntryNotFoundError,
    InvalidBodyWeightError,
)
from backend.src.domain.entities.body_weight_entry import (
    MAX_WEIGHT_KG,
    BodyWeightEntry,
    BodyWeightError,
)
from backend.src.domain.repositories.body_weight_repository import BodyWeightRepository

_MESSAGES = {
    BodyWeightError.INVALID_WEIGHT: f"Weight must be greater than 0 and at most {MAX_WEIGHT_KG:g} kg.",
    BodyWeightError.DATE_IN_FUTURE: "The date cannot be in the future.",
}


class RecordBodyWeightUseCase:
    def __init__(
        self,
        repo: BodyWeightRepository,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repo = repo
        self._clock = clock

    async def execute(self, cmd: RecordBodyWeightCommand) -> Result[BodyWeightEntryDTO, ApplicationError]:
        # The client sends its local date; users ahead of UTC are already on
        # the next UTC day, so allow one day of slack.
        latest_allowed = self._clock().date() + timedelta(days=1)
        result = BodyWeightEntry.record(
            user_id=cmd.user_id,
            measured_on=cmd.measured_on,
            weight_kg=cmd.weight_kg,
            latest_allowed=latest_allowed,
        )
        if isinstance(result, Failure):
            return Failure(InvalidBodyWeightError(message=_MESSAGES[result.failure()]))
        entry = result.unwrap()
        await self._repo.save(entry)
        return Success(BodyWeightEntryDTO.from_entity(entry))


class ListBodyWeightUseCase:
    def __init__(self, repo: BodyWeightRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: str) -> Result[tuple[BodyWeightEntryDTO, ...], ApplicationError]:
        entries = await self._repo.list_by_user(user_id)
        return Success(tuple(BodyWeightEntryDTO.from_entity(e) for e in entries))


class DeleteBodyWeightUseCase:
    def __init__(self, repo: BodyWeightRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: DeleteBodyWeightCommand) -> Result[None, ApplicationError]:
        # Entries are scoped by user_id, so another user's day is simply missing.
        if not await self._repo.delete_for_user(cmd.user_id, cmd.measured_on):
            return Failure(BodyWeightEntryNotFoundError(measured_on=cmd.measured_on.isoformat()))
        return Success(None)
