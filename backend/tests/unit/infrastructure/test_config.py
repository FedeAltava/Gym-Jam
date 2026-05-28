"""Tests for Settings config — TDD RED/GREEN."""
from backend.src.infrastructure.config import Settings


def test_settings_has_secret_key_default() -> None:
    s = Settings()
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
