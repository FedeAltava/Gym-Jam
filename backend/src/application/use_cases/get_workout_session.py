"""GetWorkoutSession use case — application layer.

Fetches a single session as an enriched history read model, scoped to the
requesting user. Used by the session detail page, which must resolve a session
by id directly instead of scanning the first page of paginated history.
"""
from __future__ import annotations

from returns.result import Failure, Result, Success

from backend.src.application.dtos import SessionHistoryItemDTO
from backend.src.application.errors import ApplicationError, SessionNotFoundError
from backend.src.domain.repositories.session_repository import SessionRepository


class GetWorkoutSessionUseCase:
    def __init__(self, session_repo: SessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(
        self, session_id: str, user_id: str
    ) -> Result[SessionHistoryItemDTO, ApplicationError]:
        # The repository query is scoped by user_id, so a session belonging to
        # another user is indistinguishable from a missing one — both return
        # None here, which is the correct behaviour for a read endpoint.
        item = await self._session_repo.get_history_item_for_user(
            user_id=user_id,
            session_id=session_id,
        )
        if item is None:
            return Failure(SessionNotFoundError(session_id=session_id))
        return Success(item)
