"""Standard exercise catalog seed data.

Used by test fixtures: tests create the schema via metadata.create_all, so
the migration seed never runs there and fixtures must insert these rows.

Note: alembic migration 003_add_exercise_catalog carries its own frozen copy
of these rows on purpose — migrations must never import mutable app modules.

created_at is a deterministic literal so the seed is reproducible.
"""
from datetime import UTC, datetime

_SEED_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

# Every row carries is_bodyweight explicitly: conftest bulk-inserts this list
# via a single executemany, which requires homogeneous keys across all rows.
_CATALOG: list[dict[str, object]] = [
    # Pecho
    {"id": "bench-press", "name": "Press de banca", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "incline-bench-press", "name": "Press inclinado", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "push-up", "name": "Flexiones", "muscle_group": "Pecho", "is_bodyweight": True},
    # Espalda
    {"id": "pull-up", "name": "Dominadas", "muscle_group": "Espalda", "is_bodyweight": True},
    {"id": "lat-pulldown", "name": "Jalón al pecho", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "barbell-row", "name": "Remo con barra", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "deadlift", "name": "Peso muerto", "muscle_group": "Espalda", "is_bodyweight": False},
    # Piernas
    {"id": "squat", "name": "Sentadilla", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "front-squat", "name": "Sentadilla frontal", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "leg-press", "name": "Prensa de piernas", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "lunge", "name": "Zancadas", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "leg-curl", "name": "Curl femoral", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "calf-raise", "name": "Elevación de gemelos", "muscle_group": "Piernas", "is_bodyweight": False},
    # Hombros
    {"id": "overhead-press", "name": "Press militar", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "lateral-raise", "name": "Elevaciones laterales", "muscle_group": "Hombros", "is_bodyweight": False},
    # Brazos
    {"id": "biceps-curl", "name": "Curl de bíceps", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "hammer-curl", "name": "Curl martillo", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "triceps-pushdown", "name": "Extensión de tríceps en polea", "muscle_group": "Brazos", "is_bodyweight": False},
    # Core
    {"id": "plank", "name": "Plancha", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "crunch", "name": "Abdominales", "muscle_group": "Core", "is_bodyweight": True},
]

EXERCISE_SEED: list[dict[str, object]] = [
    {**row, "created_at": _SEED_CREATED_AT} for row in _CATALOG
]
