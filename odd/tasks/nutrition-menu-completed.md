# Nutrition: mark a menu as completed

Objective: each menu card in Nutrición gets a checkbox to record whether the menu was completed, stored in the backend.
Branch: `feat/nutrition-menu-completed` · Delivery: work-unit commits, push/deploy on user approval · Runners: `poetry run pytest backend/tests`, `cd frontend && npx vitest run`.

## Specs

- **S1 — Completed checkbox per menu.** "en el apartado de nutricion estaria bien que cada menu tuviese un check box para saber si lo hemos completado o no"
  - Assumption: "menú" is a card of the list (one weekly menu); for a grouped menu (Fede/Belén variants) the check belongs to the whole menu, like delete.
  - Backend: diet plans get `completed` (bool, default false; existing menus start unchecked), returned by list and detail. `PATCH /nutrition/menus/{id}` with `{"completed": true|false}` sets it on the plan and, when grouped, on every variant; 404 for a missing, foreign or malformed id; 401 without auth.
  - Frontend: every menu card shows a checkbox reflecting the state; toggling it persists the change and does not open the menu.

## Tasks

| ID | Specs | Route | Status | Evidence |
|----|-------|-------|--------|----------|
| T1 | S1 backend (column + migration 026 + PATCH) | inline (no writer reason) | done | 29fe0b2; RED 8 failing → GREEN 763 passed, ruff clean; migration 025→026→025→026 on Postgres 16 with a pre-existing row (→ false), `alembic check` clean |
| T2 | S1 frontend (checkbox on the card) | inline (no writer reason) | done | 98cc9e3; RED 5 failing → GREEN 622 passed, tsc + eslint clean |

Risk: T1 item 1 (schema migration, additive column with default) → own commit. Forecast ~250 authored lines (< 400).

## Log

- L1 (2026-11-16) "hola en el apartado de nutricion estaria bien que cada menu tuviese un check box para saber si lo hemos completado o no"
- L2 (2026-11-16) T1 RDD assess on 318aa8e..29fe0b2: high (executable_change + escalated item 1) → independent verifier launched before native review. Untracked user files (screenshots, node_modules, backend/scripts) excluded from the candidate.
- L3 (2026-11-16) T2: checkbox "Completado" on every list card (MenuCompletedCheckbox), optimistic update of the list cache for the whole group with rollback + "No se pudo guardar. Inténtalo de nuevo." on failure; click does not open the menu.
- L4 (2026-11-16) T2 RDD assess on 29fe0b2..98cc9e3: medium, review_due false (under_budget, 187 lines) → no review, stays in the slice. T1 native review pending the verifier; T1 will be reviewed alone (range 318aa8e..29fe0b2).
- L5 (2026-11-16) Independent verifier on 29fe0b2: PASS, no blockers (763 passed; probes: rejected PATCH 404/422/401 leaves the table hash unchanged; ungrouped PATCH touches one row; grouped PATCH scoped to the user even with a shared group_id; baseline vs candidate output diff = only added `"completed": false`; migration 026 round-trip on SQLite + `alembic check` clean). Advisories: repo methods' rowcount unused by the use case; four FakeRepos repeat no-op stubs. Native review of T1 alone in a detached worktree at 29fe0b2 (lineage review-49dfef954e25bb41, lenses risk+reliability): user granted consent; reviewer captures running.
- L6 (2026-11-16) Native review review-49dfef954e25bb41 (318aa8e..29fe0b2, risk+reliability): approved and acknowledged; reviewed boundary → 29fe0b2. Non-blocking advisories (later work, not reopening review): use case ignores the repo rowcount (existence checked first); no unit test for the use case (covered by HTTP tests); model `server_default="false"` vs migration `sa.false()` (same idiom as `is_bodyweight`, `alembic check` clean). T2 slice (29fe0b2..98cc9e3) medium/under_budget → no review due. Feature implemented; push/deploy pending the user's decision.
