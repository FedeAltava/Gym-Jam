import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import sqlalchemy
from backend.src.infrastructure.persistence.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    return create_async_engine(TEST_DATABASE_URL, echo=False)

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
        await conn.execute(sqlalchemy.text("PRAGMA foreign_keys=OFF"))
        async with async_sessionmaker(conn, class_=AsyncSession, expire_on_commit=False)() as s:
            async with s.begin():
                yield s
                await s.rollback()
