"""GetSessionHistory use case — application layer."""
from __future__ import annotations

from returns.result import Result, Success

from backend.src.application.commands import GetSessionHistoryQuery
from backend.src.application.dtos import PaginatedSessionHistoryDTO
from backend.src.application.errors import ApplicationError
from backend.src.domain.repositories.session_repository import SessionRepository


class GetSessionHistoryUseCase:
    """Cross-workout session history, scoped to the requesting user.

    No separate ownership check for workout_id/day_id filters: the repository
    query is always scoped by user_id, so filtering by another user's workout
    simply yields an empty page (read endpoint — silent scoping is acceptable).
    """

    def __init__(self, session_repo: SessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(
        self, query: GetSessionHistoryQuery
    ) -> Result[PaginatedSessionHistoryDTO, ApplicationError]:
        total, items = await self._fetch(query)
        page_size = query.limit
        page = (query.offset // page_size) + 1 if page_size > 0 else 1
        return Success(
            PaginatedSessionHistoryDTO(
                items=tuple(items),
                total=total,
                page=page,
                page_size=page_size,
            )
        )

    async def _fetch(self, query: GetSessionHistoryQuery):  # type: ignore[return]
        total, items = await _gather(
            self._session_repo.count_history_for_user(
                user_id=query.user_id,
                workout_id=query.workout_id,
                day_id=query.day_id,
                status=query.status,
                date_from=query.date_from,
                date_to=query.date_to,
            ),
            self._session_repo.list_history_for_user(
                user_id=query.user_id,
                workout_id=query.workout_id,
                day_id=query.day_id,
                status=query.status,
                date_from=query.date_from,
                date_to=query.date_to,
                limit=query.limit,
                offset=query.offset,
            ),
        )
        return total, items


async def _gather(count_coro, list_coro):  # type: ignore[no-untyped-def]
    import asyncio
    return await asyncio.gather(count_coro, list_coro)
