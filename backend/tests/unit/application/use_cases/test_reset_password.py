"""Tests for ResetPasswordUseCase."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy
from returns.result import Failure, Success
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.application.errors import DomainViolationError
from backend.src.application.use_cases.reset_password import ResetPasswordUseCase
from backend.src.infrastructure.auth.password import hash_password, verify_password
from backend.src.infrastructure.persistence.models import Base, PasswordResetTokenModel, UserModel
from backend.src.infrastructure.persistence.password_reset_token_repository import (
    SqlAlchemyPasswordResetTokenRepository,
)
from backend.src.infrastructure.persistence.refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
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


def _make_user() -> UserModel:
    return UserModel(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4()}@example.com",
        hashed_password=hash_password("original-password"),
    )


def _make_reset_token(
    user_id: str,
    raw_token: str,
    *,
    expires_delta: timedelta = timedelta(minutes=15),
    used_at: datetime | None = None,
) -> PasswordResetTokenModel:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return PasswordResetTokenModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + expires_delta,
        used_at=used_at,
    )


async def test_reset_password_happy_path(session: AsyncSession) -> None:
    user = _make_user()
    session.add(user)
    raw_token = secrets.token_urlsafe(32)
    record = _make_reset_token(user.id, raw_token)
    session.add(record)
    await session.flush()

    user_repo = SqlAlchemyUserRepository(session)
    token_repo = SqlAlchemyPasswordResetTokenRepository(session)
    refresh_repo = SqlAlchemyRefreshTokenRepository(session)
    uc = ResetPasswordUseCase(user_repo, token_repo, refresh_repo, hash_password)
    result = await uc.execute(raw_token, "brand-new-password")

    assert isinstance(result, Success)

    updated = await user_repo.find_by_id(user.id)
    assert updated is not None
    assert verify_password("brand-new-password", updated.hashed_password)

    # Token must be marked used — re-fetch from DB.
    fetched = (
        await session.execute(
            select(PasswordResetTokenModel).where(PasswordResetTokenModel.id == record.id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    assert fetched is not None
    assert fetched.used_at is not None


async def test_reset_password_expired_token(session: AsyncSession) -> None:
    user = _make_user()
    session.add(user)
    raw_token = secrets.token_urlsafe(32)
    record = _make_reset_token(user.id, raw_token, expires_delta=timedelta(minutes=-1))
    session.add(record)
    await session.flush()

    user_repo = SqlAlchemyUserRepository(session)
    token_repo = SqlAlchemyPasswordResetTokenRepository(session)
    refresh_repo = SqlAlchemyRefreshTokenRepository(session)
    uc = ResetPasswordUseCase(user_repo, token_repo, refresh_repo, hash_password)
    result = await uc.execute(raw_token, "new-password")

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)


async def test_reset_password_used_token(session: AsyncSession) -> None:
    user = _make_user()
    session.add(user)
    raw_token = secrets.token_urlsafe(32)
    record = _make_reset_token(user.id, raw_token, used_at=datetime.now(UTC))
    session.add(record)
    await session.flush()

    user_repo = SqlAlchemyUserRepository(session)
    token_repo = SqlAlchemyPasswordResetTokenRepository(session)
    refresh_repo = SqlAlchemyRefreshTokenRepository(session)
    uc = ResetPasswordUseCase(user_repo, token_repo, refresh_repo, hash_password)
    result = await uc.execute(raw_token, "new-password")

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)


async def test_reset_password_invalid_token(session: AsyncSession) -> None:
    user_repo = SqlAlchemyUserRepository(session)
    token_repo = SqlAlchemyPasswordResetTokenRepository(session)
    refresh_repo = SqlAlchemyRefreshTokenRepository(session)
    uc = ResetPasswordUseCase(user_repo, token_repo, refresh_repo, hash_password)
    result = await uc.execute("completely-fake-token", "new-password")

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
