"""Standard exercise catalog seed data.

Used by test fixtures: tests create the schema via metadata.create_all, so
the migration seed never runs there and fixtures must insert these rows.

Note: alembic migration 003_add_exercise_catalog carries its own frozen copy
of these rows on purpose — migrations must never import mutable app modules.

created_at is a deterministic literal so the seed is reproducible.
"""
from datetime import UTC, datetime

_SEED_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

_CATALOG: list[dict[str, object]] = [
    # Pecho
    {"id": "bench-press", "name": "Press de banca", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "chest-press-machine", "name": "Press pecho en máquina", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "incline-press-machine", "name": "Press inclinado en máquina", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "chest-fly-machine", "name": "Aperturas en máquina", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "cable-crossover", "name": "Cruce de poleas", "muscle_group": "Pecho", "is_bodyweight": False},
    # Espalda
    {"id": "lat-pulldown", "name": "Jalón al pecho", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "gironda-row", "name": "Remo Gironda", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "pullover", "name": "Pull-over", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "machine-row", "name": "Remo en máquina", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "deadlift", "name": "Peso muerto", "muscle_group": "Espalda", "is_bodyweight": False},
    # Piernas
    {"id": "leg-press", "name": "Prensa de piernas", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "hack-squat", "name": "Sentadilla hack", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "leg-extension", "name": "Extensión de cuádriceps", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "leg-curl", "name": "Curl femoral", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "abductor", "name": "Abductor", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "adductor", "name": "Aductor", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "glute-kickback", "name": "Patada de glúteo", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "smith-squat", "name": "Sentadilla Smith", "muscle_group": "Piernas", "is_bodyweight": False},
    # Hombros
    {"id": "shoulder-press-machine", "name": "Press hombros en máquina", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "front-raise", "name": "Elevación frontal", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "lateral-raise", "name": "Elevación lateral", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "face-pull", "name": "Face pull", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "rear-delt-machine", "name": "Pájaros", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "overhead-press", "name": "Press militar", "muscle_group": "Hombros", "is_bodyweight": False},
    # Brazos
    {"id": "cable-bicep-curl", "name": "Curl de bíceps en cable", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "dumbbell-bicep-curl", "name": "Curl de bíceps con mancuerna", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "barbell-bicep-curl", "name": "Curl de bíceps con barra", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "hammer-curl", "name": "Curl martillo", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "triceps-pushdown", "name": "Extensión de tríceps en polea", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "triceps-overhead", "name": "Extensión de tríceps tras nuca", "muscle_group": "Brazos", "is_bodyweight": False},
    # Core
    {"id": "crunch-machine", "name": "Crunch abdominal", "muscle_group": "Core", "is_bodyweight": False},
    {"id": "woodchopper", "name": "Woodchopper", "muscle_group": "Core", "is_bodyweight": False},
]

EXERCISE_SEED: list[dict[str, object]] = [
    {**row, "created_at": _SEED_CREATED_AT} for row in _CATALOG
]
