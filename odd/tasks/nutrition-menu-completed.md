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
| T1 | S1 backend (column + migration 026 + PATCH) | inline (no writer reason) | pending | |
| T2 | S1 frontend (checkbox on the card) | inline (no writer reason) | pending | |

Risk: T1 item 1 (schema migration, additive column with default) → own commit. Forecast ~250 authored lines (< 400).

## Log

- L1 (2026-11-16) "hola en el apartado de nutricion estaria bien que cada menu tuviese un check box para saber si lo hemos completado o no"
