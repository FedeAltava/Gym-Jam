"""DayName frozen dataclass — domain value object."""
from dataclasses import dataclass

from backend.src.domain.value_objects.day_of_week import DayOfWeek

_NAMES: dict[DayOfWeek, str] = {
    DayOfWeek.MONDAY: "Lunes",
    DayOfWeek.TUESDAY: "Martes",
    DayOfWeek.WEDNESDAY: "Miércoles",
    DayOfWeek.THURSDAY: "Jueves",
    DayOfWeek.FRIDAY: "Viernes",
    DayOfWeek.SATURDAY: "Sábado",
    DayOfWeek.SUNDAY: "Domingo",
}


@dataclass(frozen=True)
class DayName:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("DayName cannot be empty or whitespace")
        if len(self.value) > 50:
            raise ValueError("DayName cannot exceed 50 characters")

    @classmethod
    def for_day(cls, day: DayOfWeek) -> "DayName":
        return cls(value=_NAMES[day])
