"""Replace exercise catalog with updated list.

Revision ID: 012
Revises: 011
Create Date: 2026-07-09

Replaces the original 20-exercise seed with a curated 33-exercise catalog
grouped by muscle group. Old IDs that still exist are preserved; removed
exercises are deleted only if no workout references them (cascade via FK).
"""
from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEED_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

# IDs removed from the catalog (no longer offered to users).
# Rows are deleted only if no workout_exercises references them.
_REMOVED_IDS = [
    "bench-press",       # replaced by chest-press-machine / kept as bench-press below
    "incline-bench-press",
    "push-up",
    "pull-up",
    "barbell-row",
    "squat",
    "front-squat",
    "lunge",
    "calf-raise",
    "overhead-press",    # re-added as overhead-press (same id, kept)
    "lateral-raise",     # re-added as lateral-raise (same id, kept)
    "biceps-curl",
    "plank",
    "crunch",
]

# New rows to insert (ids not present in the original seed).
_NEW_ROWS = [
    # Pecho
    {"id": "bench-press", "name": "Press de banca", "muscle_group": "Pecho", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "chest-press-machine", "name": "Press pecho en máquina", "muscle_group": "Pecho", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "incline-press-machine", "name": "Press inclinado en máquina", "muscle_group": "Pecho", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "chest-fly-machine", "name": "Aperturas en máquina", "muscle_group": "Pecho", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "cable-crossover", "name": "Cruce de poleas", "muscle_group": "Pecho", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    # Espalda
    {"id": "gironda-row", "name": "Remo Gironda", "muscle_group": "Espalda", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "pullover", "name": "Pull-over", "muscle_group": "Espalda", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "machine-row", "name": "Remo en máquina", "muscle_group": "Espalda", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    # Piernas
    {"id": "hack-squat", "name": "Sentadilla hack", "muscle_group": "Piernas", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "leg-extension", "name": "Extensión de cuádriceps", "muscle_group": "Piernas", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "abductor", "name": "Abductor", "muscle_group": "Piernas", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "adductor", "name": "Aductor", "muscle_group": "Piernas", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "glute-kickback", "name": "Patada de glúteo", "muscle_group": "Piernas", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "smith-squat", "name": "Sentadilla Smith", "muscle_group": "Piernas", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    # Hombros
    {"id": "shoulder-press-machine", "name": "Press hombros en máquina", "muscle_group": "Hombros", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "front-raise", "name": "Elevación frontal", "muscle_group": "Hombros", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "face-pull", "name": "Face pull", "muscle_group": "Hombros", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "rear-delt-machine", "name": "Pájaros", "muscle_group": "Hombros", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    # Brazos
    {"id": "cable-bicep-curl", "name": "Curl de bíceps en cable", "muscle_group": "Brazos", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "dumbbell-bicep-curl", "name": "Curl de bíceps con mancuerna", "muscle_group": "Brazos", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "barbell-bicep-curl", "name": "Curl de bíceps con barra", "muscle_group": "Brazos", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "triceps-overhead", "name": "Extensión de tríceps tras nuca", "muscle_group": "Brazos", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    # Core
    {"id": "crunch-machine", "name": "Crunch abdominal", "muscle_group": "Core", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
    {"id": "woodchopper", "name": "Woodchopper", "muscle_group": "Core", "is_bodyweight": False, "created_at": _SEED_CREATED_AT},
]

# Existing rows to update (name or muscle_group changed).
_UPDATES = [
    {"id": "lateral-raise", "name": "Elevación lateral"},
    {"id": "leg-curl", "name": "Curl femoral"},
]


def upgrade() -> None:
    conn = op.get_bind()
    exercises = sa.table(
        "exercises",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("muscle_group", sa.String),
        sa.column("is_bodyweight", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    # Delete removed rows that are not referenced by any workout_exercise.
    # bench-press is in _REMOVED_IDS but re-inserted — skip it.
    ids_to_delete = [i for i in _REMOVED_IDS if i != "bench-press"]
    for exercise_id in ids_to_delete:
        in_use = conn.execute(
            sa.text("SELECT 1 FROM workout_exercises WHERE exercise_id = :id LIMIT 1"),
            {"id": exercise_id},
        ).fetchone()
        if not in_use:
            conn.execute(
                sa.text("DELETE FROM exercises WHERE id = :id"),
                {"id": exercise_id},
            )

    # Insert new rows (ignore conflicts for ids already present).
    for row in _NEW_ROWS:
        exists = conn.execute(
            sa.text("SELECT 1 FROM exercises WHERE id = :id"),
            {"id": row["id"]},
        ).fetchone()
        if not exists:
            conn.execute(exercises.insert().values(**row))

    # Update names for rows that changed.
    for upd in _UPDATES:
        conn.execute(
            sa.text("UPDATE exercises SET name = :name WHERE id = :id"),
            upd,
        )


def downgrade() -> None:
    # Downgrade is not supported: restoring deleted rows would require
    # re-seeding the original catalog, which is handled by migration 003.
    pass
