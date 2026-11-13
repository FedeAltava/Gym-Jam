"""GetLastSets use case — application layer."""
from __future__ import annotations

from returns.result import Result, Success

from backend.src.application.dtos import LastSetDTO
from backend.src.application.errors import ApplicationError
from backend.src.domain.repositories.session_repository import SessionRepository


class GetLastSetsUseCase:
    """Latest logged set per set number of each requested catalog exercise,
    across all of the user's routines and days. Seeds the set suggestions of a
    session, also after swapping an exercise for another one."""

    def __init__(self, session_repo: SessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(self, user_id: str, exercise_ids: list[str]) -> Result[list[LastSetDTO], ApplicationError]:
        sets = await self._session_repo.get_last_sets_for_user(user_id, sorted(set(exercise_ids)))
        return Success(
            [
                LastSetDTO(
                    exercise_id=s.exercise_id,
                    set_number=s.set_number,
                    reps_completed=s.reps_completed,
                    weight_kg=s.weight_kg,
                )
                for s in sets
            ]
        )
