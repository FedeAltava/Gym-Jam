"""Add exercises catalog table and seed the standard catalog.

Revision ID: 003
Revises: 002
Create Date: 2026-07-02

"""
from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Seed rows are inlined as literals on purpose: migrations must be frozen in
# time and never depend on mutable application modules. This is a snapshot of
# backend/src/infrastructure/persistence/exercise_seed.py at migration time.
_SEED_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

_EXERCISE_SEED: list[dict[str, object]] = [
    # Pecho
    {"id": "bench-press", "name": "Press de banca", "muscle_group": "Pecho", "created_at": _SEED_CREATED_AT},
    {"id": "incline-bench-press", "name": "Press inclinado", "muscle_group": "Pecho", "created_at": _SEED_CREATED_AT},
    {"id": "push-up", "name": "Flexiones", "muscle_group": "Pecho", "created_at": _SEED_CREATED_AT},
    # Espalda
    {"id": "pull-up", "name": "Dominadas", "muscle_group": "Espalda", "created_at": _SEED_CREATED_AT},
    {"id": "lat-pulldown", "name": "Jalón al pecho", "muscle_group": "Espalda", "created_at": _SEED_CREATED_AT},
    {"id": "barbell-row", "name": "Remo con barra", "muscle_group": "Espalda", "created_at": _SEED_CREATED_AT},
    {"id": "deadlift", "name": "Peso muerto", "muscle_group": "Espalda", "created_at": _SEED_CREATED_AT},
    # Piernas
    {"id": "squat", "name": "Sentadilla", "muscle_group": "Piernas", "created_at": _SEED_CREATED_AT},
    {"id": "front-squat", "name": "Sentadilla frontal", "muscle_group": "Piernas", "created_at": _SEED_CREATED_AT},
    {"id": "leg-press", "name": "Prensa de piernas", "muscle_group": "Piernas", "created_at": _SEED_CREATED_AT},
    {"id": "lunge", "name": "Zancadas", "muscle_group": "Piernas", "created_at": _SEED_CREATED_AT},
    {"id": "leg-curl", "name": "Curl femoral", "muscle_group": "Piernas", "created_at": _SEED_CREATED_AT},
    {"id": "calf-raise", "name": "Elevación de gemelos", "muscle_group": "Piernas", "created_at": _SEED_CREATED_AT},
    # Hombros
    {"id": "overhead-press", "name": "Press militar", "muscle_group": "Hombros", "created_at": _SEED_CREATED_AT},
    {"id": "lateral-raise", "name": "Elevaciones laterales", "muscle_group": "Hombros", "created_at": _SEED_CREATED_AT},
    # Brazos
    {"id": "biceps-curl", "name": "Curl de bíceps", "muscle_group": "Brazos", "created_at": _SEED_CREATED_AT},
    {"id": "hammer-curl", "name": "Curl martillo", "muscle_group": "Brazos", "created_at": _SEED_CREATED_AT},
    {"id": "triceps-pushdown", "name": "Extensión de tríceps en polea", "muscle_group": "Brazos", "created_at": _SEED_CREATED_AT},
    # Core
    {"id": "plank", "name": "Plancha", "muscle_group": "Core", "created_at": _SEED_CREATED_AT},
    {"id": "crunch", "name": "Abdominales", "muscle_group": "Core", "created_at": _SEED_CREATED_AT},
]


def upgrade() -> None:
    exercises = op.create_table(
        "exercises",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("muscle_group", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.bulk_insert(exercises, _EXERCISE_SEED)


def downgrade() -> None:
    op.drop_table("exercises")
