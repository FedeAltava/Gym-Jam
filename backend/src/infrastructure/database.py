from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.infrastructure.config import settings

# aiosqlite (used in tests) does not support connection-pool arguments —
# only pass pool kwargs when connecting to PostgreSQL.
_is_postgres = settings.database_url.startswith("postgresql")
_pool_kwargs = (
    {"pool_size": 5, "max_overflow": 10, "pool_timeout": 30} if _is_postgres else {}
)

engine = create_async_engine(settings.database_url, echo=False, **_pool_kwargs)


# SQLite disables foreign-key enforcement per connection by default, so
# ON DELETE CASCADE never fires (e.g. deleting a TrainingDay would orphan its
# workout_sessions / workout_logs). Emit PRAGMA foreign_keys=ON on every new
# SQLite connection. PostgreSQL enforces FKs natively, so this is a no-op there.
if not _is_postgres:

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
