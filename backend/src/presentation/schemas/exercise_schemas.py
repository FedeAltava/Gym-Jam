from __future__ import annotations

from pydantic import BaseModel

from backend.src.application.dtos import ExerciseDTO, LastSetDTO


class ExerciseResponse(BaseModel):
    id: str
    name: str
    muscle_group: str
    is_bodyweight: bool

    @classmethod
    def from_dto(cls, dto: ExerciseDTO) -> ExerciseResponse:
        return cls(
            id=dto.id,
            name=dto.name,
            muscle_group=dto.muscle_group,
            is_bodyweight=dto.is_bodyweight,
        )


class LastSetResponse(BaseModel):
    exercise_id: str
    set_number: int
    reps_completed: int
    weight_kg: float | None

    @classmethod
    def from_dto(cls, dto: LastSetDTO) -> LastSetResponse:
        return cls(
            exercise_id=dto.exercise_id,
            set_number=dto.set_number,
            reps_completed=dto.reps_completed,
            weight_kg=dto.weight_kg,
        )
