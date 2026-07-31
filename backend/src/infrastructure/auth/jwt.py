from __future__ import annotations
from datetime import datetime, timedelta, UTC
import jwt
from fastapi import HTTPException, status
from backend.src.infrastructure.config import settings


def create_access_token(
    user_id: str,
    expires_delta: timedelta | None = None,
    password_changed_at: datetime | None = None,
) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload: dict[str, object] = {"sub": user_id, "exp": expire}
    if password_changed_at is not None:
        # Store as a UTC ISO string so it round-trips without float precision
        # loss (JWT "iat"/"exp" use int seconds, but we need sub-second
        # fidelity here to match datetime comparisons).
        payload["pca"] = password_changed_at.isoformat()
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def decode_access_token_payload(token: str) -> dict[str, object]:
    """Return the full decoded payload; raises HTTP 401 on any failure."""
    try:
        payload: dict[str, object] = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("sub") is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
