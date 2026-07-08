"""PersonalRecordRepository ABC — port for personal record persistence."""
from abc import ABC, abstractmethod
from datetime import datetime


class PersonalRecordRepository(ABC):
    @abstractmethod
    async def get_catalog_exercise_ids(
        self, workout_exercise_ids: list[str]
    ) -> dict[str, str]:
        """Map workout_exercise ids to catalog exercise ids.

        Personal records are keyed by catalog exercise (a user's max on
        "bench-press"), while logs reference plan rows (workout_exercises).
        Returns {workout_exercise_id: exercise_id} for the ids found.
        """
        ...

    @abstractmethod
    async def get_previous_max_weights(
        self,
        user_id: str,
        exclude_session_id: str,
        exercise_ids: list[str],
    ) -> dict[str, float]:
        """Max weight ever logged per catalog exercise across the user's
        prior COMPLETED sessions, excluding the session being completed.

        Compares against full log history (not personal_records) so the
        first post-feature session cannot award false PRs (ADR 5).
        Returns {exercise_id: max_weight_kg}; exercises never logged are absent.
        """
        ...

    @abstractmethod
    async def upsert_if_higher(
        self,
        user_id: str,
        exercise_id: str,
        weight_kg: float,
        session_id: str,
        achieved_at: datetime,
    ) -> bool:
        """Insert or update the (user, exercise) record if weight_kg beats it.

        Returns True when a record was inserted or updated, False when the
        existing record is equal or heavier (idempotent backstop, ADR 4).
        """
        ...
