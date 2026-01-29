"""Redis caching service for hot data."""

from __future__ import annotations

import json
from typing import Any, TypeVar

from redis.asyncio import Redis

from app.core.config import get_settings

T = TypeVar("T")


class CacheService:
    """Redis caching service for frequently accessed data.

    Provides caching for hot data to reduce database load and improve
    API response times. Uses Redis with automatic expiration.

    Cache keys follow the pattern: {entity_type}:{id}

    Attributes:
        DEFAULT_TTL: Default time-to-live in seconds (5 minutes)
        DANCE_STYLES_KEY: Cache key for all dance styles list
        HOST_PROFILE_PREFIX: Prefix for host profile cache keys
        USER_PREFIX: Prefix for user cache keys
    """

    DEFAULT_TTL: int = 300  # 5 minutes
    DANCE_STYLES_KEY: str = "dance_styles:all"
    HOST_PROFILE_PREFIX: str = "host_profile:"
    USER_PREFIX: str = "user:"
    HOST_SEARCH_PREFIX: str = "host_search:"

    def __init__(self, redis_url: str | None = None) -> None:
        """Initialize cache service.

        Args:
            redis_url: Redis connection URL. Uses settings if not provided.
        """
        self._redis_url = redis_url or get_settings().redis_url
        self._redis: Redis | None = None

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(
                self._redis_url,
                decode_responses=True,
            )
        return self._redis

    async def get(self, key: str) -> dict[str, Any] | list[Any] | None:
        """Get a value from cache.

        Args:
            key: The cache key.

        Returns:
            The cached value (dict or list), or None if not found.
        """
        redis = await self._get_redis()
        value = await redis.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(
        self,
        key: str,
        value: dict[str, Any] | list[Any],
        ttl: int | None = None,
    ) -> None:
        """Set a value in cache.

        Args:
            key: The cache key.
            value: The value to cache (must be JSON-serializable).
            ttl: Time-to-live in seconds. Uses DEFAULT_TTL if not provided.
        """
        redis = await self._get_redis()
        ttl = ttl if ttl is not None else self.DEFAULT_TTL
        await redis.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        """Delete a value from cache.

        Args:
            key: The cache key to delete.
        """
        redis = await self._get_redis()
        await redis.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Args:
            pattern: The pattern to match (e.g., "host_profile:*").

        Returns:
            Number of keys deleted.
        """
        redis = await self._get_redis()
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await redis.delete(*keys)
        return 0

    # ===== Dance Styles Cache =====

    async def get_dance_styles(self) -> list[dict[str, Any]] | None:
        """Get all dance styles from cache.

        Returns:
            List of dance style dicts, or None if not cached.
        """
        result = await self.get(self.DANCE_STYLES_KEY)
        if result is None:
            return None
        return result if isinstance(result, list) else None

    async def set_dance_styles(
        self,
        dance_styles: list[dict[str, Any]],
        ttl: int = 3600,  # 1 hour - dance styles rarely change
    ) -> None:
        """Cache all dance styles.

        Args:
            dance_styles: List of dance style dicts to cache.
            ttl: Time-to-live in seconds (default 1 hour).
        """
        await self.set(self.DANCE_STYLES_KEY, dance_styles, ttl=ttl)

    async def invalidate_dance_styles(self) -> None:
        """Invalidate dance styles cache."""
        await self.delete(self.DANCE_STYLES_KEY)

    # ===== Host Profile Cache =====

    def _host_profile_key(self, profile_id: str) -> str:
        """Generate cache key for a host profile."""
        return f"{self.HOST_PROFILE_PREFIX}{profile_id}"

    async def get_host_profile(self, profile_id: str) -> dict[str, Any] | None:
        """Get a host profile from cache.

        Args:
            profile_id: The host profile UUID.

        Returns:
            Host profile dict, or None if not cached.
        """
        result = await self.get(self._host_profile_key(profile_id))
        if result is None:
            return None
        return result if isinstance(result, dict) else None

    async def set_host_profile(
        self,
        profile_id: str,
        profile_data: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Cache a host profile.

        Args:
            profile_id: The host profile UUID.
            profile_data: The profile data to cache.
            ttl: Time-to-live in seconds.
        """
        await self.set(self._host_profile_key(profile_id), profile_data, ttl=ttl)

    async def invalidate_host_profile(self, profile_id: str) -> None:
        """Invalidate a host profile cache entry.

        Args:
            profile_id: The host profile UUID to invalidate.
        """
        await self.delete(self._host_profile_key(profile_id))
        # Also invalidate any search results that might include this profile
        await self.delete_pattern(f"{self.HOST_SEARCH_PREFIX}*")

    # ===== User Cache =====

    def _user_key(self, user_id: str) -> str:
        """Generate cache key for a user."""
        return f"{self.USER_PREFIX}{user_id}"

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Get a user from cache.

        Args:
            user_id: The user UUID.

        Returns:
            User dict (without sensitive fields), or None if not cached.
        """
        result = await self.get(self._user_key(user_id))
        if result is None:
            return None
        return result if isinstance(result, dict) else None

    async def set_user(
        self,
        user_id: str,
        user_data: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Cache a user (without sensitive fields).

        Args:
            user_id: The user UUID.
            user_data: The user data to cache (should exclude password_hash).
            ttl: Time-to-live in seconds.
        """
        # Ensure password_hash is never cached
        safe_data = {k: v for k, v in user_data.items() if k != "password_hash"}
        await self.set(self._user_key(user_id), safe_data, ttl=ttl)

    async def invalidate_user(self, user_id: str) -> None:
        """Invalidate a user cache entry.

        Args:
            user_id: The user UUID to invalidate.
        """
        await self.delete(self._user_key(user_id))

    # ===== Host Search Cache =====

    def _host_search_key(self, query_hash: str) -> str:
        """Generate cache key for a host search query."""
        return f"{self.HOST_SEARCH_PREFIX}{query_hash}"

    async def get_host_search_results(
        self,
        query_hash: str,
    ) -> dict[str, Any] | None:
        """Get cached host search results.

        Args:
            query_hash: Hash of the search query parameters.

        Returns:
            Search results dict, or None if not cached.
        """
        result = await self.get(self._host_search_key(query_hash))
        if result is None:
            return None
        return result if isinstance(result, dict) else None

    async def set_host_search_results(
        self,
        query_hash: str,
        results: dict[str, Any],
        ttl: int = 60,  # 1 minute - search results change frequently
    ) -> None:
        """Cache host search results.

        Args:
            query_hash: Hash of the search query parameters.
            results: The search results to cache.
            ttl: Time-to-live in seconds (default 1 minute).
        """
        await self.set(self._host_search_key(query_hash), results, ttl=ttl)

    # ===== Connection Management =====

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    async def health_check(self) -> bool:
        """Check if Redis is available.

        Returns:
            True if Redis is responsive, False otherwise.
        """
        try:
            redis = await self._get_redis()
            await redis.ping()
            return True
        except Exception:
            return False


def _create_cache_service() -> CacheService:
    """Create cache service from application settings."""
    return CacheService()


# Singleton instance for use across the application
cache_service = _create_cache_service()
