"""Estimated one-rep max — the domain rule behind personal records.

A set's estimated one-rep max follows the Epley formula; a personal record
is the set with the highest estimate, so more reps at the same weight can
beat a heavier set done for far fewer reps. Migration 025 re-implements the
formula inline (migrations never import application code); keep both in sync.
"""
from __future__ import annotations

# Estimates are compared after rounding to this many decimals (0.1 kg).
COMPARISON_DECIMALS = 1


def estimated_one_rep_max(weight_kg: float, reps: int) -> float:
    """Epley estimate: `weight_kg × (1 + reps / 30)`."""
    return weight_kg * (1 + reps / 30)


def beats_record(estimate_kg: float, previous_estimate_kg: float | None) -> bool:
    """True when `estimate_kg` is strictly higher than the previous best after
    rounding both to 0.1 kg. A tie is not a record; no previous best is."""
    if previous_estimate_kg is None:
        return True
    return round(estimate_kg, COMPARISON_DECIMALS) > round(previous_estimate_kg, COMPARISON_DECIMALS)
