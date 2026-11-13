"""In-memory implementation of PersonalRecordRepository for use case unit tests."""
from __future__ import annotations

from datetime import datetime

from backend.src.domain.estimated_one_rep_max import beats_record, estimated_one_rep_max
from backend.src.domain.repositories.personal_record_repository import (
    PersonalRecordRepository,
)


class InMemoryPersonalRecordRepository(PersonalRecordRepository):
    def __init__(self) -> None:
        # workout_exercise_id -> catalog exercise_id (seeded per test).
        self.catalog_map: dict[str, str] = {}
        # catalog exercise_id -> best estimated 1RM from prior log history.
        self.history_best_estimate: dict[str, float] = {}
        # (user_id, exercise_id) -> stored record fields.
        self.records: dict[tuple[str, str], dict[str, object]] = {}
        self.upsert_calls: list[dict[str, object]] = []
        # When True, every method raises — exercises the non-fatal PR path.
        self.raise_always = False

    def _maybe_raise(self) -> None:
        if self.raise_always:
            raise RuntimeError("simulated PR repository failure")

    async def get_catalog_exercise_ids(
        self, workout_exercise_ids: list[str]
    ) -> dict[str, str]:
        self._maybe_raise()
        return {
            we_id: self.catalog_map[we_id]
            for we_id in workout_exercise_ids
            if we_id in self.catalog_map
        }

    async def get_previous_best_estimates(
        self,
        user_id: str,
        exclude_session_id: str,
        exercise_ids: list[str],
    ) -> dict[str, float]:
        self._maybe_raise()
        return {
            ex_id: self.history_best_estimate[ex_id]
            for ex_id in exercise_ids
            if ex_id in self.history_best_estimate
        }

    async def upsert_if_higher(
        self,
        user_id: str,
        exercise_id: str,
        weight_kg: float,
        reps: int,
        session_id: str,
        achieved_at: datetime,
    ) -> bool:
        self._maybe_raise()
        self.upsert_calls.append(
            {
                "user_id": user_id,
                "exercise_id": exercise_id,
                "weight_kg": weight_kg,
                "reps": reps,
                "session_id": session_id,
                "achieved_at": achieved_at,
            }
        )
        key = (user_id, exercise_id)
        existing = self.records.get(key)
        previous = (
            None
            if existing is None
            else estimated_one_rep_max(existing["weight_kg"], existing["reps"])  # type: ignore[arg-type]
        )
        if not beats_record(estimated_one_rep_max(weight_kg, reps), previous):
            return False
        self.records[key] = {
            "weight_kg": weight_kg,
            "reps": reps,
            "session_id": session_id,
            "achieved_at": achieved_at,
        }
        return True
