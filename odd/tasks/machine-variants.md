# Machine variants, quick switch in the session, and the new Torso/Pierna routines

Objective: tell plate-loaded and selectorized machines apart, switch between them in one tap during a session with suggestions from the last time that exact exercise was done, then give both accounts the shorter Torso/Pierna routine.
Branch: `feat/machine-variants` · Delivery: work-unit commits, merge/push on user approval; deploy is run by the user (the auto-mode classifier blocks Claude's SSH writes); forecast ~700 authored lines · Runners: `poetry run pytest backend/tests`, `cd frontend && npx vitest run`.

## Specs

- **S1 — Machine variants in the catalog.** "hay que añadir al listado de ejercicios general no de la rutina, ejercicios de maquina pero diferenciando si son d elos qu ese les añade discos a la maquina o los que se sube de peso bajando el palo metalico en las placas de la maquina"
  - Named "(discos)" (plate-loaded) and "(placas)" (selectorized); 16 machine exercises × 2. Existing catalog rows stay untouched (history).
- **S2 — One-tap switch to the other machine type in the session.** "no siempre puedo usar el mismo tipo de maquina en el gym porque a veces estan ocupadas y con el tiempo justo tengo que hacer la de el otro tipo, hay que encontrar la manera para el  cambio el ejercicio de la sesion" · "lo dle boton esta bnien , pero manteniendo el otro de cambiar por qu ealomejor no hay ninguna maquina libre de ese ejercicio y decido hace rotro y quiero poder cambiarlo en la sesion de entrene."
  - A button "Cambiar a placas" / "Cambiar a discos" on exercises whose current exercise has a twin variant; the existing "Cambiar" (any exercise) stays.
  - Same rules as the existing swap: only while the session is in progress and before a set of that exercise is logged.
- **S3 — Suggestions from the last time that exact exercise was done.** Proposed and accepted together with S2 (assumption: the user's "lo del botón está bien" answered "¿Hago estas dos mejoras?").
  - Each set is suggested from the latest logged set with that set number for the exercise actually done (planned or swapped), in any routine or day of the user; plan values otherwise.
- **S4 — New routines in both accounts.** "ahora necesito que repliques mi rutina de torso/pierna4xsemana en la cuenta de belen ... modifica esas rutinas para que lunes y jueves sean mas cortas ... el jueves a ella le pongas uno o dos ejercicios de pierna y lo demas enfocado al culo y a mi uno o dos de pierna y el resto de hombro." Proposal approved ("si", "me parece bien lo que propones para no perder el historial").
  - New routines (old ones renamed "(anterior)" and inactive, so no logged set is deleted); plan weights from each user's last logged weight; machine variant per exercise pending the user's answer.

## Tasks

| ID | Specs | Route | Status | Evidence |
|----|-------|-------|--------|----------|
| T1 | S1 catalog migration 023 + seed + test | inline | done | 66740be; RED KeyError → GREEN; Postgres 16: 88→120, downgrade 88, upgrade 120; backend 716 passed |
| T2 | S3 backend: `GET /exercises/last-sets` | inline (frontend depends on it) | done | 5587661; RED 6 failing (no route) → GREEN; backend 722 passed; ruff clean; mypy unchanged (36 pre-existing) |
| T3 | S2, S3 frontend: twin button, suggestions from T2, SetRow re-seeds late suggestions | inline (same file as T2's consumer) | done | RED 6 failing → GREEN 37/37; frontend 289 passed; tsc + eslint clean; not checked in the real app |
| T4 | Deploy (user runs the script) | user | pending | |
| T5 | S4 prod routines (dry run, then commit) | inline script, user-authorized | pending | |

## Log

- L1 (2026-11-13) Routine request (S4 quote) and catalog request (S1 quote), then the session switch request (S2 quotes).
- L2 (2026-11-13) Prod snapshot (read-only, authorized): Fede active "Torso/Pierna 4×/semana" 6ced068b (24 ex/68 sets), Belén active ce28ac1f (copied from the old "Recomposición"). Removing exercises from a routine cascade-deletes their logged sets (migration 005) → new routines instead.
- L3 (2026-11-13) Existing swap already lets the user pick "(placas)" from the sheet; gaps: several taps, and suggestions only from the same training day's sessions. Swapping to the planned exercise removes the swap (domain), so the twin button can always PUT the twin id.
