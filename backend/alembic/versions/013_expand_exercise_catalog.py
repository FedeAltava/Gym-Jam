"""Expand exercise catalog to 15 exercises per muscle group.

Revision ID: 013
Revises: 012
Create Date: 2026-07-29

Adds 58 new exercises across all muscle groups. Existing rows are untouched.
"""
from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEED_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

_NEW_ROWS = [
    # Pecho
    {"id": "incline-bench-press", "name": "Press inclinado con barra", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "dumbbell-bench-press", "name": "Press con mancuernas", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "incline-dumbbell-press", "name": "Press inclinado con mancuernas", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "decline-bench-press", "name": "Press declinado", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "dumbbell-fly", "name": "Aperturas con mancuernas", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "push-up", "name": "Flexiones", "muscle_group": "Pecho", "is_bodyweight": True},
    {"id": "cable-fly-high", "name": "Cruce de poleas alto", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "cable-fly-low", "name": "Cruce de poleas bajo", "muscle_group": "Pecho", "is_bodyweight": False},
    {"id": "chest-dip", "name": "Fondos en paralelas", "muscle_group": "Pecho", "is_bodyweight": True},
    {"id": "pec-deck", "name": "Pec deck", "muscle_group": "Pecho", "is_bodyweight": False},
    # Espalda
    {"id": "pull-up", "name": "Dominadas", "muscle_group": "Espalda", "is_bodyweight": True},
    {"id": "barbell-row", "name": "Remo con barra", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "dumbbell-row", "name": "Remo con mancuerna", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "cable-row", "name": "Remo en polea baja", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "t-bar-row", "name": "Remo en T", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "chest-supported-row", "name": "Remo en banco inclinado", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "straight-arm-pulldown", "name": "Jalón a polea brazos rectos", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "rack-pull", "name": "Rack pull", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "good-morning", "name": "Good morning", "muscle_group": "Espalda", "is_bodyweight": False},
    {"id": "hyperextension", "name": "Hiperextensión lumbar", "muscle_group": "Espalda", "is_bodyweight": True},
    # Piernas
    {"id": "squat", "name": "Sentadilla", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "romanian-deadlift", "name": "Peso muerto rumano", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "hip-thrust", "name": "Hip thrust", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "bulgarian-split-squat", "name": "Sentadilla búlgara", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "lunge", "name": "Zancadas", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "calf-raise", "name": "Elevación de gemelos", "muscle_group": "Piernas", "is_bodyweight": False},
    {"id": "step-up", "name": "Step up", "muscle_group": "Piernas", "is_bodyweight": False},
    # Hombros
    {"id": "dumbbell-shoulder-press", "name": "Press de hombros con mancuernas", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "arnold-press", "name": "Press Arnold", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "cable-lateral-raise", "name": "Elevación lateral en polea", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "upright-row", "name": "Remo al cuello", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "cable-front-raise", "name": "Elevación frontal en polea", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "shrug", "name": "Encogimientos de hombros", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "landmine-press", "name": "Press landmine", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "push-press", "name": "Push press", "muscle_group": "Hombros", "is_bodyweight": False},
    {"id": "rear-delt-fly", "name": "Aperturas posteriores", "muscle_group": "Hombros", "is_bodyweight": False},
    # Brazos
    {"id": "preacher-curl", "name": "Curl en banco Scott", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "concentration-curl", "name": "Curl de concentración", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "incline-dumbbell-curl", "name": "Curl inclinado con mancuernas", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "reverse-curl", "name": "Curl inverso", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "skull-crusher", "name": "Rompecráneos", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "triceps-dip", "name": "Fondos para tríceps", "muscle_group": "Brazos", "is_bodyweight": True},
    {"id": "diamond-push-up", "name": "Flexiones en diamante", "muscle_group": "Brazos", "is_bodyweight": True},
    {"id": "close-grip-bench-press", "name": "Press agarre cerrado", "muscle_group": "Brazos", "is_bodyweight": False},
    {"id": "cable-overhead-triceps", "name": "Extensión de tríceps en polea alta", "muscle_group": "Brazos", "is_bodyweight": False},
    # Core
    {"id": "plank", "name": "Plancha", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "leg-raise", "name": "Elevación de piernas", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "russian-twist", "name": "Giro ruso", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "bicycle-crunch", "name": "Abdominales bicicleta", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "hanging-leg-raise", "name": "Elevación de piernas en barra", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "cable-crunch", "name": "Crunch en polea", "muscle_group": "Core", "is_bodyweight": False},
    {"id": "ab-wheel", "name": "Rueda abdominal", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "side-plank", "name": "Plancha lateral", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "mountain-climber", "name": "Escaladores", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "dead-bug", "name": "Dead bug", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "pallof-press", "name": "Press Pallof", "muscle_group": "Core", "is_bodyweight": False},
    {"id": "toe-to-bar", "name": "Toes to bar", "muscle_group": "Core", "is_bodyweight": True},
    {"id": "dragon-flag", "name": "Dragon flag", "muscle_group": "Core", "is_bodyweight": True},
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
    ids = [row["id"] for row in _NEW_ROWS]
    for exercise_id in ids:
        in_use = conn.execute(
            sa.text("SELECT 1 FROM workout_exercises WHERE exercise_id = :id LIMIT 1"),
            {"id": exercise_id},
        ).fetchone()
        if not in_use:
            conn.execute(
                sa.text("DELETE FROM exercises WHERE id = :id"),
                {"id": exercise_id},
            )
