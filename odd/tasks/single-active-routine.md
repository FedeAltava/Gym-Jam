# Single active routine

## Objective
A user has at most one active routine, so Home always shows the routine they are actually following.

## Problem
- Every new workout is created with `is_active=True` (`backend/src/domain/aggregates/workout.py`).
- `SetWorkoutActiveUseCase` activates a workout without deactivating the user's others.
- Home (`frontend/src/hooks/useActiveWorkout.ts`) picks the first active workout, so with several active it can show the wrong one
  (user follows "Siclaisimo", Home shows "Torso/pierna 4x/semana").

## Scope
- Activating a workout deactivates every other workout of the same user, atomically.
- A newly created workout is active only if the user has no active workout.
- Out of scope: data migration for users already having several active workouts (activating one fixes it).

## Constraints
- Hexagonal architecture: domain port change + infra implementation + use case logic.
- Backend only; frontend already invalidates `['workouts']` on activation.

## Tasks
- [x] T1 — Activating a workout deactivates the user's other workouts (route: delegated direct; writer trigger: port + repo + use case + tests)
- [x] T2 — New workout is active only when the user has no active workout (route: delegated direct, same writer)

## Acceptance criteria
- PATCH `/workouts/{id}/active` with `is_active=true` leaves exactly one active workout for that user; other users unaffected.
- Deactivating does not touch other workouts.
- Creating a workout with none active → active; with one active → inactive.

## Checks
- TDD: on (project convention: Strict TDD in prior SDD work; runner `poetry run pytest`).
- `poetry run pytest backend/tests`
- Frontend untouched; `npx vitest run` in `frontend/` only if frontend changes.

## Delivery
- Branch `feat/single-active-routine`, strategy `ask-on-risk`, forecast < 400 authored lines (single PR / ff-merge).

## Progress
- Created 2026-09-24.
- Baseline: `poetry run pytest backend/tests` → 610 passed.
- T1 done — commit `7d45caf` (`feat(workouts): keep a single active workout per user on activation`).
  - New port `WorkoutRepository.deactivate_all_for_user(user_id, except_id)`; SQLAlchemy bulk UPDATE in the request session, committed by the router together with the save; in-memory fake updated.
  - RED: 3 failing (unit activate-deactivates-others, integration `deactivate_all_for_user` missing, http PATCH leaves one active). GREEN: targeted 68 passed; full suite 618 passed.
- T2 done — commit `0a427aa` (`feat(workouts): create new workouts inactive when one is already active`).
  - New port `WorkoutRepository.has_active_workout(user_id)`; `CreateWorkoutUseCase` deactivates the new aggregate when the user already has an active one (factory unchanged).
  - http `test_create_workout_returns_201` no longer asserts `is_active is True` (shared test DB makes it order-dependent); new http test covers inactive-on-create.
  - RED: 3 failing (unit second-workout inactive, integration `has_active_workout` missing, http create inactive). GREEN: full suite 624 passed.
- Not covered: untracked `backend/scripts/seed_routine.py` inserts workouts via raw SQL with `is_active=1`, bypassing the use case.
- Known limit: two concurrent creates for a user with no active workout could both become active (no lock); activating any workout resolves it.
- Review assess (base main, committed-only): risk medium, `review_due=false` (`under_budget`, 312 lines); no native review required.
- Next: delivery decision (merge to main, push, deploy backend) by the user.
