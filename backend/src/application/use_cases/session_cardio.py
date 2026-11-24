"""Session cardio use cases — record and delete treadmill cardio in a session."""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.commands import AddCardioEntryCommand, DeleteCardioEntryCommand
from backend.src.application.dtos import CardioEntryDTO
from backend.src.application.errors import (
    ApplicationError,
    CardioEntryNotFoundError,
    DomainViolationError,
    SessionNotFoundError,
    UnauthorizedError,
)
from backend.src.domain.entities.workout_session import WorkoutSession
from backend.src.domain.errors.session_errors import InvalidCardioEntry
from backend.src.domain.repositories.session_repository import SessionRepository
from backend.src.domain.value_objects.cardio_entry_id import CardioEntryId
from backend.src.domain.value_objects.workout_session_id import WorkoutSessionId


async def _load_owned_session(
    session_repo: SessionRepository, session_id: str, user_id: str
) -> Result[WorkoutSession, ApplicationError]:
    session_id_result = WorkoutSessionId.from_string(session_id)
    if isinstance(session_id_result, Failure):
        return Failure(SessionNotFoundError(session_id=session_id))
    session = await session_repo.get_by_id(session_id_result.unwrap())
    if session is None:
        return Failure(SessionNotFoundError(session_id=session_id))
    if session.user_id != user_id:
        return Failure(UnauthorizedError(user_id=user_id, workout_id=str(session.workout_id.value)))
    return Success(session)


class AddCardioEntryUseCase:
    def __init__(self, session_repo: SessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(self, cmd: AddCardioEntryCommand) -> Result[CardioEntryDTO, ApplicationError]:
        loaded = await _load_owned_session(self._session_repo, cmd.session_id, cmd.user_id)
        if isinstance(loaded, Failure):
            return loaded
        session = loaded.unwrap()

        try:
            entry = session.add_cardio(
                duration_minutes=cmd.duration_minutes,
                distance_km=cmd.distance_km,
                speed_kmh=cmd.speed_kmh,
                incline_percent=cmd.incline_percent,
                calories=cmd.calories,
            )
        except InvalidCardioEntry as e:
            return Failure(DomainViolationError(domain_error=e, message=str(e)))

        await self._session_repo.save(session)
        return Success(CardioEntryDTO.from_entity(entry))


class DeleteCardioEntryUseCase:
    def __init__(self, session_repo: SessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(self, cmd: DeleteCardioEntryCommand) -> Result[None, ApplicationError]:
        loaded = await _load_owned_session(self._session_repo, cmd.session_id, cmd.user_id)
        if isinstance(loaded, Failure):
            return loaded
        session = loaded.unwrap()

        # An entry of another session is simply absent here — same 404 as a
        # nonexistent entry.
        entry_id_result = CardioEntryId.from_string(cmd.entry_id)
        if isinstance(entry_id_result, Failure):
            return Failure(CardioEntryNotFoundError(entry_id=cmd.entry_id))
        if isinstance(session.remove_cardio(entry_id_result.unwrap()), Failure):
            return Failure(CardioEntryNotFoundError(entry_id=cmd.entry_id))

        await self._session_repo.save(session)
        return Success(None)
