"""Exercise catalog entity."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    id: str
    name: str
    muscle_group: str
    is_bodyweight: bool = False  # no external weight, e.g. push-up, plank
