# Nutrition: resilient PDF upload + delete menu

## Objective
Make PDF menu upload survive Gemini capacity outages, and let users delete a menu from the Nutrition tab.

## Problem
- 2026-09-22 ~18:16–18:30 every upload failed: production logs show only `503 UNAVAILABLE` from
  `gemini-3.5-flash` and `gemini-flash-latest` (the only two models in `_MODELS`). No
  `POST /nutrition/menus` response was ever logged — the client gave up during ~2+ min of retries.
- Probe on 2026-09-23 from the server: `gemini-3.5-flash` OK, `gemini-3.6-flash` OK,
  `gemini-flash-latest`/`3.7`/`3.8` 503, `gemini-2.5-flash` 404.
- There is no way to delete a diet plan (no endpoint, no UI).

## Scope
- Backend parser fallback list + retry strategy (`backend/src/infrastructure/ai/gemini_pdf_service.py`).
- `DELETE /nutrition/menus/{id}` across domain port, infra repo, use case, router, DI.
- Frontend: delete mutation hook + delete action with confirmation in the Nutrition page.

## Constraints
- Hexagonal layering as in existing nutrition slice; user can only delete own plans (404 otherwise).
- TDD: off (no project/session TDD config found); ordinary functional checks.
  Runners: `cd backend && poetry run pytest`, `cd frontend && npm test`, `npm run typecheck`, `npm run lint`.

## Tasks
- [x] T1 — Parser: add more fallback models (`gemini-3.6-flash`, `gemini-3.5-flash-lite`), fewer
  same-model retries so total latency stays bounded. Route: inline (1 file).
- [x] T2 — Backend delete endpoint + tests. Route: delegated (2+ non-trivial files, writer trigger).
- [ ] T3 — Frontend delete action + tests. Route: delegated (2+ non-trivial files, writer trigger).

## Acceptance criteria
- Parser tries 3+ models before failing; unit test covers fallback on 503.
- `DELETE /nutrition/menus/{id}` → 204 for own plan, 404 for missing/foreign plan.
- Nutrition tab shows a delete action with confirmation; list/selection refreshes after delete.

## Progress / evidence
- Branch: `fix/nutrition-upload-and-delete-menu`
- T1: commit 8671ea8. `pytest tests/unit/infrastructure/test_gemini_pdf_service.py` 2 passed; ruff clean.
  RDD assess: medium, review_due=false (under_budget) — pending in slice.
- T2: commit 92ccd88. `DELETE /nutrition/menus/{id}` → 204 own / 404 missing, malformed or foreign
  (repo `delete_for_user` scoped by user_id). `poetry run pytest backend/tests -q` 610 passed;
  `poetry run ruff check backend` all checks passed.
- Engram mirror: PENDING (mem_save failed: multiple active runtime sessions).

## Next step
T2 + T3 (delegated writer).
