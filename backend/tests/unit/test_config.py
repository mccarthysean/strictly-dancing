"""Tests for configuration module."""

import os
from unittest.mock import patch


def test_config_loads_from_environment():
    """Test that configuration loads from environment variables."""
    # Clear the cached settings to allow fresh load
    from app.core.config import Settings, get_settings

    get_settings.cache_clear()

    with patch.dict(
        os.environ,
        {
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "DATABASE_URL": "postgresql+asyncpg://test:test@testhost:5432/testdb",
        },
    ):
        settings = Settings()

        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert (
            settings.database_url
            == "postgresql+asyncpg://test:test@testhost:5432/testdb"
        )

    # Clear cache after test
    get_settings.cache_clear()


def test_config_has_required_fields():
    """Test that configuration has all required fields."""
    from app.core.config import Settings, get_settings

    get_settings.cache_clear()
    settings = Settings()

    # Application settings
    assert hasattr(settings, "app_name")
    assert hasattr(settings, "app_version")
    assert hasattr(settings, "debug")
    assert hasattr(settings, "api_v1_prefix")

    # Database settings
    assert hasattr(settings, "database_url")

    # CORS settings
    assert hasattr(settings, "cors_origins")
    assert hasattr(settings, "cors_allow_credentials")
    assert hasattr(settings, "cors_allow_methods")
    assert hasattr(settings, "cors_allow_headers")

    # JWT settings
    assert hasattr(settings, "jwt_secret_key")
    assert hasattr(settings, "jwt_algorithm")
    assert hasattr(settings, "jwt_access_token_expire_minutes")
    assert hasattr(settings, "jwt_refresh_token_expire_days")

    # Redis settings
    assert hasattr(settings, "redis_url")

    # Stripe settings
    assert hasattr(settings, "stripe_secret_key")
    assert hasattr(settings, "stripe_webhook_secret")

    # Logging settings
    assert hasattr(settings, "log_level")
    assert hasattr(settings, "log_format")

    get_settings.cache_clear()


def test_config_default_values():
    """Test that configuration has sensible default values."""
    from app.core.config import Settings, get_settings

    get_settings.cache_clear()
    settings = Settings()

    # Check default values
    assert settings.app_name == "Strictly Dancing API"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.jwt_access_token_expire_minutes == 15
    assert settings.jwt_refresh_token_expire_days == 7
    assert settings.log_level == "INFO"
    assert settings.log_format == "json"

    get_settings.cache_clear()


def test_config_cors_origins_default():
    """Test that CORS origins include localhost for development."""
    from app.core.config import Settings, get_settings

    get_settings.cache_clear()
    settings = Settings()

    assert "http://localhost:5175" in settings.cors_origins
    assert settings.cors_allow_credentials is True
    assert "*" in settings.cors_allow_methods
    assert "*" in settings.cors_allow_headers

    get_settings.cache_clear()


def test_get_settings_is_cached():
    """Test that get_settings returns a cached instance."""
    from app.core.config import get_settings

    get_settings.cache_clear()
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2

    get_settings.cache_clear()
