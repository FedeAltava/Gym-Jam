# Gym-Jam

A full-stack gym workout tracker built as a portfolio project. Manage workout plans, training days, and exercise sessions — with JWT authentication, personal records, session history, and a polished mobile-first UI.

> Built with **Clean/Hexagonal Architecture**, strict **TDD** (637 tests), and deployed via **Docker Compose**.

---

## Quick start

```bash
# 1. Clone and configure environment
git clone git@github.com:FedeAltava/Gym-Jam.git
cd Gym-Jam
cp .env.example .env   # fill in your values

# 2. Start everything
docker compose up --build

# 3. Open the app
open http://localhost
```

The `entrypoint.sh` runs Alembic migrations automatically before starting the API.

---

## Tech stack

### Backend

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Auth | PyJWT + bcrypt (cost 12) |
| Validation | Pydantic v2 + pydantic-settings |
| Package manager | Poetry |
| Testing | pytest + pytest-asyncio |
| Rate limiting | Redis sliding-window / in-memory fallback |

### Frontend

| Layer | Technology |
|-------|-----------|
| Language | TypeScript |
| Framework | React 19 + Vite |
| Styling | Tailwind CSS v3 + CSS variables |
| State | Zustand (auth) + TanStack Query v5 (server) |
| Forms | React Hook Form + Zod |
| Routing | React Router v7 |
| Testing | Vitest + React Testing Library |

### Infrastructure

| Concern | Technology |
|---------|-----------|
| Database | PostgreSQL (prod) / SQLite (dev/test) |
| Cache / rate limiting | Redis |
| Reverse proxy | nginx |
| Containerization | Docker Compose |

---

## Project structure

```
Gym-Jam/
├── backend/
│   ├── src/
│   │   ├── domain/               # Core business logic — no framework dependencies
│   │   │   ├── aggregates/       # Workout (aggregate root)
│   │   │   ├── entities/         # TrainingDay, WorkoutExercise, WorkoutSession, ExerciseLog
│   │   │   ├── value_objects/    # WorkoutId, WorkoutName, DayName, DayOfWeek…
│   │   │   ├── errors/           # Typed domain errors
│   │   │   └── repositories/     # ABC contracts (WorkoutRepository, UserRepository…)
│   │   ├── application/          # Use cases, commands, DTOs
│   │   │   └── use_cases/        # 25 async use cases
│   │   ├── infrastructure/       # Adapters (DB, auth, email, rate limiting, config)
│   │   │   ├── persistence/      # SQLAlchemy models, mapper, repositories
│   │   │   ├── auth/             # JWT + password hashing
│   │   │   ├── email/            # SMTP password reset
│   │   │   └── rate_limiter.py   # Sliding-window (Redis in prod, in-memory in dev/test)
│   │   └── presentation/         # FastAPI routers, schemas, DI, error handlers
│   ├── tests/
│   │   ├── unit/                 # Domain + application layer (in-memory repo)
│   │   ├── integration/          # Infrastructure layer (SQLite in-memory)
│   │   └── http/                 # HTTP layer (TestClient, FK constraints enabled)
│   ├── alembic/                  # Migrations (011 versions)
│   └── pyproject.toml
│
├── frontend/
│   └── src/
│       ├── pages/                # Login, Register, Dashboard, Workouts, WorkoutDetail,
│       │                         #   AddExercises, WorkoutSession, History, Profile…
│       ├── components/           # Layout, BottomNav, ProtectedRoute, dashboard cards…
│       ├── hooks/                # useAuth, useWorkouts, useSessions, useExercises,
│       │                         #   useSessionHistory, useUserStats, useUserPreferences…
│       ├── store/                # authStore (Zustand + localStorage)
│       ├── lib/                  # apiFetch (Bearer injection + 401 refresh + single-flight)
│       └── types/                # API response types
│
├── Dockerfile.backend
├── Dockerfile.frontend           # Builds React app → served by nginx
├── docker-compose.yml            # postgres + redis + backend + nginx
├── nginx.conf                    # /api/* → backend:8000, SPA fallback
└── .env.example
```

---

## Architecture

The backend follows **Hexagonal (Ports & Adapters)** architecture:

```
Presentation (FastAPI)
      │
      ▼
Application (Use Cases)          ← async def execute(), returns Result[T, DomainError]
      │
      ▼
Domain (Aggregates, Entities, Value Objects)   ← zero external dependencies
      ▲
      │
Infrastructure (SQLAlchemy, JWT, bcrypt, Redis, SMTP)
```

- The **domain** has zero framework dependencies — it can be tested in pure Python.
- **Repositories** are defined as ABCs in the domain and implemented in infrastructure.
- All use cases return `Result[T, DomainError]` from the `returns` library — no exceptions as control flow.
- The **presentation** layer translates HTTP ↔ DTOs and delegates 100% to use cases.

---

## API endpoints

### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Sign in — returns `access_token` + `refresh_token` |
| `POST` | `/auth/refresh` | Rotate refresh token — returns a new pair |
| `POST` | `/auth/logout` | Revoke refresh token |
| `GET` | `/auth/me` | Current user profile + preferences |
| `POST` | `/auth/forgot-password` | Request password reset email (rate-limited) |
| `POST` | `/auth/reset-password` | Reset password with token |
| `PATCH` | `/auth/password` | Change password (requires auth) |

### Users

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/users/me/stats` | Aggregate stats: total sessions, streak, PRs, weekly volume |
| `PATCH` | `/users/me/preferences` | Update rest timer and weight units |

### Exercise catalog

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/exercises` | List exercises, optionally filtered by `?muscle_group=` |

### Workouts

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/workouts` | Create a workout |
| `GET` | `/workouts` | List workouts for current user (paginated) |
| `GET` | `/workouts/{id}` | Get workout with all training days and exercises |
| `PATCH` | `/workouts/{id}` | Rename a workout |
| `PATCH` | `/workouts/{id}/active` | Toggle active/inactive flag |
| `DELETE` | `/workouts/{id}` | Delete a workout |
| `POST` | `/workouts/{id}/training-days` | Add a training day |
| `DELETE` | `/workouts/{id}/training-days/{day}` | Remove a training day |
| `PUT` | `/workouts/{id}/training-days/reorder` | Reorder training days |
| `POST` | `/workouts/{id}/training-days/{day}/exercises` | Add exercise to a day |
| `DELETE` | `/workouts/{id}/training-days/{day}/exercises/{ex_id}` | Remove exercise |
| `PUT` | `/workouts/{id}/training-days/{day}/exercises/reorder` | Reorder exercises |

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/workouts/{id}/days/{day_id}/sessions` | Start a workout session |
| `GET` | `/workouts/{id}/days/{day_id}/sessions` | List sessions for a training day |
| `POST` | `/sessions/{id}/logs` | Log a set (reps + weight) |
| `PATCH` | `/sessions/{id}/logs/{log_id}` | Update a logged set (partial — only sent fields updated) |
| `DELETE` | `/sessions/{id}/logs/{log_id}` | Delete a logged set |
| `POST` | `/sessions/{id}/complete` | Complete a session + detect personal records |
| `DELETE` | `/sessions/{id}` | Delete a session |
| `GET` | `/sessions` | Session history with filters (status, workout, date range, pagination) |

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe — checks DB and Redis connectivity |

Interactive docs available at `http://localhost/api/docs` when running locally.

---

## Environment variables

Copy `.env.example` to `.env` and fill in:

```env
POSTGRES_USER=gymjam
POSTGRES_PASSWORD=your_password          # use a strong password in production
POSTGRES_DB=gymjam

SECRET_KEY=your_secret_key_here          # JWT signing — generate: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=http://localhost            # comma-separated allowed origins

# Optional — enables Redis-backed rate limiting (recommended in production)
REDIS_URL=redis://redis:6379

# Optional SMTP — required for password reset emails
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=noreply@example.com

# Set to "production" to enable startup secret-key validation and disable /docs
ENVIRONMENT=development
```

---

## Running tests

```bash
# Backend — all 548 tests
cd backend
poetry run pytest

# With coverage
poetry run pytest --cov=src

# Only unit tests
poetry run pytest tests/unit

# Only HTTP tests
poetry run pytest tests/http

# Frontend — all 89 tests
cd frontend
npx vitest run
```

**637 total tests** across backend (unit / integration / HTTP) and frontend (Vitest + RTL).

---

## Local development (without Docker)

```bash
# Backend
cd backend
poetry install
poetry run uvicorn src.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL=http://localhost:8000` in `frontend/.env.local` for local dev.

---

## Known issues & technical backlog

Items identified during the architecture + security + test audit. Ordered by priority.

### Architecture violations (backend)

| ID | Severity | Description |
|----|----------|-------------|
| A-1 | **CRITICAL** | `forgot_password`, `reset_password`, `change_password` use cases import directly from `infrastructure` (SQLAlchemy models, `hash_password`, `settings`). Violates the dependency rule. Fix: define `PasswordService`, `PasswordResetTokenRepository`, and `EmailService` ports in the domain. |
| A-2 | **CRITICAL** | `UserRepository` domain port imports `AsyncSession` from SQLAlchemy — the domain must have zero infrastructure dependencies. |
| A-3 | **CRITICAL** | Three use cases accept `AsyncSession` in `execute()` — the session is an infrastructure concern and belongs in the repository constructor. |
| A-4 | **CRITICAL** | `auth.py` router contains registration business logic inline (creates `UserModel`, calls `hash_password`, writes to DB). A `RegisterUserUseCase` is missing. |
| A-5 | **WARNING** | `users.py` router instantiates `SqlAlchemyUserRepository` as a module-level singleton without a session — inconsistent with every other router in the project. |
| A-6 | **WARNING** | `ForgotPasswordUseCase` reads `settings.app_base_url` directly — config is an infrastructure concern and should be injected via the constructor. |
| A-7 | **WARNING** | `SetWorkoutActiveCommand` and `GetWorkoutsByUserQuery` are defined inside use case files instead of `commands.py`. |

### Security

| ID | Severity | Description |
|----|----------|-------------|
| S-1 | **CRITICAL** | JWT access token and refresh token are stored in `localStorage` via Zustand `persist`. Any XSS on the page can exfiltrate both tokens. Fix: keep access token in memory only; serve refresh token via `HttpOnly; SameSite=Strict` cookie. |
| S-2 | **HIGH** | `/auth/reset-password` and `/auth/password` (change) have no rate limiter — brute-force and amplification risk. |
| S-3 | **HIGH** | FastAPI `/docs` and `/redoc` are publicly accessible with no env-based disable. Exposes full API schema to attackers. Disable in production via `docs_url=None`. |
| S-4 | **HIGH** | Redis rate limiter has a TOCTOU race: count-check and increment are not atomic. Fix: use a Lua script for atomic check-and-increment. |
| S-5 | **MEDIUM** | No HTTPS in nginx config — all tokens and personal data transmitted in cleartext. |
| S-6 | **MEDIUM** | nginx has no HTTP security headers (CSP, X-Frame-Options, X-Content-Type-Options, HSTS). |
| S-7 | **MEDIUM** | `day_of_week` and `training_days` list fields have no Pydantic size/format constraints — minor DoS amplification. |
| S-8 | **LOW** | Password reset token URL logged in plaintext when SMTP is unconfigured. |
| S-9 | **LOW** | Redis connection has no password or TLS in docker-compose. |
| S-10 | **LOW** | `WorkoutSessionResponse` exposes `user_id` unnecessarily. |

### Confirmed bugs

| ID | Severity | Description |
|----|----------|-------------|
| B-1 | **BUG** | `SetExceedsPlan` domain error only checks `set_number < 1`, not `> exercise.sets`. Extra sets logged via "+ Serie extra" bypass domain validation entirely. |
| B-2 | **BUG** | Reps stepper has `min={0}`, but `handleRepsChange` applies `Math.max(1, ...)` before the API call — UI shows `0`, API receives `1`, causing a visual flicker on already-logged sets. Fix: `min={1}`. |
| B-3 | **BUG** | `WorkoutSessionPage` sorts exercises by `muscle_group` first, then `order` — this overrides the user's configured plan order. Fix: sort by `order` only. |
| B-4 | **BUG** | `ProfilePage` rest timer `commitRestEdit` closes edit mode before the mutation resolves — if the API call fails, the error is silent and the old value is shown with no feedback. |
| B-5 | **BUG** | Progress bar `totalSets` is derived from `exercise.sets` (plan total) and ignores extra sets added during the session. Counter can show `6/5`. |
| B-6 | **BUG** | `WorkoutSessionResponse` TypeScript type is missing `duration_seconds: number | null`. Code accessing this field gets `undefined` with no type error. |

### Edge cases

| ID | Severity | Description |
|----|----------|-------------|
| E-1 | **HIGH** | No guard against two simultaneous `in_progress` sessions for the same `(user_id, training_day_id)`. Two browser tabs can create duplicates. Fix: unique partial index on `(user_id, training_day_id) WHERE completed_at IS NULL`. |
| E-2 | **HIGH** | Deleting a training day cascades to sessions — the frontend holding a local `newSession` reference then gets `404` on all subsequent log calls with no navigation fallback. |
| E-3 | **HIGH** | `personal_records.session_id` uses `ondelete="CASCADE"` — deleting a session permanently removes the user's PR records. Fix: `ondelete="SET NULL"`. |
| E-4 | **MEDIUM** | Multiple active workouts allowed — `SetWorkoutActiveUseCase` does not deactivate others. Stats endpoint unions all plan days; dashboard shows only the first active workout found. Inconsistency. |
| E-5 | **MEDIUM** | PR tie (same weight as existing record) does not update `achieved_at` — the PR keeps the session reference of the original record, which may have been deleted. Fix: use `>=` instead of `>`. |
| E-6 | **LOW** | `useActiveWorkout` only scans the first paginated page of workouts. A user with 20+ workouts whose active workout is on page 2 sees the dashboard as if they have no active workout. |
| E-7 | **LOW** | `doneSets` counter uses delta callbacks — rapid log + undo interactions can undercount relative to actual server state. |

### Missing tests (highest priority)

| ID | Area | What's missing |
|----|------|----------------|
| T-1 | Backend | `set_workout_active` use case + `PATCH /workouts/{id}/active` HTTP endpoint — zero coverage at all levels |
| T-2 | Backend | `update_exercise_log` use case — `fields_set` partial-update semantics untested at unit level |
| T-3 | Backend | `delete_workout_session` use case — no unit tests |
| T-4 | Frontend | `AddExercisesPage` — the most complex page (multi-select, `Promise.allSettled`, partial failure) is completely untested |
| T-5 | Frontend | `LoginPage` and `RegisterPage` — auth entry points with Zod validation and error rendering, zero coverage |
| T-6 | Frontend | `WorkoutSessionPage` — complete session flow (click "Completar") untested |
| T-7 | Frontend | `ProtectedRoute` — the auth gate for the entire app has no test |
| T-8 | Frontend | `useAuth` mutations — `onSuccess` side-effects (store update + navigation) untested |
| T-9 | Backend | `get_session_history` — no cross-user isolation assertion |
| T-10 | Frontend | `ForgotPasswordPage` and `ResetPasswordPage` — both render states and URL token extraction untested |

### Code quality

| ID | Description |
|----|-------------|
| Q-1 | `(error as Error).message` unsafe cast used in ~15 files. Replace with a typed `getErrorMessage(e: unknown)` helper. |
| Q-2 | `user-stats` query not invalidated after `useCompleteSession` or `useDeleteSession` — Profile and Dashboard show stale stats. |
| Q-3 | `change_password` form in `ProfilePage` uses raw `useState` + `apiFetch` instead of React Hook Form + Zod + `useMutation`. |
| Q-4 | `exerciseById`, `sortedExercises`, `lastSessionLogs` rebuilt on every render in `WorkoutSessionPage`. Wrap with `useMemo`. |
| Q-5 | Dead ORM columns: `WorkoutSessionModel.duration_minutes`, `WorkoutLogModel.difficulty_rating`, `WorkoutLogModel.notes` — written nowhere. |
| Q-6 | `SlidingWindowRateLimiter.dependency` is sync; `RedisRateLimiter.dependency` is async. Extract a `RateLimiter` protocol for type safety. |
| Q-7 | `WorkoutDetailPage` has ~20 `<button>` elements missing `type="button"`. |
