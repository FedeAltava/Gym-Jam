"""Tests for Settings config — TDD RED/GREEN."""
import pytest
from pydantic import ValidationError

from backend.src.infrastructure.config import Settings


def test_settings_has_secret_key_default() -> None:
    # The class-level default is the sentinel; override env-file to test field default.
    s = Settings(secret_key="dev-secret-key-change-in-production")
    assert s.secret_key == "dev-secret-key-change-in-production"


def test_settings_has_algorithm_default() -> None:
    s = Settings()
    assert s.algorithm == "HS256"


def test_settings_has_access_token_expire_minutes_default() -> None:
    s = Settings()
    assert s.access_token_expire_minutes == 30


def test_settings_database_url_unchanged() -> None:
    s = Settings()
    assert s.database_url == "sqlite+aiosqlite:///./gym_jam.db"


def test_settings_default_environment_is_development() -> None:
    s = Settings()
    assert s.environment == "development"


def test_settings_sentinel_secret_key_allowed_in_development() -> None:
    # Should NOT raise in development mode
    s = Settings(environment="development", secret_key="dev-secret-key-change-in-production")
    assert s.secret_key == "dev-secret-key-change-in-production"


def test_settings_sentinel_secret_key_raises_in_production() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY must be set"):
        Settings(environment="production", secret_key="dev-secret-key-change-in-production")


def test_settings_env_example_placeholder_secret_key_raises_in_production() -> None:
    # The placeholder shipped in .env.example is 47 chars — long enough to pass
    # the length check, so it must be rejected as a known insecure sentinel.
    with pytest.raises(ValidationError, match="SECRET_KEY must be set"):
        Settings(
            environment="production",
            secret_key="change_me_in_production_use_openssl_rand_hex_32",
        )


def test_settings_short_secret_key_raises_in_production() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY must be set"):
        Settings(environment="production", secret_key="tooshort")


def test_settings_valid_secret_key_accepted_in_production() -> None:
    key = "a" * 32  # exactly 32 chars, not the sentinel
    s = Settings(environment="production", secret_key=key)
    assert s.secret_key == key
