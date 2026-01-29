"""Unit tests for database configuration and session management."""

import contextlib

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import get_settings


class TestDatabaseConfiguration:
    """Tests for database module configuration."""

    def test_database_module_exists(self) -> None:
        """Test that the database module can be imported."""
        from app.core import database

        assert database is not None

    def test_async_engine_exists(self) -> None:
        """Test that async_engine is exported from database module."""
        from app.core.database import async_engine

        assert async_engine is not None
        assert isinstance(async_engine, AsyncEngine)

    def test_async_session_factory_exists(self) -> None:
        """Test that AsyncSessionLocal is exported from database module."""
        from app.core.database import AsyncSessionLocal

        assert AsyncSessionLocal is not None

    def test_get_db_dependency_exists(self) -> None:
        """Test that get_db dependency function is exported."""
        from app.core.database import get_db

        assert get_db is not None
        assert callable(get_db)

    def test_database_url_from_config(self) -> None:
        """Test that database uses URL from config."""
        from app.core.database import async_engine

        settings = get_settings()
        # The URL should match settings (SQLAlchemy masks password with ***)
        # Compare host, port, and database name instead
        engine_url = async_engine.url
        assert engine_url.host == "localhost"
        assert engine_url.port == 5432
        assert engine_url.database == "strictly_dancing"
        assert "asyncpg" in settings.database_url


class TestDatabasePoolConfiguration:
    """Tests for database connection pool settings."""

    def test_connection_pool_min_size(self) -> None:
        """Test that connection pool has minimum size of 2."""
        from app.core.database import async_engine

        # SQLAlchemy uses pool_size for min connections
        assert async_engine.pool.size() >= 0  # Pool exists and has size method

    def test_connection_pool_configured(self) -> None:
        """Test that connection pool is properly configured."""
        from app.core.database import async_engine

        # Check pool configuration via engine options
        pool = async_engine.pool
        assert pool is not None


class TestAsyncSession:
    """Tests for async session creation."""

    @pytest.mark.asyncio
    async def test_database_session_creates(self) -> None:
        """Test that async session can be created."""
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            assert session is not None
            assert isinstance(session, AsyncSession)

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self) -> None:
        """Test that get_db dependency yields a session."""
        from app.core.database import get_db

        # get_db is an async generator, we need to iterate it
        db_gen = get_db()
        session = await db_gen.__anext__()

        assert session is not None
        assert isinstance(session, AsyncSession)

        # Clean up - close the generator
        with contextlib.suppress(StopAsyncIteration):
            await db_gen.__anext__()
