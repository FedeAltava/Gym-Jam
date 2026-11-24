# Session: treadmill cardio

Objective: add treadmill cardio on the fly to a workout session and record it (minutes, distance, speed, incline, calories).
Branch: `feat/session-treadmill-cardio` · Delivery: work-unit commits, fast-forward merge to main, push and deploy (authorized by the user, repo practice; exception-ok) · Runners: `poetry run pytest backend/tests`, `cd frontend && npx vitest run`.

## Specs

- **S1 — Add treadmill cardio to a session.** "se añade sobre la marcha en la sesion y tiene que tener en cuenta minutos, distancia y pendiente y calorias quemadas, todo opcionales" + "y velocidad" + "el cardio sera siempre en cinta"
  - Agreed with the user ("si, implementalo"): no type field (always treadmill); fields `duration_minutes` (int), `distance_km`, `speed_kmh`, `incline_percent` (floats), `calories` (int), all optional but at least one filled; every value > 0 except incline 0–40 %; 422 otherwise; entries can be added and deleted also on a completed session.
  - Assumption: integer upper bounds to avoid DB overflow on typos: minutes ≤ 1440, calories ≤ 20000; non-finite numbers rejected.
  - Backend: `POST /sessions/{id}/cardio` (201, the entry) and `DELETE /sessions/{id}/cardio/{entry_id}` (204); 404 for a missing or malformed session id and for a missing, malformed or other-session entry id; 403 for another user's session (same as logs and swaps); 401 without auth. Session responses carry `cardio: [...]` ordered by creation.
- **S2 — Record and show it.** "como podemos hacer que el entrene tenga un aopcion de añadirle cardio, y registrarlo"
  - Session page: an "Añadir cardio" button opens a sheet with the five fields; saved entries are listed and can be deleted.
  - Session detail (history): the session's cardio entries are shown, with the same add/delete card (the session page leaves on completion, so this is where cardio is added to a completed session). History list and detail responses include `cardio`.
- **S3 — Deliver.** "tiene spermiso para pushear mergear y deplegar en produccion"
  - Merge to main, push, deploy to production with a DB backup first; check migration 027 at head and the route live.

## Tasks

| ID | Specs | Route | Status | Evidence |
|----|-------|-------|--------|----------|
| T1 | S1, S2 backend (migration 027 + domain + API + history read) | inline (no writer reason: frontend depends on this API) | done, verified, review approved | d55de01; RED import errors → GREEN 811 passed, ruff clean; migration on Postgres 16: 026→027, cascade, 027→026, re-upgrade, `alembic check` clean |
| T2 | S2 frontend (sheet + list in session page + detail page) | inline (no writer reason) | done | d073004 + 8092ee6 (sheet polish); RED 4 failing + 2 uncompilable files → GREEN 649 passed, tsc clean, eslint (1 pre-existing warning), build OK |
| T3 | S3 merge, push, deploy | inline | pending | |

Risk: T1 item 1 (schema migration, new table) → own commit, independent verifier. Forecast ~800 authored lines (backend ~450, frontend ~350).

## Log

- L1 (2026-11-24) "como podemos hacer que el entrene tenga un aopcion de añadirle cardio, y registrarlo"
- L2 (2026-11-24) "se añade sobre la marcha en la sesion y tiene que tener en cuenta minutos, distancia y pendiente y calorias quemadas, todo opcionales, te parece bien¿?"
- L3 (2026-11-24) "y velocidad"
- L4 (2026-11-24) "el cardio sera siempre en cinta"
- L5 (2026-11-24) "si, implementalo y tiene spermiso para pushear mergear y deplegar en produccion"
- L6 (2026-11-24) T1 d55de01: domain `CardioEntry` + `WorkoutSession.add_cardio/remove_cardio` (no completed guard), table `session_cardio_entries` (migration 027, cascade on session delete), POST/DELETE routes, `cardio` in session, day-sessions, history and detail responses (history: one more IN query, 6 SELECTs). Foreign session → 403, like logs/swaps (S1 text corrected from 404). RDD assess 62b738a..d55de01: high (executable_change + escalated item 1), review_due → independent verifier launched before native review. Untracked user files excluded from the candidate.
- L7 (2026-11-24) T2 d073004: shared `SessionCardioSection` (list, delete, "Añadir cardio" sheet with client validation and decimal comma) in WorkoutSessionPage and SessionDetailPage; hooks `useAddCardio`/`useDeleteCardio` invalidate `['sessions']`. Gotcha: `beforeEach(() => mock.mockReset())` returns the mock, which Vitest runs as teardown — use a block body. RDD assess d55de01..d073004: medium, review_due false (under_budget, 679 lines).
- L8 (2026-11-24) Independent verifier on d55de01 (baseline 62b738a): S1 PASS, S2 backend PASS, no blockers; 811 passed, ruff clean; 123 probes OK on SQLite and Postgres 16; DB hash unchanged after 37 rejected commands; 31-step base-vs-candidate diff of shared endpoints identical except the added `cardio` key; migration 027 up/down/up + `alembic check` clean. Advisories: pydantic lax coercion (`"250"`, `true`, extra keys ignored) like every other schema; no upper bound on distance/speed; order by created_at without tiebreaker. Probes committed as regression tests in cce7ae1 (35 cardio tests). Local UI check at 390px (scratch SQLite, servers stopped, scratch removed): card and sheet render, adding "15 / 5,5 / 12" lists "15 min · 5,5 km/h · pendiente 12 %", detail page of a completed session shows the card; polish 8092ee6 removed example placeholders that looked like filled values and added safe-area bottom padding. Native review of T1 alone (detached worktree at d55de01, lineage review-53aee1314afddce9, lenses risk+reliability): consent envelope relayed to the user.
- L9 (2026-11-24) User granted the review ("Revisar este cambio"). Native review review-53aee1314afddce9 (62b738a..d55de01, risk+reliability): approved and acknowledged (authority burned); reviewed boundary → d55de01. Non-blocking suggestions (later work, not reopening review): order cardio by created_at has no tiebreaker; an entry with only incline 0 passes "at least one value" (spec-compliant: a filled field). Slice d55de01..8092ee6 (T2 + probes + sheet polish): medium, review_due false (under_budget, 767 lines). Full frontend suite 649 passed, build OK. Next: T3 merge, push, deploy.
