# Gym-Jam

A full-stack gym workout tracker. Manage workout plans, training days, and exercise sessions — with JWT authentication, personal records, session history, and a polished mobile-first UI.

> Built with **Clean/Hexagonal Architecture**, strict **TDD** (794 tests), and deployed via **Docker Compose** + **Traefik** with automatic HTTPS.

---

## Features

- **Workout plans** — create routines with training days (Mon–Sun) and drag-to-reorder exercises
- **Live session** — log reps and weight per set, inline edit without re-submission, extra sets on the fly
- **Rest timer** — countdown and ascending modes, preset buttons (1:00 / 1:30 / 2:00 / 3:00), Wake Lock keeps screen on
- **Sticky timer FAB** — floating button follows scroll so the timer is always one tap away, pulses green while running
- **Personal records** — auto-detected on session complete; history shows PR badge per set
- **Weight progress chart** — per-exercise line chart of max weight over time
- **Session history** — infinite scroll with workout / date / status filters
- **User preferences** — configurable rest interval and weight units (kg / lb)
- **PWA** — installable, offline-capable, push-to-home-screen on iOS and Android
- **Auth** — JWT access token + httpOnly refresh token rotation, email/password reset, case-insensitive email
- **Exercise catalog** — 90 curated exercises (15 per muscle group) with bodyweight flag

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
| Reverse proxy | Traefik v3 (automatic HTTPS via Let's Encrypt) + nginx |
| Containerization | Docker Compose |
| PWA | vite-plugin-pwa (Workbox, service worker, web manifest) |

---

## Project structure

```
Gym-Jam/
├── backend/
│   ├── src/
│   │   ├── domain/               # Core business logic — no framework dependencies
│   │   │   ├── aggregates/       # Workout (aggregate root)
│   │   │   ├── entities/         # TrainingDay, WorkoutExercise, WorkoutSession, ExerciseLog
│   │   │   ├── value_objects/    # WorkoutId, WorkoutName, DayOfWeek…
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
│   ├── alembic/                  # Migrations (018 versions)
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
# Backend — all 567 tests
cd backend
poetry run pytest

# With coverage
poetry run pytest --cov=src

# Only unit tests
poetry run pytest tests/unit

# Only HTTP tests
poetry run pytest tests/http

# Frontend — all 227 tests
cd frontend
npx vitest run
```

**794 total tests** across backend (unit / integration / HTTP) and frontend (Vitest + RTL).

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

