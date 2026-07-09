from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_SENTINEL_SECRET = "dev-secret-key-change-in-production"
# Known placeholder values that must never be accepted in production,
# regardless of their length (.env.example ships the second one).
_INSECURE_SECRETS = frozenset(
    {
        _SENTINEL_SECRET,
        "change_me_in_production_use_openssl_rand_hex_32",
    }
)
_MIN_SECRET_LEN = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./gym_jam.db"
    secret_key: str = _SENTINEL_SECRET
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    # Grace window during which reuse of a rotation-revoked refresh token is
    # treated as a benign concurrent refresh (multi-tab race), not theft.
    refresh_token_reuse_grace_seconds: int = 60
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    environment: str = "development"
    # Redis connection URL for the shared rate limiter. Empty means "not
    # configured": the app falls back to the in-memory limiter (tests, dev).
    redis_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@gymjam.app"
    app_base_url: str = "http://localhost:5173"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment != "production":
            return self
        if self.secret_key in _INSECURE_SECRETS or len(self.secret_key) < _MIN_SECRET_LEN:
            raise ValueError(
                "SECRET_KEY must be set to a secure value (>= 32 chars) in production. "
                "Generate one with: openssl rand -hex 32"
            )
        if "sqlite" in self.database_url.lower():
            raise ValueError(
                "DATABASE_URL must not use SQLite in production. "
                "Configure a PostgreSQL connection string."
            )
        import warnings
        if not self.redis_url:
            warnings.warn(
                "REDIS_URL is not set in production: rate limiting is per-process only.",
                stacklevel=2,
            )
        if not self.smtp_host:
            warnings.warn(
                "SMTP_HOST is not set in production: password reset emails will fail silently.",
                stacklevel=2,
            )
        return self


settings = Settings()
