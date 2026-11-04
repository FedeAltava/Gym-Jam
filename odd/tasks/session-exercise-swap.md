# Workout session: swap an exercise for that session only

Objective: during a workout session, replace a planned exercise with another catalog exercise for that session only; the routine stays unchanged.
Branch: `feat/session-exercise-swap` · Delivery: work-unit commits, merge/push/deploy on user approval (same as previous features); forecast ~1100 authored lines · Runners: `poetry run pytest backend/tests`, `cd frontend && npx vitest run`.

## Specs

- **S1 — Swap during the session.** "hay que hacer que cuando estas haciendo una rutina, poder cambiar de un ejercicio a otro, es decir si hay press banca entre otros ese dia de la rutina pero yo justo ese dia no voy a hacer press banca y quiero hacer aperturas poder cambiarlo duarante la sesion de entrenamiento"
  - The swap applies to that session only; the routine plan is not modified (from "justo ese dia").
  - Assumption: the substitute is any catalog exercise and keeps the planned slot's sets and reps.
  - Assumption: a swap is allowed only while the session is in progress and before any set of that slot is logged (logged sets would otherwise change exercise silently).
  - Assumption: the swap can be undone (back to the planned exercise) under the same conditions.
  - The swap persists (page reload keeps it).
- **S2 — The substitute is what was trained.** Derived from S1: the session's history/detail shows the substitute's name and muscle group, and personal records are computed for the substitute exercise, not the planned one.

## Tasks

| ID | Specs | Route | Status | Evidence |
|----|-------|-------|--------|----------|
| T1 | S1 backend: swap persistence (migration 021), domain, swap/undo endpoints | inline (no writer reason: units depend on each other) | done | b95a27b + e9f5232 (verifier probes as tests, README) + 94af701 (lint); RED (import errors, 10 HTTP failing) → GREEN 658 passed; ruff clean, no new mypy errors; migration 020→021→020→021 + `alembic check` on Postgres 16 |
| T2 | S2 backend: history and PR detection honor swaps | inline | done | bc58e51; RED 2 failing ('Press Arnold' ≠ 'Cruce de poleas'; pr_count 0 ≠ 1) → GREEN 660 passed |
| T3 | S1, S2 frontend: swap picker in the session, substitute shown | inline | done | 13c146f; RED 3 failing (no swap button) → GREEN 270 passed; tsc clean; eslint 0 errors; checked in the real app at 390×844 (swap, undo, reload persistence, button hidden after a logged set) |

Risk: T1 item 1 (schema migration, new table) → own commit. T2, T3: none (non-swapped history/PR output unchanged, pinned by existing tests).

## Log

- L1 (2026-11-04) "hola, hay que hacer que cuando estas haciendo una rutina, poder cambiar de un ejercicio a otro, es decir si hay press banca entre otros ese dia de la rutina pero yo justo ese dia no voy a hacer press banca y quiero hacer aperturas poder cambiarlo duarante la sesion de entrenamiento"
- L2 (2026-11-04) Map: `workout_logs.workout_exercise_id` is a NOT NULL FK to the plan row, unique with `(session_id, set_number)`; `LogExerciseSetUseCase` only accepts plan rows of the session's day; history names come from `logs → workout_exercises → exercises`; PR detection maps plan row → catalog id (`personal_record_repository.py`). Design: new table `session_exercise_swaps(session_id, workout_exercise_id → exercise_id)` owned by the `WorkoutSession` aggregate; logs keep pointing at the plan slot; exercise identity resolves as `COALESCE(swap.exercise_id, plan.exercise_id)`.
- L3 (2026-11-04) T1 API: `PUT /sessions/{id}/exercises/{workout_exercise_id}/swap {exercise_id}` and `DELETE` same path (undo); both return the session with `swaps: [{workout_exercise_id, exercise_id}]`. Errors: 404 unknown session/slot/catalog exercise, 403 other user, 409 completed session or slot with logged sets. `Workout.find_exercise_in_day` extracted and reused by `LogExerciseSetUseCase` (pinned by a new cross-day test). RDD assess on b95a27b: high (executable_change + escalated item 1) → independent verifier launched; T2/T3 held uncommitted so the review candidate stays T1 alone.
- L4 (2026-11-04) T3 UI: "Cambiar" button per exercise (in-progress session, no logged sets in that slot), bottom sheet filtered by the current exercise's muscle group ("Todos" chip), "En lugar de <planned>" subtitle and "Deshacer". A swapped slot does not prefill the plan's weight, and last-session values are only used when that session did the same exercise. Swaps/logged slots are read from the refetched sessions query because the page's local session snapshot is not refreshed after mutations.
- L5 (2026-11-04) Independent verifier on b95a27b: PASS, no blockers (658 passed; migration 020→021→020→021 + `alembic check` on Postgres 16 with pre-existing rows hash-identical; 35-step baseline/candidate differential: only new `swaps: []` key; probes 8 passed SQLite, 52 on Postgres). Advisories: README endpoint table missing the swap endpoints (fixed in e9f5232); wrong-slot 404 says "Workout ... not found" (pre-existing LogExerciseSet wording, kept). Probes committed as `backend/tests/http/test_session_exercise_swaps.py` (e9f5232, 666 passed without T2).
- L6 (2026-11-04) UI check in the real app found the swap sheet's chip row shrinking (clipped chips) and the preselected muscle group off-screen; fixed (shrink-0, scroll chip into view). Undo moved to an inline "Deshacer" link next to "En lugar de …" so the title is not squeezed on phones.
- L7 (2026-11-04) Native review START for range b2c6473..e9f5232 (lineage review-9cb0b15ca5d3aedb, lenses risk+reliability, untracked excluded) returned consent_required (medium); relayed to the user.
- L8 (2026-11-04) User chose "Revisar este cambio". Native review lineage review-9cb0b15ca5d3aedb (risk + reliability) on b2c6473..e9f5232: approved and acknowledged; boundary → e9f5232. Advisory, non-blocking: R3-swap-pr-attribution (PRs/history credited to the planned exercise) — solved by T2 (bc58e51); R3-swap-log-race (a concurrent log POST and swap PUT on the same slot can both commit) — follow-up; R3-integrity-path-untested (router 409 on IntegrityError has no test) — follow-up.
- L9 (2026-11-04) T2+T3 committed (bc58e51, 13c146f); assess on e9f5232..HEAD: medium, review not due (under_budget). Final: backend 668 passed, ruff clean (94af701 fixed E741 in the probe file); frontend 270 passed, tsc clean, eslint 0 errors. Feature closed on branch `feat/session-exercise-swap`; merge/push/deploy (runs migration 021) are the user's decision.
