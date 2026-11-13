"""Personal records by estimated one-rep max: store reps, recompute records.

Revision ID: 025
Revises: 024
Create Date: 2026-11-13

A record is no longer the heaviest weight logged but the set with the best
estimated one-rep max (Epley: weight_kg × (1 + reps / 30)), so the record
keeps the reps of its set. Every existing record is recomputed from the
logged sets of completed sessions (the source of truth: logs can be edited
after completion without touching records): one row per (user, catalog
exercise done, swaps resolved) holding the best set; a tie goes to the
earliest session (completed_at, then started_at). `achieved_at` is that
session's completed_at and `session_id` that session.

The formula is re-implemented inline because migrations never import
application code — keep it in sync with
`backend.src.domain.estimated_one_rep_max.estimated_one_rep_max`.

Downgrade restores heaviest-weight records (tie → earliest session) and
drops `reps`.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Callable

import sqlalchemy as sa
from alembic import op

revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


# Estimates are compared after rounding to 0.1 kg, like the domain rule.
_COMPARISON_DECIMALS = 1

# Every weighted set of a completed session, keyed by the catalog exercise
# actually done (a session swap replaces the plan row's exercise). Logs
# without weight (NULL or 0) never make a record.
_LOGGED_SETS_SQL = sa.text(
    """
    SELECT s.user_id AS user_id,
           COALESCE(sw.exercise_id, we.exercise_id) AS exercise_id,
           l.weight_kg AS weight_kg,
           l.reps_completed AS reps,
           s.id AS session_id,
           s.completed_at AS completed_at,
           s.started_at AS started_at,
           l.set_number AS set_number
    FROM workout_logs l
    JOIN workout_exercises we ON we.id = l.workout_exercise_id
    LEFT OUTER JOIN session_exercise_swaps sw
        ON sw.session_id = l.session_id
       AND sw.workout_exercise_id = l.workout_exercise_id
    JOIN workout_sessions s ON s.id = l.session_id
    WHERE s.completed_at IS NOT NULL
      AND l.weight_kg > 0
    """
)


def _personal_records(*, with_reps: bool) -> sa.TableClause:
    columns = [
        sa.column("id", sa.String(36)),
        sa.column("user_id", sa.String(36)),
        sa.column("exercise_id", sa.String(255)),
        sa.column("weight_kg", sa.Float()),
        sa.column("achieved_at", sa.DateTime(timezone=True)),
        sa.column("session_id", sa.String(36)),
    ]
    if with_reps:
        columns.append(sa.column("reps", sa.Integer()))
    return sa.table("personal_records", *columns)


def _estimated_one_rep_max(weight_kg: float, reps: int) -> float:
    """Epley — mirrors backend.src.domain.estimated_one_rep_max."""
    return weight_kg * (1 + reps / 30)


def _rank_by_estimate(row: sa.Row) -> tuple[float, datetime, datetime, int]:
    # Highest estimate first; ties go to the earliest session, then set order.
    return (
        -round(_estimated_one_rep_max(row.weight_kg, row.reps), _COMPARISON_DECIMALS),
        row.completed_at,
        row.started_at,
        row.set_number,
    )


def _rank_by_weight(row: sa.Row) -> tuple[float, datetime, datetime, int]:
    # Heaviest first; ties go to the earliest session, then set order.
    return (-row.weight_kg, row.completed_at, row.started_at, row.set_number)


def _recompute_records(rank: Callable[[sa.Row], tuple], *, with_reps: bool) -> None:
    """Replace every personal record with the best logged set per
    (user, catalog exercise) under `rank` (lower sorts first)."""
    conn = op.get_bind()
    best: dict[tuple[str, str], sa.Row] = {}
    for row in conn.execute(_LOGGED_SETS_SQL):
        key = (row.user_id, row.exercise_id)
        current = best.get(key)
        if current is None or rank(row) < rank(current):
            best[key] = row

    table = _personal_records(with_reps=with_reps)
    conn.execute(sa.delete(table))
    records = []
    for (user_id, exercise_id), row in sorted(best.items()):
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "exercise_id": exercise_id,
            "weight_kg": row.weight_kg,
            "achieved_at": row.completed_at,
            "session_id": row.session_id,
        }
        if with_reps:
            record["reps"] = row.reps
        records.append(record)
    if records:
        conn.execute(sa.insert(table), records)


def upgrade() -> None:
    op.add_column("personal_records", sa.Column("reps", sa.Integer(), nullable=True))
    _recompute_records(_rank_by_estimate, with_reps=True)
    op.alter_column("personal_records", "reps", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    # Drop `reps` first: the recomputed heaviest-weight rows carry no reps.
    op.drop_column("personal_records", "reps")
    _recompute_records(_rank_by_weight, with_reps=False)
