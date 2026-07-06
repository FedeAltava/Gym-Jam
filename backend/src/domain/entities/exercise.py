"""Exercise catalog entity."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    id: str                      # slug for global; UUID for custom
    name: str
    muscle_group: str
    is_bodyweight: bool = False  # no external weight, e.g. push-up, plank
    owner_id: str | None = None  # None = global catalog; str = user-created
