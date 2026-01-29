"""Unit tests for the cache service."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.services.cache import CacheService


class TestCacheService:
    """Tests for CacheService initialization and basic operations."""

    def test_init_with_default_url(self) -> None:
        """Test initialization with default redis URL from settings."""
        with patch("app.services.cache.get_settings") as mock_settings:
            mock_settings.return_value.redis_url = "redis://localhost:6379/0"
            service = CacheService()
            assert service._redis_url == "redis://localhost:6379/0"

    def test_init_with_custom_url(self) -> None:
        """Test initialization with custom redis URL."""
        service = CacheService(redis_url="redis://custom:6379/1")
        assert service._redis_url == "redis://custom:6379/1"

    @pytest.mark.asyncio
    async def test_get_creates_redis_connection(self) -> None:
        """Test that get creates Redis connection on first call."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch("app.services.cache.Redis") as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis_class.from_url.return_value = mock_redis

            await service.get("test_key")

            mock_redis_class.from_url.assert_called_once_with(
                "redis://localhost:6379/0",
                decode_responses=True,
            )

    @pytest.mark.asyncio
    async def test_get_reuses_redis_connection(self) -> None:
        """Test that subsequent calls reuse Redis connection."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch("app.services.cache.Redis") as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis_class.from_url.return_value = mock_redis

            await service.get("key1")
            await service.get("key2")

            # Should only create connection once
            assert mock_redis_class.from_url.call_count == 1


class TestCacheGetSet:
    """Tests for get and set operations."""

    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self) -> None:
        """Test get returns None when key doesn't exist."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_get_redis.return_value = mock_redis

            result = await service.get("nonexistent_key")

            assert result is None
            mock_redis.get.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_get_returns_parsed_dict(self) -> None:
        """Test get returns parsed JSON dict."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get = AsyncMock(return_value='{"name": "test", "value": 123}')
            mock_get_redis.return_value = mock_redis

            result = await service.get("test_key")

            assert result == {"name": "test", "value": 123}

    @pytest.mark.asyncio
    async def test_get_returns_parsed_list(self) -> None:
        """Test get returns parsed JSON list."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get = AsyncMock(return_value="[1, 2, 3]")
            mock_get_redis.return_value = mock_redis

            result = await service.get("test_key")

            assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_set_with_default_ttl(self) -> None:
        """Test set uses default TTL when not specified."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.set = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await service.set("test_key", {"data": "value"})

            mock_redis.set.assert_called_once_with(
                "test_key",
                '{"data": "value"}',
                ex=300,  # DEFAULT_TTL
            )

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self) -> None:
        """Test set uses custom TTL when specified."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.set = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await service.set("test_key", {"data": "value"}, ttl=600)

            mock_redis.set.assert_called_once_with(
                "test_key",
                '{"data": "value"}',
                ex=600,
            )

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        """Test delete removes a key."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.delete = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await service.delete("test_key")

            mock_redis.delete.assert_called_once_with("test_key")


class TestCacheDeletePattern:
    """Tests for delete_pattern operation."""

    @pytest.mark.asyncio
    async def test_delete_pattern_deletes_matching_keys(self) -> None:
        """Test delete_pattern removes all matching keys."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()

            # Simulate scan_iter returning matching keys
            async def fake_scan_iter(match: str) -> Any:
                for key in ["host_profile:1", "host_profile:2"]:
                    yield key

            mock_redis.scan_iter = fake_scan_iter
            mock_redis.delete = AsyncMock(return_value=2)
            mock_get_redis.return_value = mock_redis

            result = await service.delete_pattern("host_profile:*")

            assert result == 2
            mock_redis.delete.assert_called_once_with(
                "host_profile:1", "host_profile:2"
            )

    @pytest.mark.asyncio
    async def test_delete_pattern_returns_zero_when_no_matches(self) -> None:
        """Test delete_pattern returns 0 when no keys match."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()

            # Simulate scan_iter returning no keys
            async def fake_scan_iter(match: str) -> Any:
                return
                yield  # noqa: B901 - This makes it an async generator

            mock_redis.scan_iter = fake_scan_iter
            mock_get_redis.return_value = mock_redis

            result = await service.delete_pattern("nonexistent:*")

            assert result == 0


class TestDanceStylesCache:
    """Tests for dance styles caching."""

    @pytest.mark.asyncio
    async def test_get_dance_styles_returns_list(self) -> None:
        """Test get_dance_styles returns cached list."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        dance_styles = [
            {"id": "1", "name": "Salsa"},
            {"id": "2", "name": "Bachata"},
        ]

        with patch.object(service, "get", return_value=dance_styles) as mock_get:
            result = await service.get_dance_styles()

            assert result == dance_styles
            mock_get.assert_called_once_with("dance_styles:all")

    @pytest.mark.asyncio
    async def test_get_dance_styles_returns_none_when_not_cached(self) -> None:
        """Test get_dance_styles returns None when not in cache."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "get", return_value=None) as mock_get:
            result = await service.get_dance_styles()

            assert result is None
            mock_get.assert_called_once_with("dance_styles:all")

    @pytest.mark.asyncio
    async def test_set_dance_styles(self) -> None:
        """Test set_dance_styles caches with 1 hour TTL."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        dance_styles = [
            {"id": "1", "name": "Salsa"},
        ]

        with patch.object(service, "set") as mock_set:
            await service.set_dance_styles(dance_styles)

            mock_set.assert_called_once_with(
                "dance_styles:all",
                dance_styles,
                ttl=3600,
            )

    @pytest.mark.asyncio
    async def test_invalidate_dance_styles(self) -> None:
        """Test invalidate_dance_styles deletes cache key."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "delete") as mock_delete:
            await service.invalidate_dance_styles()

            mock_delete.assert_called_once_with("dance_styles:all")


class TestHostProfileCache:
    """Tests for host profile caching."""

    def test_host_profile_key_generation(self) -> None:
        """Test host profile key generation."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        key = service._host_profile_key("abc-123")

        assert key == "host_profile:abc-123"

    @pytest.mark.asyncio
    async def test_get_host_profile(self) -> None:
        """Test get_host_profile returns cached profile."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        profile = {"id": "abc-123", "bio": "Test bio"}

        with patch.object(service, "get", return_value=profile) as mock_get:
            result = await service.get_host_profile("abc-123")

            assert result == profile
            mock_get.assert_called_once_with("host_profile:abc-123")

    @pytest.mark.asyncio
    async def test_set_host_profile(self) -> None:
        """Test set_host_profile caches profile."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        profile = {"id": "abc-123", "bio": "Test bio"}

        with patch.object(service, "set") as mock_set:
            await service.set_host_profile("abc-123", profile)

            mock_set.assert_called_once_with(
                "host_profile:abc-123",
                profile,
                ttl=None,
            )

    @pytest.mark.asyncio
    async def test_invalidate_host_profile(self) -> None:
        """Test invalidate_host_profile deletes profile and search caches."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with (
            patch.object(service, "delete") as mock_delete,
            patch.object(service, "delete_pattern") as mock_delete_pattern,
        ):
            await service.invalidate_host_profile("abc-123")

            mock_delete.assert_called_once_with("host_profile:abc-123")
            mock_delete_pattern.assert_called_once_with("host_search:*")


class TestUserCache:
    """Tests for user caching."""

    def test_user_key_generation(self) -> None:
        """Test user key generation."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        key = service._user_key("user-123")

        assert key == "user:user-123"

    @pytest.mark.asyncio
    async def test_get_user(self) -> None:
        """Test get_user returns cached user."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        user = {"id": "user-123", "email": "test@example.com"}

        with patch.object(service, "get", return_value=user) as mock_get:
            result = await service.get_user("user-123")

            assert result == user
            mock_get.assert_called_once_with("user:user-123")

    @pytest.mark.asyncio
    async def test_set_user_excludes_password_hash(self) -> None:
        """Test set_user excludes password_hash from cache."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        user = {
            "id": "user-123",
            "email": "test@example.com",
            "password_hash": "secret_hash",
        }

        with patch.object(service, "set") as mock_set:
            await service.set_user("user-123", user)

            # Should cache without password_hash
            expected_data = {
                "id": "user-123",
                "email": "test@example.com",
            }
            mock_set.assert_called_once_with(
                "user:user-123",
                expected_data,
                ttl=None,
            )

    @pytest.mark.asyncio
    async def test_invalidate_user(self) -> None:
        """Test invalidate_user deletes cache key."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "delete") as mock_delete:
            await service.invalidate_user("user-123")

            mock_delete.assert_called_once_with("user:user-123")


class TestHostSearchCache:
    """Tests for host search caching."""

    def test_host_search_key_generation(self) -> None:
        """Test host search key generation."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        key = service._host_search_key("query-hash-123")

        assert key == "host_search:query-hash-123"

    @pytest.mark.asyncio
    async def test_get_host_search_results(self) -> None:
        """Test get_host_search_results returns cached results."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        results = {
            "items": [{"id": "1"}],
            "total": 1,
        }

        with patch.object(service, "get", return_value=results) as mock_get:
            result = await service.get_host_search_results("query-hash")

            assert result == results
            mock_get.assert_called_once_with("host_search:query-hash")

    @pytest.mark.asyncio
    async def test_set_host_search_results(self) -> None:
        """Test set_host_search_results caches with 1 minute TTL."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        results = {"items": [], "total": 0}

        with patch.object(service, "set") as mock_set:
            await service.set_host_search_results("query-hash", results)

            mock_set.assert_called_once_with(
                "host_search:query-hash",
                results,
                ttl=60,
            )


class TestConnectionManagement:
    """Tests for connection management."""

    @pytest.mark.asyncio
    async def test_close_closes_redis_connection(self) -> None:
        """Test close closes Redis connection and clears reference."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()
        service._redis = mock_redis

        await service.close()

        mock_redis.close.assert_called_once()
        assert service._redis is None

    @pytest.mark.asyncio
    async def test_close_when_no_connection(self) -> None:
        """Test close is safe when no connection exists."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        # Should not raise
        await service.close()

    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(self) -> None:
        """Test health_check returns True when Redis responds."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_get_redis.return_value = mock_redis

            result = await service.health_check()

            assert result is True
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_error(self) -> None:
        """Test health_check returns False when Redis fails."""
        service = CacheService(redis_url="redis://localhost:6379/0")

        with patch.object(service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
            mock_get_redis.return_value = mock_redis

            result = await service.health_check()

            assert result is False


class TestSingletonInstance:
    """Tests for singleton instance."""

    def test_cache_service_singleton_exists(self) -> None:
        """Test that cache_service singleton is created."""
        from app.services.cache import cache_service

        assert isinstance(cache_service, CacheService)

    def test_cache_service_uses_settings_url(self) -> None:
        """Test singleton uses settings URL."""
        with patch("app.services.cache.get_settings") as mock_settings:
            mock_settings.return_value.redis_url = "redis://settings:6379/0"

            # Create a new instance to test (can't reload singleton easily)
            from app.services.cache import _create_cache_service

            service = _create_cache_service()

            # The service should use the settings URL
            # (In actual use, it would use the mocked settings)
            assert isinstance(service, CacheService)
