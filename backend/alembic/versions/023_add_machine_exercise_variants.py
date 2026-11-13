"""Add machine exercises in plate-loaded and selectorized variants.

Revision ID: 023
Revises: 022
Create Date: 2026-11-13

The same machine exercise comes in two kinds: plate-loaded machines, where
plates are loaded onto the machine (guided free weight), and selectorized
machines, where the load is picked with the pin in the weight stack. Adds
both variants, named "(discos)" and "(placas)", for 16 machine exercises.
Existing rows are untouched. Kept in sync with exercise_seed.py.
"""
from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEED_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

_NEW_ROWS = [
    {"id": "chest-press-plate-loaded", "name": "Press pecho en máquina (discos)", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "chest-press-selectorized", "name": "Press pecho en máquina (placas)", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "incline-press-plate-loaded", "name": "Press inclinado en máquina (discos)", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "incline-press-selectorized", "name": "Press inclinado en máquina (placas)", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "decline-press-plate-loaded", "name": "Press declinado en máquina (discos)", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "decline-press-selectorized", "name": "Press declinado en máquina (placas)", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "lat-pulldown-plate-loaded", "name": "Jalón al pecho en máquina (discos)", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "lat-pulldown-selectorized", "name": "Jalón al pecho en máquina (placas)", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "seated-row-plate-loaded", "name": "Remo sentado en máquina (discos)", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "seated-row-selectorized", "name": "Remo sentado en máquina (placas)", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "high-row-plate-loaded", "name": "Remo alto en máquina (discos)", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "high-row-selectorized", "name": "Remo alto en máquina (placas)", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "shoulder-press-plate-loaded", "name": "Press hombros en máquina (discos)", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "shoulder-press-selectorized", "name": "Press hombros en máquina (placas)", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "lateral-raise-machine-plate-loaded", "name": "Elevación lateral en máquina (discos)", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "lateral-raise-machine-selectorized", "name": "Elevación lateral en máquina (placas)", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "leg-press-plate-loaded", "name": "Prensa de piernas (discos)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "leg-press-selectorized", "name": "Prensa de piernas (placas)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "leg-extension-plate-loaded", "name": "Extensión de cuádriceps (discos)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "leg-extension-selectorized", "name": "Extensión de cuádriceps (placas)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "leg-curl-plate-loaded", "name": "Curl femoral (discos)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "leg-curl-selectorized", "name": "Curl femoral (placas)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "hip-thrust-machine-plate-loaded", "name": "Hip thrust en máquina (discos)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "hip-thrust-machine-selectorized", "name": "Hip thrust en máquina (placas)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "glute-kickback-machine-plate-loaded", "name": "Patada de glúteo en máquina (discos)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "glute-kickback-machine-selectorized", "name": "Patada de glúteo en máquina (placas)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "calf-raise-machine-plate-loaded", "name": "Elevación de gemelos en máquina (discos)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "calf-raise-machine-selectorized", "name": "Elevación de gemelos en máquina (placas)", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "biceps-curl-machine-plate-loaded", "name": "Curl de bíceps en máquina (discos)", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "biceps-curl-machine-selectorized", "name": "Curl de bíceps en máquina (placas)", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "triceps-machine-plate-loaded", "name": "Extensión de tríceps en máquina (discos)", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "triceps-machine-selectorized", "name": "Extensión de tríceps en máquina (placas)", "muscle_group": "Brazos", "is_bodyweight": False},
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

    for row in _NEW_ROWS:
        exists = conn.execute(
            sa.text("SELECT 1 FROM exercises WHERE id = :id"),
            {"id": row["id"]},
        ).fetchone()
        if not exists:
            conn.execute(exercises.insert().values(**row, created_at=_SEED_CREATED_AT))


def downgrade() -> None:
    conn = op.get_bind()
    for row in _NEW_ROWS:
        # Keep a variant that a routine plans or a session swapped in: swaps
        # reference catalog ids without a foreign key, and their logged sets
        # count for the swapped-in exercise.
        in_use = conn.execute(
            sa.text(
                "SELECT 1 FROM workout_exercises WHERE exercise_id = :id "
                "UNION ALL SELECT 1 FROM session_exercise_swaps WHERE exercise_id = :id LIMIT 1"
            ),
            {"id": row["id"]},
        ).fetchone()
        if not in_use:
            conn.execute(sa.text("DELETE FROM exercises WHERE id = :id"), {"id": row["id"]})
