"""Standard exercise catalog seed data.

Used by test fixtures: tests create the schema via metadata.create_all, so
the migration seed never runs there and fixtures must insert these rows.

Note: alembic migration 003_add_exercise_catalog carries its own frozen copy
of these rows on purpose — migrations must never import mutable app modules.

created_at is a deterministic literal so the seed is reproducible.
"""
from datetime import UTC, datetime

_SEED_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

_CATALOG: list[dict[str, str]] = [
    # Pecho
    {"id": "bench-press", "name": "Press de banca", "muscle_group": "Pecho"},
    {"id": "incline-bench-press", "name": "Press inclinado", "muscle_group": "Pecho"},
    {"id": "push-up", "name": "Flexiones", "muscle_group": "Pecho"},
    # Espalda
    {"id": "pull-up", "name": "Dominadas", "muscle_group": "Espalda"},
    {"id": "lat-pulldown", "name": "Jalón al pecho", "muscle_group": "Espalda"},
    {"id": "barbell-row", "name": "Remo con barra", "muscle_group": "Espalda"},
    {"id": "deadlift", "name": "Peso muerto", "muscle_group": "Espalda"},
    # Piernas
    {"id": "squat", "name": "Sentadilla", "muscle_group": "Piernas"},
    {"id": "front-squat", "name": "Sentadilla frontal", "muscle_group": "Piernas"},
    {"id": "leg-press", "name": "Prensa de piernas", "muscle_group": "Piernas"},
    {"id": "lunge", "name": "Zancadas", "muscle_group": "Piernas"},
    {"id": "leg-curl", "name": "Curl femoral", "muscle_group": "Piernas"},
    {"id": "calf-raise", "name": "Elevación de gemelos", "muscle_group": "Piernas"},
    # Hombros
    {"id": "overhead-press", "name": "Press militar", "muscle_group": "Hombros"},
    {"id": "lateral-raise", "name": "Elevaciones laterales", "muscle_group": "Hombros"},
    # Brazos
    {"id": "biceps-curl", "name": "Curl de bíceps", "muscle_group": "Brazos"},
    {"id": "hammer-curl", "name": "Curl martillo", "muscle_group": "Brazos"},
    {"id": "triceps-pushdown", "name": "Extensión de tríceps en polea", "muscle_group": "Brazos"},
    # Core
    {"id": "plank", "name": "Plancha", "muscle_group": "Core"},
    {"id": "crunch", "name": "Abdominales", "muscle_group": "Core"},
]

EXERCISE_SEED: list[dict[str, object]] = [
    {**row, "created_at": _SEED_CREATED_AT} for row in _CATALOG
]
