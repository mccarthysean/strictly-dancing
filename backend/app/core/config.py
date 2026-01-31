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
        # Production URLs
        "https://strictly-dancing.vercel.app",
        "https://strictly-dancing-*.vercel.app",  # Preview deployments
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

    # Task/Cron settings
    task_secret_key: str = ""  # Secret for authenticating task endpoints

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "console"

    # Sentry settings
    sentry_dsn: str = ""  # Leave empty to disable Sentry
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1  # 10% of transactions for performance
    sentry_profiles_sample_rate: float = 0.1  # 10% for profiling

    # Email settings (SendGrid)
    sendgrid_api_key: str = ""  # Leave empty to use console logging
    email_from_address: str = "noreply@strictlydancing.com"
    email_from_name: str = "Strictly Dancing"

    # Rate limiting settings
    rate_limit_authenticated: int = 100  # requests per minute for authenticated users
    rate_limit_anonymous: int = 20  # requests per minute for anonymous users
    rate_limit_window_seconds: int = 60  # sliding window size

    # S3 Storage settings
    s3_bucket_name: str = ""  # Leave empty to use local file storage
    s3_region: str = "us-west-2"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_endpoint_url: str = ""  # For Supabase Storage or MinIO compatibility
    storage_base_url: str = ""  # Base URL for accessing stored files (CDN or S3)

    # Avatar settings
    avatar_max_size_bytes: int = 5 * 1024 * 1024  # 5MB
    avatar_allowed_types: list[str] = ["image/jpeg", "image/png", "image/webp"]
    avatar_resize_width: int = 400  # Resize avatar to this width (preserving aspect)
    avatar_resize_height: int = 400  # Max height for avatar
    avatar_thumbnail_size: int = 100  # Thumbnail size (square)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
