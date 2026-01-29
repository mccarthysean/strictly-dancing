"""Rate limiting middleware using Redis sliding window algorithm."""

from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request, Response
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_rate_limit_config() -> tuple[int, int, int]:
    """Get rate limit configuration from settings.

    Returns:
        Tuple of (authenticated_limit, anonymous_limit, window_seconds).
    """
    settings = get_settings()
    return (
        settings.rate_limit_authenticated,
        settings.rate_limit_anonymous,
        settings.rate_limit_window_seconds,
    )


class RateLimitConfig:
    """Rate limit configuration values."""

    # Redis key prefix
    KEY_PREFIX: str = "rate_limit:"


class RateLimiter:
    """Redis-backed sliding window rate limiter.

    Uses a sorted set to track requests within a sliding time window.
    Each request is scored by its timestamp, and expired entries are
    removed before counting.

    Attributes:
        redis_url: Redis connection URL.
        authenticated_limit: Max requests per window for authenticated users.
        anonymous_limit: Max requests per window for anonymous users.
        window_seconds: Sliding window size in seconds.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        authenticated_limit: int | None = None,
        anonymous_limit: int | None = None,
        window_seconds: int | None = None,
    ) -> None:
        """Initialize rate limiter.

        Args:
            redis_url: Redis connection URL. Uses settings if not provided.
            authenticated_limit: Max requests per window for authenticated users.
            anonymous_limit: Max requests per window for anonymous users.
            window_seconds: Sliding window size in seconds.
        """
        self._redis_url = redis_url or get_settings().redis_url
        self._redis: Redis | None = None

        # Get defaults from config if not provided
        default_auth, default_anon, default_window = get_rate_limit_config()
        self.authenticated_limit = (
            authenticated_limit if authenticated_limit is not None else default_auth
        )
        self.anonymous_limit = (
            anonymous_limit if anonymous_limit is not None else default_anon
        )
        self.window_seconds = (
            window_seconds if window_seconds is not None else default_window
        )

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(
                self._redis_url,
                decode_responses=True,
            )
        return self._redis

    def _get_key(self, identifier: str) -> str:
        """Generate Redis key for rate limit tracking.

        Args:
            identifier: User ID for authenticated users or IP for anonymous.

        Returns:
            Redis key string.
        """
        return f"{RateLimitConfig.KEY_PREFIX}{identifier}"

    async def check_rate_limit(
        self,
        identifier: str,
        is_authenticated: bool,
    ) -> tuple[bool, int, int, int]:
        """Check if request is within rate limit.

        Uses a sliding window algorithm with Redis sorted sets:
        1. Remove entries older than the window
        2. Count current entries
        3. Add new entry if under limit
        4. Return result with rate limit headers info

        Args:
            identifier: User ID for authenticated users or IP for anonymous.
            is_authenticated: Whether the request is authenticated.

        Returns:
            Tuple of (allowed, limit, remaining, retry_after_seconds).
            - allowed: True if request is allowed, False if rate limited.
            - limit: The rate limit for this identifier.
            - remaining: Remaining requests in current window.
            - retry_after: Seconds until rate limit resets (0 if not limited).
        """
        redis = await self._get_redis()
        key = self._get_key(identifier)
        limit = self.authenticated_limit if is_authenticated else self.anonymous_limit
        now = time.time()
        window_start = now - self.window_seconds

        # Use pipeline for atomic operations
        pipe = redis.pipeline()

        # Remove entries older than the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Get current count
        pipe.zcard(key)

        # Execute pipeline
        results = await pipe.execute()
        current_count = results[1]

        # Check if we're at the limit
        if current_count >= limit:
            # Get the oldest entry to calculate retry-after
            oldest_entries = await redis.zrange(key, 0, 0, withscores=True)
            if oldest_entries:
                oldest_timestamp = oldest_entries[0][1]
                retry_after = max(
                    1, int(oldest_timestamp + self.window_seconds - now) + 1
                )
            else:
                retry_after = self.window_seconds

            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                is_authenticated=is_authenticated,
                limit=limit,
                current_count=current_count,
            )

            return False, limit, 0, retry_after

        # Add new entry with current timestamp as score
        # Use timestamp + counter to ensure uniqueness
        member = f"{now}:{current_count}"
        await redis.zadd(key, {member: now})

        # Set expiration on key to clean up eventually
        await redis.expire(key, self.window_seconds + 10)

        remaining = max(0, limit - current_count - 1)

        return True, limit, remaining, 0

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting.

    Applies different rate limits based on authentication status:
    - Authenticated users (valid Bearer token): 100 req/min
    - Anonymous users: 20 req/min

    Rate limit headers are included in all responses:
    - X-RateLimit-Limit: The rate limit for this request
    - X-RateLimit-Remaining: Remaining requests in current window
    - X-RateLimit-Reset: Timestamp when the rate limit resets

    When rate limited, returns 429 with Retry-After header.
    """

    def __init__(
        self,
        app: Callable,
        rate_limiter: RateLimiter | None = None,
        exclude_paths: list[str] | None = None,
    ) -> None:
        """Initialize rate limit middleware.

        Args:
            app: The ASGI application.
            rate_limiter: Custom rate limiter instance. Creates default if not provided.
            exclude_paths: Paths to exclude from rate limiting (e.g., /health).
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request.

        Handles forwarded headers for proxied requests.

        Args:
            request: The FastAPI request.

        Returns:
            Client IP address string.
        """
        # Check for forwarded headers (common with proxies/load balancers)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client
        if request.client:
            return request.client.host

        return "unknown"

    def _extract_user_id(self, request: Request) -> str | None:
        """Extract user ID from Authorization header.

        Attempts to decode the JWT token to get the user ID.
        Returns None if no valid token is present.

        Args:
            request: The FastAPI request.

        Returns:
            User ID string or None.
        """
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return None

        if not auth_header.lower().startswith("bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            from app.services.token import token_service

            payload = token_service.verify_token(token)
            if payload.token_type == "access":
                return payload.sub
        except (ValueError, Exception):
            # Invalid or expired token - treat as anonymous
            pass

        return None

    def _should_exclude(self, path: str) -> bool:
        """Check if path should be excluded from rate limiting.

        Args:
            path: The request path.

        Returns:
            True if path should be excluded.
        """
        return any(path.startswith(excluded) for excluded in self.exclude_paths)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with rate limiting.

        Args:
            request: The incoming request.
            call_next: The next middleware/handler.

        Returns:
            The response, or 429 if rate limited.
        """
        # Skip rate limiting for excluded paths
        if self._should_exclude(request.url.path):
            return await call_next(request)

        # Determine identifier and authentication status
        user_id = self._extract_user_id(request)
        is_authenticated = user_id is not None

        # Use user ID for authenticated, IP for anonymous
        identifier = user_id if is_authenticated else self._get_client_ip(request)

        # Check rate limit
        try:
            (
                allowed,
                limit,
                remaining,
                retry_after,
            ) = await self.rate_limiter.check_rate_limit(identifier, is_authenticated)
        except Exception as e:
            # If Redis is unavailable, allow the request but log warning
            logger.warning(
                "rate_limit_redis_error",
                error=str(e),
                identifier=identifier,
            )
            return await call_next(request)

        if not allowed:
            # Rate limited - return 429
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too Many Requests",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time()) + self.rate_limiter.window_seconds
        )

        return response


# Default rate limiter instance
rate_limiter = RateLimiter()
