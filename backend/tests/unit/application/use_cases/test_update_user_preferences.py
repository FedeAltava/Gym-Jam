"""Tests for UpdateUserPreferencesUseCase."""
from __future__ import annotations
import uuid

import pytest
import sqlalchemy
from returns.result import Failure, Success
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.application.commands import UpdateUserPreferencesCommand
from backend.src.application.errors import DomainViolationError
from backend.src.application.use_cases.update_user_preferences import (
    UpdateUserPreferencesUseCase,
)
from backend.src.infrastructure.persistence.models import Base, UserModel
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
        hashed_password="$stub$",
    )


async def _seed_user(session: AsyncSession) -> UserModel:
    user = _make_user()
    session.add(user)
    await session.flush()
    return user


async def test_update_rest_seconds_only(session: AsyncSession) -> None:
    user = await _seed_user(session)

    uc = UpdateUserPreferencesUseCase(SqlAlchemyUserRepository())
    cmd = UpdateUserPreferencesCommand(user_id=user.id, rest_seconds=120)
    result = await uc.execute(cmd, session)

    assert isinstance(result, Success)
    updated = result.unwrap()
    assert updated.rest_seconds == 120
    assert updated.units == "kg"  # untouched — partial update


async def test_update_units_only(session: AsyncSession) -> None:
    user = await _seed_user(session)

    uc = UpdateUserPreferencesUseCase(SqlAlchemyUserRepository())
    cmd = UpdateUserPreferencesCommand(user_id=user.id, units="lb")
    result = await uc.execute(cmd, session)

    assert isinstance(result, Success)
    updated = result.unwrap()
    assert updated.units == "lb"
    assert updated.rest_seconds == 90  # untouched — partial update


async def test_update_both_fields(session: AsyncSession) -> None:
    user = await _seed_user(session)

    uc = UpdateUserPreferencesUseCase(SqlAlchemyUserRepository())
    cmd = UpdateUserPreferencesCommand(user_id=user.id, rest_seconds=45, units="lb")
    result = await uc.execute(cmd, session)

    assert isinstance(result, Success)
    updated = result.unwrap()
    assert updated.rest_seconds == 45
    assert updated.units == "lb"


async def test_update_persists_via_repository(session: AsyncSession) -> None:
    user = await _seed_user(session)
    repo = SqlAlchemyUserRepository()

    uc = UpdateUserPreferencesUseCase(repo)
    result = await uc.execute(
        UpdateUserPreferencesCommand(user_id=user.id, rest_seconds=180), session
    )

    assert isinstance(result, Success)
    fetched = await repo.find_by_id(user.id, session)
    assert fetched is not None
    assert fetched.rest_seconds == 180


async def test_user_not_found(session: AsyncSession) -> None:
    uc = UpdateUserPreferencesUseCase(SqlAlchemyUserRepository())
    cmd = UpdateUserPreferencesCommand(user_id="nonexistent-id", rest_seconds=120)
    result = await uc.execute(cmd, session)

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
    assert "not found" in result.failure().message
