from __future__ import annotations

from pydantic import BaseModel, Field

from backend.src.application.dtos import ExerciseDTO


class ExerciseResponse(BaseModel):
    id: str
    name: str
    muscle_group: str
    is_bodyweight: bool
    is_custom: bool

    @classmethod
    def from_dto(cls, dto: ExerciseDTO) -> ExerciseResponse:
        return cls(
            id=dto.id,
            name=dto.name,
            muscle_group=dto.muscle_group,
            is_bodyweight=dto.is_bodyweight,
            is_custom=dto.owner_id is not None,
        )


class CreateExerciseRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    muscle_group: str = Field(min_length=1, max_length=50)
    is_bodyweight: bool = False
