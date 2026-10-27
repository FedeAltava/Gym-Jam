# Nutrition: per-person menu variants (Fede / Belén)

Objective: one menu card per nutritionist menu with a Fede/Belén selector, loaded from the user's PDFs with descriptive titles.
Branch: `feat/nutrition-person-variants` · Delivery: work-unit commits, push/deploy on user approval · Runners: `poetry run pytest backend/tests`, `cd frontend && npx vitest run`.

## Specs

- **S1 — Selector.** "hay diferente smenus pero repetido dos veces porqu elso que tienen mas calorias son para mi fede y los qu emenos son para belen, habria qu ehacer alusion en el titulo de esoo crear un selector dentro del menu y que ca,mbie la vista entre el de belen y el de fede" → user chose "vamos con el selector, opción 2".
  - Backend: diet plans get two optional fields, `group_id` (variants of the same menu share it) and `person` (variant label, e.g. "Fede"); returned by list and detail endpoints. Existing menus (both null) behave as before.
  - Frontend: the list shows one card per group; the detail shows a selector with the group's persons that switches the shown variant. Variants ordered by calories, highest first (Fede first).
  - Deleting a grouped menu deletes all its variants (assumption: the card represents the whole menu).
- **S2 — Load the menus with descriptive titles.** "quiero pasarte lso menus y qu elso crees tu en la app, ademas que les des distintos nombres que hagan alusion a algo de dentro del menu qu eme sirva para saber que contiene y diferenciarlso de lso otros"
- **S3 — No duplicates; calories decide the person.** "si hay archivos que contrienen lo mismo osea que es el mismo menu pero te lo he pasado dos o mas veces, crea solo uno, tenoiendo encuenta lo que te dije de el numero de calorias de lso menus que los que mas son para fede y lso que menos para belen"
- **S4 — Remove the old menu.** "por cierto el menu que ya existia hay que borrarlo"

## Tasks

| ID | Specs | Route | Status | Evidence |
|----|-------|-------|--------|----------|
| T1 | S1 backend | inline | done | 8ffc95c; RED 10 failing → GREEN 632 passed; migration up/down/up on Postgres 16 |
| T2 | S1 frontend | inline | done | b8918fe; RED 3 failing + missing module → GREEN 267 passed, tsc + eslint clean |
| T3 | S2, S3 extraction + dedupe | delegated (3 read-only extractors, context backstop: 30 PDFs) | done | 30 JSON validated with ParsedMenu; 15 menus; loader dry-tested on temp SQLite |
| T4 | S2, S3, S4 deploy + load in prod + delete old menu | inline | done | main 4bac1a8 pushed + deployed (migration 019→020); prod: 30 plans / 15 groups / 15 Fede + 15 Belén per account, 0 old menus |

Risk: T1 item 1 (schema migration, additive nullable columns) → own commit.

## Log

- L1 (2026-10-27) "ahora mismo subo un pdf y con la llamada  ala api de gemini gratuita se crea el menu, pero quiero pasarte lso menus y qu elso crees tu en la app, ademas que les des distintos nombres que hagan alusion a algo de dentro del menu qu eme sirva para saber que contiene y diferenciarlso de lso otros se podria?"
- L2 (2026-10-27) S1 quote above; user picked option 2 (selector) over title-only.
- L3 (2026-10-27) 31 PDFs in ~/Descargas. md5: only `S1 XXIII ED. 1500 Kcal (1)` is a byte copy. Dish-name comparison: each FEDE/BELÉN pair of a week and each 1500/2100 pair of an edition+week is the same menu → 15 candidate menus; cross-edition duplicates to confirm from extracted dishes.
- L4 (2026-10-27) S4 quote; the old menu is deleted in prod when loading the new ones.
- L5 (2026-10-27) Extraction done: 15 menus × (Fede, Belén). Max same-meal overlap between different menus 6/12 (S1 vs S1 XXVII) → no duplicates beyond the byte copy. Fede/Belén variants sometimes differ in a dish, not only quantities (kept per person). Calories only known for 2100/1500 editions and S2 FEDE; loader makes Fede 1 s newer so ties still show Fede first. Titles de-duplicated by hand (agents' proposals repeated quinoa/boloñesa/bacalao).
- L6 (2026-10-27) RDD assess on 8ffc95c: high (executable_change + escalated item 1) → independent verifier launched, then native review.
- L7 (2026-10-27) Independent verifier on 8ffc95c: PASS, no blockers (632 passed, probes for grouped/ungrouped delete and payloads, baseline diff = only 2 added null keys, migration 019→020→019→020 on Postgres with a pre-existing row, `alembic check` clean). Native review (lineage review-a359d13c92236271, lenses risk+reliability, range 69d793f..56d376c): consent granted, approved, acknowledged. Advisory follow-ups (non-blocking): delete returns 204 if the plan vanishes between lookup and delete (baseline 404); null-person grouped cards render an empty subtitle (untested; not produced by the loader).
- L8 (2026-10-27) Prod has two old menus "MENÚ S1 XXVII Ed. Reto REMUS30": 2100 kcal in fedealtava1992@gmail.com, 1500 kcal in bchiquinquira40@gmail.com (likely Belén's own account). Asked user which accounts to load/clean.
- L9 (2026-10-27) User chose "Mi cuenta y la de Belén". Fast-forwarded main to 4bac1a8, pushed, server `git pull` + `docker compose up -d --build --no-deps backend frontend` (backend healthy, alembic 020). Loader dry run then COMMIT=1: deleted "MENÚ S1 XXVII Ed. Reto REMUS30" in both accounts and created 15 grouped menus in each (fedealtava1992@gmail.com, bchiquinquira40@gmail.com). Feature closed.
