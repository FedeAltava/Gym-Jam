from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.src.main import create_app


@pytest.fixture
async def bare_client():
    """Bare create_app() client with no dependency overrides.

    The health probe intentionally bypasses get_session and hits the engine
    directly, so we don't need (nor want) session overrides here.
    """
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# 1. Happy path — no Redis configured (default test environment)
# ---------------------------------------------------------------------------

async def test_health_ok_redis_disabled(bare_client):
    """GET /health returns 200 with redis='disabled' when redis_url is empty."""
    # The default test settings have redis_url="" so the probe is skipped.
    # We still need to make the DB probe succeed without a real DB, so patch it.
    with patch(
        "backend.src.presentation.routers.health._check_database",
        new_callable=AsyncMock,
        return_value=True,
    ):
        r = await bare_client.get("/health")

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "disabled"


# ---------------------------------------------------------------------------
# 2. Database down → 503
# ---------------------------------------------------------------------------

async def test_health_db_down_returns_503(bare_client):
    """When the DB probe fails the endpoint returns 503 with status='degraded'."""
    with patch(
        "backend.src.presentation.routers.health._check_database",
        new_callable=AsyncMock,
        return_value=False,
    ):
        r = await bare_client.get("/health")

    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "error"
    assert body["checks"]["redis"] == "disabled"


# ---------------------------------------------------------------------------
# 3. Redis configured and reachable → 200
# ---------------------------------------------------------------------------

async def test_health_redis_ok(bare_client):
    """When redis_url is set and ping succeeds, redis check returns 'ok'."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.aclose = AsyncMock()

    with (
        patch(
            "backend.src.presentation.routers.health.settings",
            redis_url="redis://localhost:6379",
        ),
        patch(
            "backend.src.presentation.routers.health._check_database",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "backend.src.presentation.routers.health.aioredis.from_url",
            return_value=mock_redis,
        ),
    ):
        r = await bare_client.get("/health")

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["checks"]["redis"] == "ok"
    assert body["checks"]["database"] == "ok"


# ---------------------------------------------------------------------------
# 4. Redis configured but unreachable → 503
# ---------------------------------------------------------------------------

async def test_health_redis_down(bare_client):
    """When redis_url is set but ping raises, redis check returns 'error' and status is 503."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=ConnectionError("refused"))
    mock_redis.aclose = AsyncMock()

    with (
        patch(
            "backend.src.presentation.routers.health.settings",
            redis_url="redis://localhost:6379",
        ),
        patch(
            "backend.src.presentation.routers.health._check_database",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "backend.src.presentation.routers.health.aioredis.from_url",
            return_value=mock_redis,
        ),
    ):
        r = await bare_client.get("/health")

    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "degraded"
    assert body["checks"]["redis"] == "error"
    assert body["checks"]["database"] == "ok"
