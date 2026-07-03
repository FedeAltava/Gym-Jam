from __future__ import annotations

from pydantic import BaseModel

from backend.src.application.dtos import ExerciseDTO


class ExerciseResponse(BaseModel):
    id: str
    name: str
    muscle_group: str

    @classmethod
    def from_dto(cls, dto: ExerciseDTO) -> ExerciseResponse:
        return cls(id=dto.id, name=dto.name, muscle_group=dto.muscle_group)
