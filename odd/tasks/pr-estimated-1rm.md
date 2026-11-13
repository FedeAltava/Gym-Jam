# Personal records by estimated 1RM

Objective: a personal record takes the reps into account (best estimated one-rep max), stores the record set, recomputes existing records from logged sets, and the app shows the exact record set.
Branch: `feat/pr-estimated-1rm` · Delivery: work-unit commits, merge/push/deploy on user approval (deploy with a database backup first); forecast ~700 authored lines · Runners: `poetry run pytest backend/tests` (repo root), `cd frontend && npx vitest run`; migrations on a throwaway `postgres:16-alpine` (alembic does not run on SQLite).

## Specs

- **S1 — A record takes the reps into account.** "para calcular el pr creo que deberia tener en cuenta las repeticiones con las que se ha hecho no?" Proposal accepted ("si hazlo"):
  - A set's estimated 1RM is Epley: `weight_kg × (1 + reps / 30)`.
  - When a session is completed, for each catalog exercise actually done (a swap counts for the swapped-in exercise), the session's best set by estimated 1RM is a new record when it is strictly higher than the best estimated 1RM of the user's previous completed sessions for that exercise. Comparison rounded to 0.1 kg; a tie is not a record.
  - Sets without weight (null or 0) never make a record. Only completed sessions count; detection stays non-fatal and runs once per session (existing rules).
  - Examples from the proposal: 80 kg × 10 → ≈ 107 kg; 82,5 kg × 3 → ≈ 91 kg (not a record after 80 × 10); 80 kg × 12 → ≈ 112 kg (record after 80 × 8 ≈ 101 kg).
- **S2 — The record keeps its set, and existing records are recomputed.** "Una migración para guardar las repeticiones en los récords" · "Recalcular vuestros récords actuales a partir de las series que ya tenéis registradas. No se pierde nada, porque todo sale de vuestro historial, y haría una copia de seguridad antes."
  - `personal_records` stores the record set's `reps` next to `weight_kg`.
  - The migration recomputes every user's records from logged sets of completed sessions: one row per (user, exercise) with the best estimated 1RM; tie → the earliest session; `achieved_at` = that session's `completed_at`; `session_id` = that session. Downgrade restores heaviest-weight records.
- **S3 — The app shows the record with its real set.** "En la app el récord se mostraría con la serie real, por ejemplo "80 kg × 12 (≈ 112 kg)"."
  - The session API returns the records a session holds (exercise, weight, reps) and each log's catalog exercise; session detail marks exactly those sets (not the heaviest-set guess) and shows the estimate, e.g. "≈ 112 kg".

## Tasks

| ID | Specs | Route | Status | Evidence |
|----|-------|-------|--------|----------|
| T1 | S1, S2 backend: estimated-1RM detection, repository, migration 025 (reps + recompute), tests | delegated writer (context backstop: long parent session) | done | RED per rule (missing module, port mismatch, HTTP `assert 0 == 1`, `assert 1 == 0`) → GREEN; Postgres 16 up/down/up + `alembic check` clean (heavier-fewer-reps, swap, in-progress, bodyweight, tie, two users); parent fixed 2 stats-test fixtures (`reps=`); backend 744 passed, ruff clean, mypy baseline 36 |
| T2 | S3 backend session records in history/detail API + frontend session detail | delegated writer (context backstop; depends on T1's `reps` column) | done | RED `KeyError: 'records'`/`'exercise_id'`, query count `assert 4 == 5`, `ImportError SessionRecordSnapshot`, 4 frontend failures (badge on heaviest set, missing "≈ 101 kg", cross-exercise badge) → GREEN; parent added `records: []` to useSessionHistory.test.ts fixture (tsc); backend 746, frontend 306, tsc/eslint/ruff clean, mypy baseline 36 |
| T3 | Independent verification (Risk item 1: migration recomputes stored records), review, deploy | verifier + parent | pending | |

Risk: T1 item 1 (migration rewrites stored personal records) → own commit.

## Log

- L1 (2026-11-13) "para calcular el pr creo que deberia tener en cuenta las repeticiones con las que se ha hecho no?" → proposal (estimated 1RM, Epley, store reps, recompute) → "si hazlo".
- L2 (2026-11-13) Map: `personal_records` one row per (user_id, exercise_id), `weight_kg` only (migration 011); detection in `CompleteWorkoutSessionUseCase._detect_personal_records` (max weight, strict `>`), previous best from completed log history (`get_previous_max_weights`, swaps via COALESCE); `upsert_if_higher` re-points the row to the newer session. Readers: history/detail `pr_count` (count only), stats `total_prs`/`weekly_prs` (row counts), frontend HistoryPage badge, SessionDetailPage badge = heaviest set of the whole session (a guess), ProfilePage total. Logs can be edited/deleted after completion without updating records, so recomputing from logs is the source of truth.
- L3 (2026-11-13) T1 writer: domain `estimated_one_rep_max` + `beats_record` (round 0.1, strict); port `get_previous_best_estimates`, `upsert_if_higher(..., reps, ...)`; migration 025 recomputes in Python via `op.get_bind()` (rank: -round(estimate,1), completed_at, started_at, set_number); downgrade drops `reps` first, then recomputes by weight. Parent spot check: full backend suite 744 passed.
- L4 (2026-11-13) T2 writer: history logs carry `exercise_id` (existing COALESCE join); items carry `records` from one IN query on personal_records; `pr_count = len(records)` (old pr_counts subquery removed); DTO adds `estimated_one_rep_max_kg` (domain function, 0.1 kg); SessionDetailPage `findRecordSets` marks the first set matching exercise/weight/reps and shows "≈ N kg" (Math.round). Parent spot check: tsc 0, vitest 306, backend 746.
