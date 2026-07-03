"""Tests for opaque refresh token generation and hashing."""
import hashlib

from backend.src.infrastructure.auth.refresh_tokens import (
    generate_refresh_token,
    hash_refresh_token,
)


def test_generate_refresh_token_is_long_urlsafe_string():
    token = generate_refresh_token()
    assert isinstance(token, str)
    # token_urlsafe(48) yields 64 base64url characters
    assert len(token) >= 48


def test_generate_refresh_token_is_unique():
    tokens = {generate_refresh_token() for _ in range(100)}
    assert len(tokens) == 100


def test_hash_refresh_token_is_sha256_hex():
    raw = "some-raw-token"
    hashed = hash_refresh_token(raw)
    assert hashed == hashlib.sha256(raw.encode()).hexdigest()
    assert len(hashed) == 64


def test_hash_refresh_token_is_deterministic():
    raw = generate_refresh_token()
    assert hash_refresh_token(raw) == hash_refresh_token(raw)


def test_hash_refresh_token_differs_per_input():
    assert hash_refresh_token("token-a") != hash_refresh_token("token-b")
