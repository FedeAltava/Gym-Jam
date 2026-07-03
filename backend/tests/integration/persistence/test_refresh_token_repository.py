"""Integration tests for SqlAlchemyRefreshTokenRepository.

Uses a FILE-based SQLite database (not :memory:) so two truly independent
sessions/connections can simulate concurrent requests racing on a row.
"""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.infrastructure.persistence.models import Base, RefreshTokenModel
from backend.src.infrastructure.persistence.refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)

USER_ID = "user-1"


@pytest.fixture
async def file_engine(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/refresh_race.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(file_engine):
    return async_sessionmaker(file_engine, class_=AsyncSession, expire_on_commit=False)


async def _insert_token(
    session_factory, token_id: str, token_hash: str, user_id: str = USER_ID, **overrides
) -> None:
    async with session_factory() as session:
        session.add(
            RefreshTokenModel(
                id=token_id,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=overrides.get("expires_at", datetime.now(UTC) + timedelta(days=7)),
                revoked_at=overrides.get("revoked_at"),
                replaced_by_id=overrides.get("replaced_by_id"),
            )
        )
        await session.commit()


# 1. A refresh request that loses the revoke race against a LOGOUT must see
# the committed DB state on re-read — NOT values fabricated in its own
# identity map by the losing UPDATE — so it takes the theft/401 path.
async def test_lost_revoke_race_against_logout_reads_committed_state(session_factory) -> None:
    token_id = str(uuid.uuid4())
    token_hash = f"hash-{uuid.uuid4()}"
    await _insert_token(session_factory, token_id, token_hash)

    async with session_factory() as loser_session, session_factory() as winner_session:
        loser = SqlAlchemyRefreshTokenRepository(loser_session)
        winner = SqlAlchemyRefreshTokenRepository(winner_session)

        # The refresh request loads the token first — the instance now lives
        # in the loser session's identity map.
        loaded = await loser.get_by_hash(token_hash)
        assert loaded is not None and not loaded.is_revoked

        # A concurrent LOGOUT wins: revokes with NO replacement and commits.
        assert await winner.revoke(token_id) is True
        await winner_session.commit()

        # The loser's rotation attempt matches 0 rows...
        assert await loser.revoke(token_id, replaced_by_id=str(uuid.uuid4())) is False
        # ...and its re-read MUST reflect the logout revocation: revoked_at
        # set, replaced_by_id NULL → no rotation grace, session is dead.
        current = await loser.get_by_hash(token_hash)
        assert current is not None
        assert current.revoked_at is not None
        assert current.replaced_by_id is None


# 2. revoke_all_for_user closes rotation grace windows: already-rotated rows
# lose their replaced_by_id so a replay after a family nuke gets no grace.
async def test_revoke_all_for_user_clears_rotation_grace(session_factory) -> None:
    rotated_id = str(uuid.uuid4())
    active_id = str(uuid.uuid4())
    foreign_id = str(uuid.uuid4())
    await _insert_token(
        session_factory,
        rotated_id,
        f"hash-{uuid.uuid4()}",
        revoked_at=datetime.now(UTC) - timedelta(seconds=5),
        replaced_by_id=active_id,
    )
    await _insert_token(session_factory, active_id, f"hash-{uuid.uuid4()}")
    await _insert_token(session_factory, foreign_id, f"hash-{uuid.uuid4()}", user_id="user-2")

    async with session_factory() as session:
        repo = SqlAlchemyRefreshTokenRepository(session)
        await repo.revoke_all_for_user(USER_ID)
        await session.commit()

        rotated = await repo.get_by_id(rotated_id)
        active = await repo.get_by_id(active_id)
        foreign = await repo.get_by_id(foreign_id)
        assert rotated is not None and rotated.is_revoked
        assert rotated.replaced_by_id is None  # grace window closed
        assert active is not None and active.is_revoked
        assert foreign is not None and not foreign.is_revoked
