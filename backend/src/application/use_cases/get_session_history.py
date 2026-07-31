"""GetSessionHistory use case — application layer."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone as _tz

from returns.result import Result, Success

from backend.src.application.commands import GetSessionHistoryQuery
from backend.src.application.dtos import (
    PaginatedSessionHistoryDTO,
    SessionHistoryItemDTO,
    SessionHistoryLogDTO,
)
from backend.src.application.errors import ApplicationError
from backend.src.domain.read_models import SessionSnapshot
from backend.src.domain.repositories.session_repository import SessionRepository


def _to_dto(snap: SessionSnapshot) -> SessionHistoryItemDTO:
    """Map a domain SessionSnapshot to the application-layer SessionHistoryItemDTO."""

    def _fmt(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_tz.utc)
        return dt.isoformat()

    status = "completed" if snap.completed_at is not None else "in_progress"

    duration_seconds: int | None = None
    if snap.completed_at is not None and snap.started_at is not None:
        started = snap.started_at
        completed = snap.completed_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=_tz.utc)
        if completed.tzinfo is None:
            completed = completed.replace(tzinfo=_tz.utc)
        duration_seconds = int((completed - started).total_seconds())

    return SessionHistoryItemDTO(
        id=snap.id,
        workout_id=snap.workout_id,
        training_day_id=snap.training_day_id,
        workout_name=snap.workout_name,
        day_of_week=snap.day_of_week,
        started_at=_fmt(snap.started_at) or "",
        completed_at=_fmt(snap.completed_at),
        status=status,
        logs=tuple(
            SessionHistoryLogDTO(
                id=log.id,
                workout_exercise_id=log.workout_exercise_id,
                exercise_name=log.exercise_name,
                muscle_group=log.muscle_group,
                set_number=log.set_number,
                reps_completed=log.reps_completed,
                weight_kg=log.weight_kg,
            )
            for log in snap.logs
        ),
        pr_count=snap.pr_count,
        duration_seconds=duration_seconds,
    )


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
        total, snapshots = await self._fetch(query)
        items = tuple(_to_dto(snap) for snap in snapshots)
        page_size = query.limit
        page = (query.offset // page_size) + 1 if page_size > 0 else 1
        return Success(
            PaginatedSessionHistoryDTO(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
            )
        )

    async def _fetch(self, query: GetSessionHistoryQuery):  # type: ignore[return]
        total, snapshots = await _gather(
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
        return total, snapshots


async def _gather(count_coro, list_coro):  # type: ignore[no-untyped-def]
    import asyncio
    return await asyncio.gather(count_coro, list_coro)
