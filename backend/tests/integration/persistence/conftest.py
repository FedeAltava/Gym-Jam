from datetime import UTC, datetime

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.infrastructure.persistence.models import Base, UserModel

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# User ids referenced by the persistence test suite. Seeded before every test so
# that DB-level foreign keys (now enforced via PRAGMA foreign_keys=ON) are
# satisfied when tests insert Workout / WorkoutSession rows. Add new ids here if
# a new test introduces one.
_SEED_USER_IDS = (
    "user-1",
    "user-2",
    "user-a",
    "user-abc",
    "user-alice",
    "user-b",
    "user-bob",
    "user-complete",
    "user-filter",
    "user-multi",
    "user-order",
    "user-ordering",
)


@pytest.fixture(scope="session")
def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Enforce foreign keys on every SQLite connection (OFF by default per
    # connection). Without this, ON DELETE CASCADE never fires and deleting a
    # TrainingDay would orphan its workout_sessions / workout_logs.
    @event.listens_for(eng.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return eng


@pytest.fixture(scope="session")
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(engine, create_tables) -> AsyncSession:
    async with engine.connect() as conn:
        async with async_sessionmaker(conn, class_=AsyncSession, expire_on_commit=False)() as s:
            async with s.begin():
                # Seed the users referenced by the suite so FK constraints pass.
                for uid in _SEED_USER_IDS:
                    s.add(
                        UserModel(
                            id=uid,
                            email=f"{uid}@example.com",
                            hashed_password="x",
                            created_at=datetime.now(UTC),
                        )
                    )
                await s.flush()
                yield s
                await s.rollback()
