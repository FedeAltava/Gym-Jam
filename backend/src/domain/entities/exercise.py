"""Exercise catalog entity — read-model, identified by slug."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    id: str            # slug, e.g. "bench-press"
    name: str          # Spanish display name, e.g. "Press de banca"
    muscle_group: str  # Spanish muscle group, e.g. "Pecho"
