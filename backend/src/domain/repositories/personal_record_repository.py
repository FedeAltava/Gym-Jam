"""PersonalRecordRepository ABC — port for personal record persistence."""
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterator


class PersonalRecordRepository(ABC):
    @asynccontextmanager
    async def savepoint(self) -> AsyncIterator[None]:
        """Override in SQL repos to wrap in a DB savepoint. Default: no-op."""
        yield
    @abstractmethod
    async def get_catalog_exercise_ids(
        self, workout_exercise_ids: list[str]
    ) -> dict[str, str]:
        """Map workout_exercise ids to catalog exercise ids.

        Personal records are keyed by catalog exercise (a user's best on
        "bench-press"), while logs reference plan rows (workout_exercises).
        Returns {workout_exercise_id: exercise_id} for the ids found.
        """
        ...

    @abstractmethod
    async def get_previous_best_estimates(
        self,
        user_id: str,
        exclude_session_id: str,
        exercise_ids: list[str],
    ) -> dict[str, float]:
        """Best estimated one-rep max (domain `estimated_one_rep_max`) ever
        logged per catalog exercise across the user's prior COMPLETED
        sessions, excluding the session being completed. Sets without weight
        (NULL or 0) never count.

        Compares against full log history (not personal_records) so the
        first post-feature session cannot award false PRs (ADR 5).
        Returns {exercise_id: best_estimate_kg}; exercises never logged are absent.
        """
        ...

    @abstractmethod
    async def upsert_if_higher(
        self,
        user_id: str,
        exercise_id: str,
        weight_kg: float,
        reps: int,
        session_id: str,
        achieved_at: datetime,
    ) -> bool:
        """Insert or update the (user, exercise) record when the set's
        estimated one-rep max beats the stored set's (domain `beats_record`).

        Returns True when a record was inserted or updated, False when the
        existing record's estimate is equal or higher (idempotent backstop, ADR 4).
        """
        ...
