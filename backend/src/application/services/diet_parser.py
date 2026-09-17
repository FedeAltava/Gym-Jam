"""DietParser port — abstract base class for PDF-to-menu extraction.

Also defines ParsedMenu and its sub-models used by UploadDietPlanUseCase
to validate Claude's output before constructing the DietPlan entity.
"""
from abc import ABC, abstractmethod

from pydantic import BaseModel


class MealOption(BaseModel):
    name: str
    ingredients: list[str]


class DayMeal(BaseModel):
    name: str
    ingredients: list[str]
    is_free: bool = False


class SharedMeals(BaseModel):
    desayuno: list[MealOption] = []
    almuerzo_options: list[MealOption] = []
    merienda: list[MealOption] = []


class DayMenu(BaseModel):
    day: str  # "lunes", "martes", etc.
    comida: DayMeal
    cena: DayMeal


class ParsedMenu(BaseModel):
    title: str
    calories: int | None = None
    shared: SharedMeals
    days: list[DayMenu]


class DietParser(ABC):
    """Port for parsing a PDF file into a structured menu dict.

    Implementations live in infrastructure/ai. Raises DietPlanProcessingError
    on malformed or unparse-able output.
    """

    @abstractmethod
    async def parse(self, pdf_bytes: bytes) -> dict: ...
