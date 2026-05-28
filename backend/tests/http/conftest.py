import pytest
import sqlalchemy
from collections.abc import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.src.infrastructure.persistence.models import Base
from backend.src.infrastructure.database import get_session
from backend.src.presentation.dependencies import get_current_user_id
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
    """Client with get_current_user_id stubbed — for workout tests that don't need real auth."""
    app = create_app()

    async def override_get_session():
        yield session

    def override_get_current_user_id() -> str:
        return "00000000-0000-0000-0000-000000000001"

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(session) -> AsyncGenerator[AsyncClient, None]:
    """Client with NO get_current_user_id override — tests real auth flow."""
    app = create_app()

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    # Note: get_current_user_id is NOT overridden here
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
