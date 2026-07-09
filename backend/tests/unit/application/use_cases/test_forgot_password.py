"""Tests for ForgotPasswordUseCase."""
from __future__ import annotations

import uuid

import pytest
import sqlalchemy
from returns.result import Success
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.application.use_cases.forgot_password import ForgotPasswordUseCase
from backend.src.infrastructure.auth.password import hash_password
from backend.src.infrastructure.persistence.models import Base, PasswordResetTokenModel, UserModel
from backend.src.infrastructure.persistence.password_reset_token_repository import (
    SqlAlchemyPasswordResetTokenRepository,
)
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


async def test_forgot_password_unknown_email(session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository(session)
    token_repo = SqlAlchemyPasswordResetTokenRepository(session)
    uc = ForgotPasswordUseCase(repo, token_repo, "http://test.local")

    result = await uc.execute("nobody@example.com")

    assert isinstance(result, Success)
    assert result.unwrap() is None


async def test_forgot_password_creates_token_record(session: AsyncSession) -> None:
    user = UserModel(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4()}@example.com",
        hashed_password=hash_password("password"),
    )
    session.add(user)
    await session.flush()

    repo = SqlAlchemyUserRepository(session)
    token_repo = SqlAlchemyPasswordResetTokenRepository(session)
    uc = ForgotPasswordUseCase(repo, token_repo, "http://test.local")

    result = await uc.execute(user.email)

    assert isinstance(result, Success)
    notification = result.unwrap()
    assert notification is not None
    returned_email, reset_url = notification
    assert returned_email == user.email
    assert "reset-password?token=" in reset_url

    rows = (
        await session.execute(
            select(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == user.id)
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].used_at is None
    assert rows[0].expires_at is not None
