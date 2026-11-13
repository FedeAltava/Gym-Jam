# Exercise how-to guides (Free Exercise DB)

Objective: each catalog exercise links to a Free Exercise DB entry (public domain): self-hosted photos and Spanish steps, shown from the workout session ("Cómo se hace" sheet) and as thumbnails in the swap sheet. Frontend only: static data, no migration, no API change.
Branch: `feat/exercise-howto` · Delivery: work-unit commits, merge/push/deploy on user approval; forecast ~900 authored lines (≈ half translated content) plus ~200 WebP images · Runner: `cd frontend && npx vitest run`, `npx tsc -b`, `npx eslint .`.

## Specs

- **S1 — The new views from the mockup.** "si haz las nuevas vistas" (mockup https://claude.ai/artifact/2fgPMtyDdJAVSv9ZHwCfS8):
  - Session exercise card: a "Cómo se hace" button next to "Cambiar" / "Cambiar a placas", only when the exercise done in that slot has a guide (a swap shows the swapped-in exercise's guide). Available in a completed session too.
  - "Cómo se hace" sheet: the exercise name, the two photos ("1 · Inicio", "2 · Final"), muscle chips (primary highlighted, secondaries muted) plus the level ("Principiante" / "Intermedio" / "Avanzado"), numbered Spanish steps, the credit "Fotos y pasos: Free Exercise DB (dominio público)", and an "Entendido" button that closes it (also the close button and tapping outside).
- **S2 — No thumbnail on the session card.** "pero quita la miniatura de la tarjeta de los ejercicios en sesion".
- **S3 — Swap sheet with photos.** Each exercise row of the "Cambiar …" sheet shows a thumbnail of its first photo; an exercise without a guide shows a placeholder and "Sin foto todavía".
- **S4 — Content.** Catalog exercises are linked to the closest Free Exercise DB entry; exercises without a fitting entry have no guide (no button, placeholder in the swap sheet). Photos are self-hosted (WebP, resized) and not precached by the PWA; steps are Spanish, translated and condensed from the entry's instructions.

## Tasks

| ID | Specs | Route | Status | Evidence |
|----|-------|-------|--------|----------|
| T1 | S4 data scaffolding: mapping, images, types/index, skeleton files, integrity test | inline | done | 1c41aff · 86 guides for 113 of 121 catalog ids, 172 WebP (480 px, q72) ≈ 2.5 MB; integrity test RED 89 (empty steps) → GREEN 262 |
| T2 | S4 Spanish steps: chest+shoulders / back+arms / legs+core | 3 delegated writers (parallel units, disjoint files) | done | 1c41aff · each writer: its ids green in exerciseGuides.test.ts; parent spot-checked back/arms/chest |
| T3 | S1, S2, S3 UI: how-to sheet, card button, swap thumbnails, tests | inline (parallel with T2) | done | 62e374c · RED 5 of 7 new tests (2 pin S2 / no-guide) → GREEN; WorkoutSessionPage.test.tsx 54 passed |
| T4 | Checks, commit, deploy on approval | parent | in progress | vitest 577/577, tsc 0, eslint 0 errors (1 pre-existing warning in ProtectedRoute.tsx), build ok (86 guide folders in dist, none in sw precache); Playwright 390×844 screenshots of card, sheet, swap sheet match the mockup; RDD assess a79bb88..62e374c: medium, under_budget (no review due). Deploy pending user approval |

Risk: none of items 1–4 (static frontend data, no stored data or contracts); deploy (item 5) only on user approval.

## Log

- L1 (2026-11-13) "si haz las nuevas vistas pero quita la miniatura de la tarjeta de los ejercicios en sesion" (after the Free Exercise DB review and the mockup canvas).
- L2 (2026-11-13) Map: catalog = 89 seed + 32 machine variants (migration 023); session card `ExerciseBlock` in `frontend/src/pages/WorkoutSessionPage.tsx`, swap sheet `frontend/src/components/sessions/ExerciseSwapSheet.tsx`; PWA `globPatterns` excludes jpg/webp (no precache); nginx caches images 1y. Decision: static frontend data keyed by catalog id (precedent `lib/machineVariants.ts`) instead of a DB migration — lower risk, no API change.
- L3 (2026-11-13) T1/T3: no guide for dragon-flag, toe-to-bar, landmine-press, lateral-raise-machine-*, glute-kickback-machine-* (no fitting entry). Card buttons moved to one wrapping row under the title ("Cómo se hace", "Cambiar", "Cambiar a …"), as in the mockup. Page tests mock `getExerciseGuide` (content-independent); the data test checks the real content.
- L4 (2026-11-13) T2 writers' flags: Push_Press and Side_Bridge have no source instructions and Cable_Seated_Lateral_Raise is an unusual seated crossed-cable variant → dropped (push-press, side-plank, cable-lateral-raise have no guide; pinned in the data test). Machine_Bench_Press foot-lever steps made conditional ("si la máquina tiene palanca de pie"). Kept as published: Pullover primary chest, Mountain_Climbers primary quadriceps; calf-raise shares the standing calf machine guide.
