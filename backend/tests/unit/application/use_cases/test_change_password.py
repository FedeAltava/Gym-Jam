"""Tests for ChangePasswordUseCase."""
from __future__ import annotations
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy
from returns.result import Failure, Success
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.application.errors import DomainViolationError
from backend.src.application.use_cases.change_password import ChangePasswordUseCase
from backend.src.infrastructure.auth.password import hash_password
from backend.src.infrastructure.persistence.models import Base, RefreshTokenModel, UserModel
from backend.src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
def engine():
    return create_async_engine(TEST_DB_URL, echo=False)


@pytest.fixture(scope="module")
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
            yield s


def _make_user(password: str = "correct-password") -> UserModel:
    return UserModel(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4()}@example.com",
        hashed_password=hash_password(password),
    )


async def test_change_password_happy_path(session: AsyncSession) -> None:
    user = _make_user("correct-password")
    session.add(user)
    await session.flush()

    repo = SqlAlchemyUserRepository()
    uc = ChangePasswordUseCase(repo)
    result = await uc.execute(user.id, "correct-password", "new-password-1", session)

    assert isinstance(result, Success)
    # Fetch the user back to verify the password was actually updated.
    updated = await repo.find_by_id(user.id, session)
    assert updated is not None
    # The stored hash should differ from the original.
    assert updated.hashed_password != hash_password("correct-password")
    from backend.src.infrastructure.auth.password import verify_password
    assert verify_password("new-password-1", updated.hashed_password)


async def test_change_password_wrong_current_password(session: AsyncSession) -> None:
    user = _make_user("correct-password")
    session.add(user)
    await session.flush()

    repo = SqlAlchemyUserRepository()
    uc = ChangePasswordUseCase(repo)
    result = await uc.execute(user.id, "wrong-password", "new-password-1", session)

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
    assert result.failure().message == "Invalid credentials"


async def test_change_password_user_not_found(session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository()
    uc = ChangePasswordUseCase(repo)
    result = await uc.execute("nonexistent-id", "any-password", "new-password-1", session)

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
    assert "not found" in result.failure().message


async def test_change_password_revokes_refresh_tokens(session: AsyncSession) -> None:
    user = _make_user("correct-password")
    session.add(user)
    await session.flush()

    now = datetime.now(UTC)
    token1 = RefreshTokenModel(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash="hash-1",
        expires_at=now + timedelta(days=7),
    )
    token2 = RefreshTokenModel(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash="hash-2",
        expires_at=now + timedelta(days=7),
    )
    session.add_all([token1, token2])
    await session.flush()

    repo = SqlAlchemyUserRepository()
    uc = ChangePasswordUseCase(repo)
    result = await uc.execute(user.id, "correct-password", "new-password-1", session)

    assert isinstance(result, Success)

    # Verify tokens are revoked in-session.
    from sqlalchemy import select
    from backend.src.infrastructure.persistence.models import RefreshTokenModel as RTM
    rows = (await session.execute(
        select(RTM).where(RTM.user_id == user.id)
    )).scalars().all()
    assert all(r.revoked_at is not None for r in rows)
