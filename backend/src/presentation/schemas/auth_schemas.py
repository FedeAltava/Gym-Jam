from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

_BCRYPT_MAX_BYTES = 72


class RegisterRequest(BaseModel):
    email: EmailStr
    # bcrypt silently truncates at 72 BYTES (not characters) — enforce the
    # UTF-8 encoded byte length as the upper bound via the validator below.
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def password_within_bcrypt_byte_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > _BCRYPT_MAX_BYTES:
            raise ValueError(
                f"Password must be at most {_BCRYPT_MAX_BYTES} bytes when UTF-8 encoded "
                "(bcrypt limit); note that non-ASCII characters use multiple bytes."
            )
        return value


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
