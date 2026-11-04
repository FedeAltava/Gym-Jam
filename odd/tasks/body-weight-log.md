# Profile: body weight log with history

Objective: record body weight from the profile view and see its history.
Branch: `feat/body-weight-log` · Delivery: work-unit commits, merge/push/deploy on user approval (same as previous features); forecast ~1000 authored lines · Runners: `poetry run pytest backend/tests`, `cd frontend && npx vitest run`.

## Specs

- **S1 — Add my weight from the profile.** "quiero que en la vista de perfil poder añadir mi peso y tener un historico tambien"
  - Weight in kg (the app shows kg everywhere; the `units` preference is not applied anywhere in the UI).
  - Assumption: one entry per day; recording a weight for a day that already has one replaces it.
  - Assumption: the date defaults to today and can be changed to fill in past weigh-ins; future dates are rejected.
  - Assumption: valid weights are greater than 0 and at most 400 kg.
- **S2 — History.** Same quote as S1 ("tener un historico tambien").
  - The profile lists the entries newest first with date, weight and change against the previous entry.
  - Assumption: an entry can be deleted (to fix mistakes).
  - Out of scope (not requested): a chart.

## Tasks

| ID | Specs | Route | Status | Evidence |
|----|-------|-------|--------|----------|
| T1 | S1, S2 backend: `body_weight_entries` table (migration 022), record/list/delete use cases and endpoints | inline (no writer reason: frontend depends on the API) | done | 9361f98 + 5b5af12 (409 guard covers the flush, verifier probes as tests) + f2d5bcd (midnight-safe test); RED (missing module, 10 HTTP failing) → GREEN 692 passed; ruff clean; mypy +2 (`rowcount`, same pattern as diet plan repo); migration 021→022→021→022 + `alembic check` on Postgres 16, users hash identical, user delete cascades |
| T2 | S1, S2 frontend: weight card in the profile with form and history | inline | done | 43f5c83; RED (missing module + profile heading) → GREEN 278 passed; tsc clean; eslint 0 errors; checked in the real app at 390×844 (save with comma, replace hint, delete) |

Risk: T1 item 1 (schema migration, new table) → own commit. T2: none (new card; the profile's existing tests pass unchanged).

## Log

- L1 (2026-11-04) "quiero que en la vista de perfil poder añadir mi peso y tener un historico tambien"
- L2 (2026-11-04) Map: no body weight tracking exists. Profile (`frontend/src/pages/ProfilePage.tsx`) = header, stats tiles, settings list. No chart library (dashboard chart is hand-made). Backend user-scoped vertical to mirror: diet plans (id VO with `from_string`, port with `*_for_user` methods, 404 for foreign rows). API design: `GET /users/me/body-weight`, `POST /users/me/body-weight {weight_kg, measured_on?}` (upsert per day), `DELETE /users/me/body-weight/{entry_id}`.
- L3 (2026-11-04) API simplified to the natural key: `GET /users/me/body-weight`, `PUT|DELETE /users/me/body-weight/{YYYY-MM-DD}` (table PK `(user_id, measured_on)`, no ids). Server accepts up to UTC today + 1 day because the client sends its local date. RDD assess on 9361f98: high (escalated item 1) → independent verifier launched; T2 held uncommitted so the review candidate stays T1.
- L4 (2026-11-04) T2 UI: "Peso corporal" card under the stats tiles: latest weight, form (date defaults to today, weight accepts "84,5"), replace hint when the day already has a weight, history newest first (7 shown, "Ver todo"), neutral-coloured change vs previous entry, delete per row. UI check widened the date field (it was truncated at 390 px).
- L5 (2026-11-04) User: "perfecto si funciona comitea mergea y deplega en el servidor". Independent verifier on 9361f98: PASS, no blockers (692 passed; migration 021→022→021→022 + `alembic check` on Postgres 16, pre-existing rows hash-identical, user delete cascades; probes 8 passed; baseline differential on stats/preferences/auth/nutrition/sessions identical). Advisories: L2 API shape outdated (L3 records the final one); the 409 IntegrityError guard only wrapped commit() while the upsert flushes inside execute() → fixed in 5b5af12; pydantic lax inputs (`"81.5"`, `2024-01-01T00:00:00`) accepted like the rest of the API. Probes committed as `backend/tests/http/test_body_weight_edge_cases.py` (700 passed).
- L6 (2026-11-04) Native review START on 646a0c2..5b5af12 (lineage review-df725b5d04421d28, lenses risk+reliability): consent relayed, user chose "Revisar este cambio".
- L7 (2026-11-04) Native review review-df725b5d04421d28 approved and acknowledged; boundary → 5b5af12. Advisory: R3-midnight-flake (HTTP future-date check could flip at UTC midnight) → fixed in f2d5bcd (+3 days; boundary pinned by the fixed-clock unit test); R3-409-untested (no test forces the IntegrityError path) → follow-up. T2 committed (43f5c83); assess 5b5af12..HEAD: medium, review not due (under_budget). Final: backend 700 passed, ruff clean; frontend 278 passed, tsc clean, eslint 0 errors.
