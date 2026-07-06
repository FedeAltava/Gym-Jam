# Gym-Jam

A full-stack gym workout tracker built as a portfolio project. Manage workout plans, training days, and exercise sessions — with JWT authentication and a clean, mobile-first UI.

> Built with **Clean/Hexagonal Architecture**, strict **TDD** (473 tests), and deployed via **Docker Compose**.

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
| Auth | PyJWT + bcrypt |
| Validation | Pydantic v2 + pydantic-settings |
| Package manager | Poetry |
| Testing | pytest + pytest-asyncio |

### Frontend

| Layer | Technology |
|-------|-----------|
| Language | TypeScript |
| Framework | React 19 + Vite |
| Styling | Tailwind CSS |
| State | Zustand (auth) + TanStack Query (server) |
| Forms | React Hook Form + Zod |
| Routing | React Router v7 |

### Infrastructure

| Concern | Technology |
|---------|-----------|
| Database | PostgreSQL |
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
│   ├── alembic/                  # Migrations
│   └── pyproject.toml
│
├── frontend/
│   └── src/
│       ├── pages/                # Login, Register, Dashboard, WorkoutDetail, AddExercises, WorkoutSession…
│       ├── components/           # Layout, BottomNav, ProtectedRoute, WorkoutCard…
│       ├── hooks/                # useAuth, useWorkouts, useSessions, useExercises (TanStack Query)
│       ├── store/                # authStore (Zustand + localStorage)
│       ├── lib/                  # apiFetch (Bearer injection + 401 refresh + retry)
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
Application (Use Cases)
      │
      ▼
Domain (Aggregates, Entities, Value Objects)   ← no external dependencies
      ▲
      │
Infrastructure (SQLAlchemy, JWT, bcrypt, Redis, SMTP)
```

- The **domain** has zero framework dependencies — it can be tested in pure Python.
- **Repositories** are defined as ABCs in the domain and implemented in infrastructure.
- All use cases are `async def execute()` and work against the repository contract, not the implementation.

---

## API endpoints

### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Sign in — returns `access_token` + `refresh_token` |
| `POST` | `/auth/refresh` | Rotate refresh token — returns a new pair |
| `POST` | `/auth/logout` | Revoke refresh token |
| `GET` | `/auth/me` | Current user (requires auth) |
| `POST` | `/auth/forgot-password` | Request password reset email |
| `POST` | `/auth/reset-password` | Reset password with token |
| `PATCH` | `/auth/password` | Change password (requires auth) |

### Exercise catalog

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/exercises` | List exercises, optionally filtered by `?muscle_group=` |

### Workouts

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/workouts` | Create a workout |
| `GET` | `/workouts` | List workouts for current user |
| `GET` | `/workouts/{id}` | Get workout with all training days |
| `PATCH` | `/workouts/{id}` | Rename a workout |
| `PATCH` | `/workouts/{id}/active` | Toggle active/inactive |
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
| `PATCH` | `/sessions/{id}/logs/{log_id}` | Update a logged set |
| `POST` | `/sessions/{id}/complete` | Complete a session |
| `DELETE` | `/sessions/{id}` | Delete a session |

Interactive docs available at `http://localhost/api/docs` when running locally.

---

## Environment variables

Copy `.env.example` to `.env` and fill in:

```env
POSTGRES_USER=gymjam
POSTGRES_PASSWORD=your_password
POSTGRES_DB=gymjam

SECRET_KEY=your_secret_key_here          # used for JWT signing — generate with: openssl rand -hex 32
CORS_ORIGINS=http://localhost            # comma-separated allowed origins

# Optional — set to enable Redis-backed rate limiting (recommended in production)
REDIS_URL=redis://redis:6379

# Optional SMTP — required for password reset emails
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=noreply@example.com
```

---

## Running tests

```bash
# All tests
cd backend
poetry run pytest

# With coverage
poetry run pytest --cov=src

# Only unit tests
poetry run pytest tests/unit

# Only HTTP tests
poetry run pytest tests/http
```

473 tests across unit, integration, and HTTP layers.

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
