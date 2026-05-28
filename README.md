# Gym-Jam

A full-stack gym workout tracker built as a portfolio project. Manage workout plans, training days, and exercises — with JWT authentication and a clean, modern UI.

> Built with **Clean/Hexagonal Architecture**, strict **TDD** (278 tests), and deployed via **Docker Compose**.

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
| Styling | Tailwind CSS + shadcn/ui |
| State | Zustand (auth) + TanStack Query (server) |
| Forms | React Hook Form + Zod |
| Routing | React Router v7 |

### Infrastructure

| Concern | Technology |
|---------|-----------|
| Database | PostgreSQL |
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
│   │   │   ├── entities/         # TrainingDay, WorkoutExercise
│   │   │   ├── value_objects/    # WorkoutId, WorkoutName, DayName, DayOfWeek…
│   │   │   ├── errors/           # Typed domain errors
│   │   │   ├── events/           # Domain events
│   │   │   └── repositories/     # ABC contracts (WorkoutRepository)
│   │   ├── application/          # Use cases, commands, DTOs, validators
│   │   │   └── use_cases/        # 8 async use cases
│   │   ├── infrastructure/       # Adapters (DB, auth, config)
│   │   │   ├── persistence/      # SQLAlchemy models, mapper, repositories
│   │   │   └── auth/             # JWT + password hashing
│   │   └── presentation/         # FastAPI routers, schemas, DI, error handlers
│   ├── tests/
│   │   ├── unit/                 # Domain + application layer (in-memory repo)
│   │   ├── integration/          # Infrastructure layer (SQLite in-memory)
│   │   └── http/                 # HTTP layer (TestClient)
│   ├── alembic/                  # Migrations
│   └── pyproject.toml
│
├── frontend/
│   └── src/
│       ├── pages/                # LoginPage, RegisterPage, Dashboard, NewWorkout, WorkoutDetail
│       ├── components/           # Layout, ProtectedRoute, WorkoutCard, shadcn/ui
│       ├── hooks/                # useAuth, useWorkouts (TanStack Query)
│       ├── store/                # authStore (Zustand + localStorage)
│       ├── lib/                  # apiFetch (Bearer injection + 401 redirect), queryClient
│       └── types/                # API response types
│
├── Dockerfile.backend
├── Dockerfile.frontend           # Builds React app → served by nginx
├── docker-compose.yml            # postgres + backend + nginx
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
Infrastructure (SQLAlchemy, JWT, bcrypt)
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
| `POST` | `/auth/login` | Get JWT token |
| `GET` | `/auth/me` | Current user (requires auth) |

### Workouts

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/workouts` | List workouts for current user |
| `POST` | `/workouts` | Create a workout |
| `GET` | `/workouts/{id}` | Get workout with all training days |
| `DELETE` | `/workouts/{id}` | Delete a workout |
| `POST` | `/workouts/{id}/training-days` | Add a training day |
| `DELETE` | `/workouts/{id}/training-days/{day_id}` | Remove a training day |
| `POST` | `/workouts/{id}/training-days/{day_id}/exercises` | Add exercise to a day |
| `DELETE` | `/workouts/{id}/training-days/{day_id}/exercises/{ex_id}` | Remove exercise |

Interactive docs available at `http://localhost/api/docs` when running locally.

---

## Environment variables

Copy `.env.example` to `.env` and fill in:

```env
POSTGRES_USER=gymjam
POSTGRES_PASSWORD=your_password
POSTGRES_DB=gymjam

SECRET_KEY=your_secret_key_here          # used for JWT signing
DATABASE_URL=postgresql+asyncpg://...    # auto-built in docker-compose
CORS_ORIGINS=http://localhost            # comma-separated allowed origins
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

278 tests across unit, integration, and HTTP layers.

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
