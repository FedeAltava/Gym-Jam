"""Opaque refresh token generation and hashing.

Refresh tokens are random opaque strings (NOT JWTs). Only the sha256 hash is
persisted, so a database leak does not expose usable tokens.
"""
from __future__ import annotations

import hashlib
import secrets


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
