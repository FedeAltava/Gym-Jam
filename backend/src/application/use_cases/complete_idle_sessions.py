"""CompleteIdleSessions use case — application layer."""
from __future__ import annotations

from datetime import datetime, timedelta

from backend.src.application.use_cases.complete_workout_session import CompleteWorkoutSessionUseCase
from backend.src.domain.repositories.session_repository import SessionRepository

# A session with no logged set for longer than this counts as finished.
IDLE_TIMEOUT = timedelta(hours=1)


class CompleteIdleSessionsUseCase:
    """Completes the user's in-progress sessions that have been idle for
    IDLE_TIMEOUT, as of their last activity, so a forgotten session neither
    blocks the next one nor inflates its duration. Runs lazily before session
    reads; there is no scheduler."""

    def __init__(
        self,
        session_repo: SessionRepository,
        completer: CompleteWorkoutSessionUseCase,
    ) -> None:
        self._session_repo = session_repo
        self._completer = completer

    async def execute(self, user_id: str, now: datetime) -> int:
        """Returns how many sessions were completed."""
        idle = await self._session_repo.list_idle_in_progress_for_user(user_id, now - IDLE_TIMEOUT)
        for session, last_activity in idle:
            await self._completer.finish(session, at=last_activity)
        return len(idle)
