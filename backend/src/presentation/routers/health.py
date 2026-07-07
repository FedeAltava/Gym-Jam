import asyncio
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.src.infrastructure.config import settings
from backend.src.infrastructure.database import engine

logger = logging.getLogger(__name__)
router = APIRouter()

_PROBE_TIMEOUT = 2.0


async def _check_database() -> bool:
    try:
        async with asyncio.timeout(_PROBE_TIMEOUT):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Health check: database probe failed")
        return False


async def _check_redis() -> bool:
    client = aioredis.from_url(settings.redis_url)
    try:
        async with asyncio.timeout(_PROBE_TIMEOUT):
            await client.ping()
        return True
    except Exception:
        logger.exception("Health check: redis probe failed")
        return False
    finally:
        await client.aclose()


@router.get("/health")
async def health() -> JSONResponse:
    if settings.redis_url:
        db_ok, redis_ok = await asyncio.gather(_check_database(), _check_redis())
        redis_status = "ok" if redis_ok else "error"
        healthy = db_ok and redis_ok
    else:
        db_ok = await _check_database()
        redis_status = "disabled"
        healthy = db_ok

    body = {
        "status": "ok" if healthy else "degraded",
        "checks": {
            "database": "ok" if db_ok else "error",
            "redis": redis_status,
        },
    }
    return JSONResponse(
        content=body,
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
