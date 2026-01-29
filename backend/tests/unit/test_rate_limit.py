"""Unit tests for rate limiting middleware."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import (
    RateLimitConfig,
    RateLimiter,
    RateLimitMiddleware,
    get_rate_limit_config,
)


class TestGetRateLimitConfig:
    """Tests for get_rate_limit_config function."""

    def test_returns_tuple_of_three_integers(self) -> None:
        """Config returns a tuple of three values."""
        result = get_rate_limit_config()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_returns_authenticated_limit(self) -> None:
        """Config returns authenticated limit."""
        auth_limit, _, _ = get_rate_limit_config()
        assert auth_limit == 100

    def test_returns_anonymous_limit(self) -> None:
        """Config returns anonymous limit."""
        _, anon_limit, _ = get_rate_limit_config()
        assert anon_limit == 20

    def test_returns_window_seconds(self) -> None:
        """Config returns window seconds."""
        _, _, window = get_rate_limit_config()
        assert window == 60


class TestRateLimitConfig:
    """Tests for RateLimitConfig class."""

    def test_key_prefix_is_rate_limit(self) -> None:
        """Key prefix is 'rate_limit:'."""
        assert RateLimitConfig.KEY_PREFIX == "rate_limit:"


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_init_with_defaults(self) -> None:
        """Initializes with default config values."""
        limiter = RateLimiter()
        assert limiter.authenticated_limit == 100
        assert limiter.anonymous_limit == 20
        assert limiter.window_seconds == 60

    def test_init_with_custom_values(self) -> None:
        """Initializes with custom values."""
        limiter = RateLimiter(
            authenticated_limit=50,
            anonymous_limit=10,
            window_seconds=30,
        )
        assert limiter.authenticated_limit == 50
        assert limiter.anonymous_limit == 10
        assert limiter.window_seconds == 30

    def test_init_with_custom_redis_url(self) -> None:
        """Initializes with custom Redis URL."""
        limiter = RateLimiter(redis_url="redis://custom:6379/0")
        assert limiter._redis_url == "redis://custom:6379/0"

    def test_get_key_generates_correct_key(self) -> None:
        """_get_key generates correct Redis key."""
        limiter = RateLimiter()
        key = limiter._get_key("user123")
        assert key == "rate_limit:user123"

    def test_get_key_with_ip_address(self) -> None:
        """_get_key works with IP addresses."""
        limiter = RateLimiter()
        key = limiter._get_key("192.168.1.1")
        assert key == "rate_limit:192.168.1.1"


def _create_mock_redis(count: int = 5) -> MagicMock:
    """Create a mock Redis client with proper pipeline setup.

    Args:
        count: The count to return from zcard (current requests in window).

    Returns:
        Mock Redis client.
    """
    # Use MagicMock for the redis object so pipeline() is sync
    mock_redis = MagicMock()

    # Pipeline is sync, but execute is async
    mock_pipe = MagicMock()
    mock_pipe.zremrangebyscore = MagicMock(return_value=mock_pipe)
    mock_pipe.zcard = MagicMock(return_value=mock_pipe)
    mock_pipe.execute = AsyncMock(return_value=[0, count])
    mock_redis.pipeline.return_value = mock_pipe

    # Async methods
    mock_redis.zadd = AsyncMock()
    mock_redis.expire = AsyncMock()
    mock_redis.zrange = AsyncMock(return_value=[])

    return mock_redis


class TestRateLimiterCheckRateLimit:
    """Tests for RateLimiter.check_rate_limit method."""

    @pytest.mark.asyncio
    async def test_allows_request_under_limit(self) -> None:
        """Allows request when under limit."""
        mock_redis = _create_mock_redis(count=5)
        limiter = RateLimiter()
        limiter._redis = mock_redis

        allowed, limit, remaining, retry_after = await limiter.check_rate_limit(
            "user123", is_authenticated=True
        )

        assert allowed is True
        assert limit == 100
        assert remaining == 94  # 100 - 5 - 1
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_blocks_request_at_limit_authenticated(self) -> None:
        """Blocks authenticated request when at limit."""
        mock_redis = _create_mock_redis(count=100)
        mock_redis.zrange = AsyncMock(return_value=[("entry", time.time() - 30)])
        limiter = RateLimiter()
        limiter._redis = mock_redis

        allowed, limit, remaining, retry_after = await limiter.check_rate_limit(
            "user123", is_authenticated=True
        )

        assert allowed is False
        assert limit == 100
        assert remaining == 0
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_blocks_request_at_limit_anonymous(self) -> None:
        """Blocks anonymous request when at limit (20)."""
        mock_redis = _create_mock_redis(count=20)
        mock_redis.zrange = AsyncMock(return_value=[("entry", time.time() - 30)])
        limiter = RateLimiter()
        limiter._redis = mock_redis

        allowed, limit, remaining, retry_after = await limiter.check_rate_limit(
            "192.168.1.1", is_authenticated=False
        )

        assert allowed is False
        assert limit == 20
        assert remaining == 0
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_uses_correct_limit_for_authenticated(self) -> None:
        """Uses 100 req/min limit for authenticated users."""
        mock_redis = _create_mock_redis(count=99)
        limiter = RateLimiter()
        limiter._redis = mock_redis

        allowed, limit, remaining, retry_after = await limiter.check_rate_limit(
            "user123", is_authenticated=True
        )

        assert allowed is True
        assert limit == 100
        assert remaining == 0  # 100 - 99 - 1

    @pytest.mark.asyncio
    async def test_uses_correct_limit_for_anonymous(self) -> None:
        """Uses 20 req/min limit for anonymous users."""
        mock_redis = _create_mock_redis(count=19)
        limiter = RateLimiter()
        limiter._redis = mock_redis

        allowed, limit, remaining, retry_after = await limiter.check_rate_limit(
            "192.168.1.1", is_authenticated=False
        )

        assert allowed is True
        assert limit == 20
        assert remaining == 0  # 20 - 19 - 1

    @pytest.mark.asyncio
    async def test_retry_after_uses_window_when_no_entries(self) -> None:
        """Uses window_seconds for retry-after when no oldest entry."""
        mock_redis = _create_mock_redis(count=100)
        mock_redis.zrange = AsyncMock(return_value=[])  # No oldest entry
        limiter = RateLimiter()
        limiter._redis = mock_redis

        allowed, _, _, retry_after = await limiter.check_rate_limit(
            "user123", is_authenticated=True
        )

        assert allowed is False
        assert retry_after == 60  # Falls back to window_seconds

    @pytest.mark.asyncio
    async def test_adds_entry_when_allowed(self) -> None:
        """Adds entry to Redis when request is allowed."""
        mock_redis = _create_mock_redis(count=5)
        limiter = RateLimiter()
        limiter._redis = mock_redis

        await limiter.check_rate_limit("user123", is_authenticated=True)

        # Verify zadd was called
        mock_redis.zadd.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_add_entry_when_blocked(self) -> None:
        """Does not add entry when rate limited."""
        mock_redis = _create_mock_redis(count=100)
        mock_redis.zrange = AsyncMock(return_value=[("entry", time.time() - 30)])
        limiter = RateLimiter()
        limiter._redis = mock_redis

        await limiter.check_rate_limit("user123", is_authenticated=True)

        # Verify zadd was NOT called
        mock_redis.zadd.assert_not_called()


class TestRateLimiterClose:
    """Tests for RateLimiter.close method."""

    @pytest.mark.asyncio
    async def test_close_clears_redis_connection(self) -> None:
        """close() clears Redis connection."""
        limiter = RateLimiter()
        mock_redis = AsyncMock()
        limiter._redis = mock_redis

        await limiter.close()

        mock_redis.close.assert_called_once()
        assert limiter._redis is None

    @pytest.mark.asyncio
    async def test_close_does_nothing_if_no_connection(self) -> None:
        """close() is safe to call without connection."""
        limiter = RateLimiter()
        await limiter.close()  # Should not raise


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware class."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create a FastAPI app with rate limiting."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"message": "ok"}

        @app.get("/health")
        async def health() -> dict:
            return {"status": "healthy"}

        return app

    def test_init_with_default_rate_limiter(self, app: FastAPI) -> None:
        """Initializes with default rate limiter."""
        middleware = RateLimitMiddleware(app)
        assert middleware.rate_limiter is not None

    def test_init_with_custom_rate_limiter(self, app: FastAPI) -> None:
        """Initializes with custom rate limiter."""
        custom_limiter = RateLimiter(authenticated_limit=50)
        middleware = RateLimitMiddleware(app, rate_limiter=custom_limiter)
        assert middleware.rate_limiter.authenticated_limit == 50

    def test_default_exclude_paths(self, app: FastAPI) -> None:
        """Default exclude paths include health and docs."""
        middleware = RateLimitMiddleware(app)
        assert "/health" in middleware.exclude_paths
        assert "/docs" in middleware.exclude_paths
        assert "/openapi.json" in middleware.exclude_paths

    def test_custom_exclude_paths(self, app: FastAPI) -> None:
        """Custom exclude paths override defaults."""
        middleware = RateLimitMiddleware(app, exclude_paths=["/custom"])
        assert middleware.exclude_paths == ["/custom"]


class TestRateLimitMiddlewareGetClientIp:
    """Tests for RateLimitMiddleware._get_client_ip method."""

    @pytest.fixture
    def middleware(self) -> RateLimitMiddleware:
        """Create middleware instance."""
        app = FastAPI()
        return RateLimitMiddleware(app)

    def test_extracts_from_x_forwarded_for(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Extracts IP from X-Forwarded-For header."""
        request = MagicMock()
        request.headers = {
            "x-forwarded-for": "203.0.113.1, 70.41.3.18, 150.172.238.178"
        }
        request.client = MagicMock(host="10.0.0.1")

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_extracts_from_x_real_ip(self, middleware: RateLimitMiddleware) -> None:
        """Extracts IP from X-Real-IP header."""
        request = MagicMock()
        request.headers = {"x-real-ip": "203.0.113.1"}
        request.client = MagicMock(host="10.0.0.1")

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_falls_back_to_client_host(self, middleware: RateLimitMiddleware) -> None:
        """Falls back to request.client.host."""
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock(host="192.168.1.100")

        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_returns_unknown_when_no_client(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Returns 'unknown' when no client info."""
        request = MagicMock()
        request.headers = {}
        request.client = None

        ip = middleware._get_client_ip(request)
        assert ip == "unknown"


class TestRateLimitMiddlewareExtractUserId:
    """Tests for RateLimitMiddleware._extract_user_id method."""

    @pytest.fixture
    def middleware(self) -> RateLimitMiddleware:
        """Create middleware instance."""
        app = FastAPI()
        return RateLimitMiddleware(app)

    def test_returns_none_without_auth_header(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Returns None when no Authorization header."""
        request = MagicMock()
        request.headers = {}

        user_id = middleware._extract_user_id(request)
        assert user_id is None

    def test_returns_none_without_bearer_prefix(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Returns None when not Bearer token."""
        request = MagicMock()
        request.headers = {"authorization": "Basic abc123"}

        user_id = middleware._extract_user_id(request)
        assert user_id is None

    def test_extracts_user_id_from_valid_token(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Extracts user ID from valid Bearer token."""
        request = MagicMock()
        request.headers = {"authorization": "Bearer valid_token"}

        with patch("app.services.token.token_service") as mock_token:
            mock_payload = MagicMock()
            mock_payload.token_type = "access"
            mock_payload.sub = "user-uuid-123"
            mock_token.verify_token.return_value = mock_payload

            user_id = middleware._extract_user_id(request)
            assert user_id == "user-uuid-123"

    def test_returns_none_for_invalid_token(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Returns None for invalid token."""
        request = MagicMock()
        request.headers = {"authorization": "Bearer invalid_token"}

        with patch("app.services.token.token_service") as mock_token:
            mock_token.verify_token.side_effect = ValueError("Invalid token")

            user_id = middleware._extract_user_id(request)
            assert user_id is None

    def test_returns_none_for_refresh_token(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Returns None for refresh token (not access token)."""
        request = MagicMock()
        request.headers = {"authorization": "Bearer refresh_token"}

        with patch("app.services.token.token_service") as mock_token:
            mock_payload = MagicMock()
            mock_payload.token_type = "refresh"
            mock_token.verify_token.return_value = mock_payload

            user_id = middleware._extract_user_id(request)
            assert user_id is None


class TestRateLimitMiddlewareShouldExclude:
    """Tests for RateLimitMiddleware._should_exclude method."""

    @pytest.fixture
    def middleware(self) -> RateLimitMiddleware:
        """Create middleware instance."""
        app = FastAPI()
        return RateLimitMiddleware(app)

    def test_excludes_health_endpoint(self, middleware: RateLimitMiddleware) -> None:
        """Excludes /health endpoint."""
        assert middleware._should_exclude("/health") is True

    def test_excludes_docs_endpoint(self, middleware: RateLimitMiddleware) -> None:
        """Excludes /docs endpoint."""
        assert middleware._should_exclude("/docs") is True

    def test_excludes_openapi_json(self, middleware: RateLimitMiddleware) -> None:
        """Excludes /openapi.json endpoint."""
        assert middleware._should_exclude("/openapi.json") is True

    def test_does_not_exclude_api_endpoints(
        self, middleware: RateLimitMiddleware
    ) -> None:
        """Does not exclude API endpoints."""
        assert middleware._should_exclude("/api/v1/users") is False
        assert middleware._should_exclude("/api/v1/hosts") is False


class TestRateLimitMiddlewareDispatch:
    """Integration tests for RateLimitMiddleware.dispatch."""

    @pytest.fixture
    def mock_rate_limiter(self) -> MagicMock:
        """Create a mock rate limiter."""
        limiter = MagicMock()
        limiter.check_rate_limit = AsyncMock(return_value=(True, 100, 95, 0))
        limiter.window_seconds = 60
        return limiter

    @pytest.fixture
    def app_with_rate_limit(self, mock_rate_limiter: MagicMock) -> FastAPI:
        """Create app with mocked rate limiter."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"message": "ok"}

        @app.get("/health")
        async def health() -> dict:
            return {"status": "healthy"}

        app.add_middleware(RateLimitMiddleware, rate_limiter=mock_rate_limiter)
        return app

    def test_allows_request_and_adds_headers(
        self, app_with_rate_limit: FastAPI, mock_rate_limiter: MagicMock
    ) -> None:
        """Allows request and adds rate limit headers."""
        client = TestClient(app_with_rate_limit)
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "95"
        assert "X-RateLimit-Reset" in response.headers

    def test_returns_429_when_rate_limited(self, mock_rate_limiter: MagicMock) -> None:
        """Returns 429 when rate limited."""
        # Configure mock to return rate limited
        mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(False, 100, 0, 30))

        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"message": "ok"}

        app.add_middleware(RateLimitMiddleware, rate_limiter=mock_rate_limiter)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 429
        assert response.json()["detail"] == "Too Many Requests"
        assert response.headers["Retry-After"] == "30"
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "0"

    def test_skips_rate_limit_for_excluded_paths(
        self, app_with_rate_limit: FastAPI, mock_rate_limiter: MagicMock
    ) -> None:
        """Skips rate limiting for excluded paths like /health."""
        client = TestClient(app_with_rate_limit)
        response = client.get("/health")

        assert response.status_code == 200
        # Rate limiter should not be called for excluded paths
        mock_rate_limiter.check_rate_limit.assert_not_called()

    def test_allows_request_when_redis_fails(
        self, mock_rate_limiter: MagicMock
    ) -> None:
        """Allows request when Redis is unavailable."""
        # Configure mock to raise exception
        mock_rate_limiter.check_rate_limit = AsyncMock(
            side_effect=Exception("Redis connection failed")
        )

        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"message": "ok"}

        app.add_middleware(RateLimitMiddleware, rate_limiter=mock_rate_limiter)
        client = TestClient(app)

        response = client.get("/test")

        # Should allow request despite Redis failure
        assert response.status_code == 200


class TestRateLimitAuthenticated:
    """Tests verifying 100 req/min limit for authenticated users."""

    def test_rate_limit_authenticated_is_100(self) -> None:
        """Authenticated rate limit is 100 requests per minute."""
        limiter = RateLimiter()
        assert limiter.authenticated_limit == 100


class TestRateLimitAnonymous:
    """Tests verifying 20 req/min limit for anonymous users."""

    def test_rate_limit_anonymous_is_20(self) -> None:
        """Anonymous rate limit is 20 requests per minute."""
        limiter = RateLimiter()
        assert limiter.anonymous_limit == 20


class TestRateLimit429Response:
    """Tests verifying 429 response with Retry-After header."""

    @pytest.fixture
    def mock_rate_limiter(self) -> MagicMock:
        """Create a mock rate limiter that's at limit."""
        limiter = MagicMock()
        limiter.check_rate_limit = AsyncMock(return_value=(False, 100, 0, 45))
        limiter.window_seconds = 60
        return limiter

    def test_returns_429_status_code(self, mock_rate_limiter: MagicMock) -> None:
        """Returns 429 status code when rate limited."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"message": "ok"}

        app.add_middleware(RateLimitMiddleware, rate_limiter=mock_rate_limiter)
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 429

    def test_includes_retry_after_header(self, mock_rate_limiter: MagicMock) -> None:
        """Includes Retry-After header when rate limited."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"message": "ok"}

        app.add_middleware(RateLimitMiddleware, rate_limiter=mock_rate_limiter)
        client = TestClient(app)

        response = client.get("/test")
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "45"

    def test_response_body_includes_detail(self, mock_rate_limiter: MagicMock) -> None:
        """Response body includes error detail."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"message": "ok"}

        app.add_middleware(RateLimitMiddleware, rate_limiter=mock_rate_limiter)
        client = TestClient(app)

        response = client.get("/test")
        data = response.json()
        assert data["detail"] == "Too Many Requests"
        assert data["retry_after"] == 45
