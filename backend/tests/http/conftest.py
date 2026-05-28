import pytest
import sqlalchemy
from collections.abc import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.src.infrastructure.persistence.models import Base
from backend.src.infrastructure.database import get_session
from backend.src.main import create_app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    return create_async_engine(TEST_DB_URL, echo=False)


@pytest.fixture(scope="session")
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(engine, create_tables) -> AsyncGenerator[AsyncSession, None]:
    # Each test gets a fresh in-memory SQLite database session.
    # The router calls session.commit() per mutation. We do NOT try to roll back
    # between tests — instead, each test creates its own uniquely named data.
    # The session-scoped engine uses a single :memory: database so tables persist.
    async with engine.connect() as conn:
        await conn.execute(sqlalchemy.text("PRAGMA foreign_keys=OFF"))
        session_factory = async_sessionmaker(conn, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as s:
            yield s


@pytest.fixture
async def client(session) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
