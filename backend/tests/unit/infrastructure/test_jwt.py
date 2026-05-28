"""Tests for JWT utilities — RED phase first."""
import pytest
from datetime import timedelta
import jwt as pyjwt
from fastapi import HTTPException

from backend.src.infrastructure.auth.jwt import create_access_token, decode_access_token
from backend.src.infrastructure.config import settings


def test_create_access_token_returns_string() -> None:
    token = create_access_token(user_id="user-123")
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_payload_contains_sub() -> None:
    token = create_access_token(user_id="user-abc")
    payload = pyjwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == "user-abc"


def test_create_access_token_payload_contains_exp() -> None:
    token = create_access_token(user_id="user-abc")
    payload = pyjwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert "exp" in payload


def test_create_access_token_payload_no_email() -> None:
    token = create_access_token(user_id="user-abc")
    payload = pyjwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert "email" not in payload


def test_decode_access_token_returns_user_id() -> None:
    token = create_access_token(user_id="user-xyz")
    user_id = decode_access_token(token)
    assert user_id == "user-xyz"


def test_decode_access_token_different_user_id() -> None:
    token = create_access_token(user_id="another-user")
    user_id = decode_access_token(token)
    assert user_id == "another-user"


def test_decode_expired_token_raises_401() -> None:
    token = create_access_token(user_id="user-123", expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token)
    assert exc_info.value.status_code == 401


def test_decode_invalid_token_raises_401() -> None:
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not.a.valid.token")
    assert exc_info.value.status_code == 401
