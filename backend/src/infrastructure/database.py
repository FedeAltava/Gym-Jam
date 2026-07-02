from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.infrastructure.config import settings

# aiosqlite (used in tests) does not support connection-pool arguments —
# only pass pool kwargs when connecting to PostgreSQL.
_is_postgres = settings.database_url.startswith("postgresql")
_pool_kwargs = (
    {"pool_size": 5, "max_overflow": 10, "pool_timeout": 30} if _is_postgres else {}
)

engine = create_async_engine(settings.database_url, echo=False, **_pool_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
