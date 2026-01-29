"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application settings
    app_name: str = "Strictly Dancing API"
    app_version: str = "0.1.0"
    debug: bool = False

    # API settings
    api_v1_prefix: str = "/api/v1"

    # Database settings
    database_url: str = (
        "postgresql+asyncpg://user:password@localhost:5432/strictly_dancing"
    )

    # CORS settings
    cors_origins: list[str] = [
        "http://localhost:5175",  # PWA development
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:5175",
        "http://127.0.0.1:3000",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # JWT settings
    jwt_secret_key: str = "development-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"

    # Stripe settings
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "console"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
