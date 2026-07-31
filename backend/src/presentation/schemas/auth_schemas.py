from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

_BCRYPT_MAX_BYTES = 72


def _validate_password_complexity(value: str) -> str:
    """Shared validator: enforces complexity + bcrypt byte limit."""
    if not any(c.isupper() for c in value):
        raise ValueError(
            "Password must contain at least one uppercase letter and one digit"
        )
    if not any(c.isdigit() for c in value):
        raise ValueError(
            "Password must contain at least one uppercase letter and one digit"
        )
    if len(value.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        raise ValueError(
            f"Password must be at most {_BCRYPT_MAX_BYTES} bytes when UTF-8 encoded "
            "(bcrypt limit); note that non-ASCII characters use multiple bytes."
        )
    return value


def _normalize_email(value: str) -> str:
    """Shared validator: normalize email to lowercase and strip whitespace."""
    return value.lower().strip()


class RegisterRequest(BaseModel):
    email: EmailStr
    # bcrypt silently truncates at 72 BYTES (not characters) — enforce the
    # UTF-8 encoded byte length as the upper bound via the validator below.
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, value: str) -> str:
        return _validate_password_complexity(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    rest_seconds: int
    units: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def new_password_complexity(cls, value: str) -> str:
        return _validate_password_complexity(value)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def new_password_complexity(cls, value: str) -> str:
        return _validate_password_complexity(value)
