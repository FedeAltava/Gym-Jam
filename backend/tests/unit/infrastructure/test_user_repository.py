"""Tests for SqlAlchemyUserRepository — RED phase first."""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.src.infrastructure.persistence.models import Base, UserModel
from backend.src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
import uuid
from datetime import datetime, UTC


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s
    await engine.dispose()


def make_user(email: str = "alice@example.com") -> UserModel:
    return UserModel(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password="$2b$12$fakehash",
        created_at=datetime.now(UTC),
    )


async def test_save_and_find_by_email(session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository()
    user = make_user("alice@example.com")
    await repo.save(user, session)
    await session.commit()
    found = await repo.find_by_email("alice@example.com", session)
    assert found is not None
    assert found.email == "alice@example.com"


async def test_find_by_email_not_found_returns_none(session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository()
    found = await repo.find_by_email("ghost@example.com", session)
    assert found is None


async def test_find_by_id_returns_user(session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository()
    user = make_user("bob@example.com")
    await repo.save(user, session)
    await session.commit()
    found = await repo.find_by_id(user.id, session)
    assert found is not None
    assert found.id == user.id
    assert found.email == "bob@example.com"


async def test_find_by_id_not_found_returns_none(session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository()
    found = await repo.find_by_id("nonexistent-id", session)
    assert found is None
