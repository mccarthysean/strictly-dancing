"""Unit tests for magic link authentication service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.magic_link import MagicLinkService, magic_link_service


class TestMagicLinkService:
    """Tests for MagicLinkService class."""

    def test_service_singleton_exists(self) -> None:
        """Test that the singleton instance exists."""
        assert magic_link_service is not None
        assert isinstance(magic_link_service, MagicLinkService)

    def test_default_expiry_minutes(self) -> None:
        """Test default expiry is 15 minutes."""
        assert MagicLinkService.DEFAULT_EXPIRY_MINUTES == 15

    def test_code_length_is_six(self) -> None:
        """Test code length is 6 digits."""
        assert MagicLinkService.CODE_LENGTH == 6

    def test_redis_key_prefix(self) -> None:
        """Test Redis key prefix is correct."""
        assert MagicLinkService.REDIS_KEY_PREFIX == "magic_link:"


class TestGenerateCode:
    """Tests for code generation."""

    def test_generated_code_is_string(self) -> None:
        """Test that generated code is a string."""
        service = MagicLinkService()
        code = service._generate_code()
        assert isinstance(code, str)

    def test_generated_code_is_six_digits(self) -> None:
        """Test that generated code is exactly 6 characters."""
        service = MagicLinkService()
        code = service._generate_code()
        assert len(code) == 6

    def test_generated_code_is_numeric(self) -> None:
        """Test that generated code contains only digits."""
        service = MagicLinkService()
        code = service._generate_code()
        assert code.isdigit()

    def test_generated_code_is_zero_padded(self) -> None:
        """Test that codes less than 100000 are zero-padded."""
        service = MagicLinkService()
        # Generate multiple codes and verify all are 6 digits
        for _ in range(100):
            code = service._generate_code()
            assert len(code) == 6

    def test_generated_codes_are_random(self) -> None:
        """Test that multiple generated codes are not identical."""
        service = MagicLinkService()
        codes = [service._generate_code() for _ in range(10)]
        # At least some codes should be different (extremely unlikely all same)
        assert len(set(codes)) > 1


class TestGetRedisKey:
    """Tests for Redis key generation."""

    def test_key_includes_prefix(self) -> None:
        """Test that key includes the magic_link prefix."""
        service = MagicLinkService()
        key = service._get_redis_key("test@example.com")
        assert key.startswith("magic_link:")

    def test_key_includes_email(self) -> None:
        """Test that key includes the email."""
        service = MagicLinkService()
        key = service._get_redis_key("test@example.com")
        assert "test@example.com" in key

    def test_key_lowercases_email(self) -> None:
        """Test that email is lowercased in key."""
        service = MagicLinkService()
        key1 = service._get_redis_key("TEST@EXAMPLE.COM")
        key2 = service._get_redis_key("test@example.com")
        assert key1 == key2

    def test_different_emails_different_keys(self) -> None:
        """Test that different emails produce different keys."""
        service = MagicLinkService()
        key1 = service._get_redis_key("user1@example.com")
        key2 = service._get_redis_key("user2@example.com")
        assert key1 != key2


class TestCreateCode:
    """Tests for create_code method."""

    @pytest.mark.asyncio
    async def test_create_code_returns_string(self) -> None:
        """Test that create_code returns a string."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        service = MagicLinkService(redis_client=mock_redis)
        code = await service.create_code("test@example.com")

        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isdigit()

    @pytest.mark.asyncio
    async def test_create_code_stores_in_redis(self) -> None:
        """Test that create_code stores code in Redis."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        service = MagicLinkService(redis_client=mock_redis)
        await service.create_code("test@example.com")

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        # First arg is key
        assert call_args[0][0] == "magic_link:test@example.com"
        # Second arg is TTL in seconds (15 minutes = 900 seconds)
        assert call_args[0][1] == 900

    @pytest.mark.asyncio
    async def test_create_code_custom_expiry(self) -> None:
        """Test that create_code uses custom expiry time."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        service = MagicLinkService(redis_client=mock_redis)
        await service.create_code("test@example.com", expiry_minutes=30)

        call_args = mock_redis.setex.call_args
        # TTL should be 30 minutes = 1800 seconds
        assert call_args[0][1] == 1800

    @pytest.mark.asyncio
    async def test_create_code_logs_event(self) -> None:
        """Test that create_code logs the event."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch("app.services.magic_link.logger") as mock_logger:
            service = MagicLinkService(redis_client=mock_redis)
            await service.create_code("test@example.com")

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "magic_link_code_created"


class TestVerifyCode:
    """Tests for verify_code method."""

    @pytest.mark.asyncio
    async def test_verify_valid_code(self) -> None:
        """Test that valid code verification succeeds."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="123456:2026-01-29T00:00:00+00:00")
        mock_redis.delete = AsyncMock()

        service = MagicLinkService(redis_client=mock_redis)
        result = await service.verify_code("test@example.com", "123456")

        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_invalid_code(self) -> None:
        """Test that invalid code verification fails."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="123456:2026-01-29T00:00:00+00:00")

        service = MagicLinkService(redis_client=mock_redis)
        result = await service.verify_code("test@example.com", "999999")

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_expired_code(self) -> None:
        """Test that expired code (not found) verification fails."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        service = MagicLinkService(redis_client=mock_redis)
        result = await service.verify_code("test@example.com", "123456")

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_code_deletes_after_success(self) -> None:
        """Test that code is deleted after successful verification."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="123456:2026-01-29T00:00:00+00:00")
        mock_redis.delete = AsyncMock()

        service = MagicLinkService(redis_client=mock_redis)
        await service.verify_code("test@example.com", "123456")

        mock_redis.delete.assert_called_once_with("magic_link:test@example.com")

    @pytest.mark.asyncio
    async def test_verify_code_case_insensitive_email(self) -> None:
        """Test that email lookup is case-insensitive."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="123456:2026-01-29T00:00:00+00:00")
        mock_redis.delete = AsyncMock()

        service = MagicLinkService(redis_client=mock_redis)
        result = await service.verify_code("TEST@EXAMPLE.COM", "123456")

        assert result is True
        mock_redis.get.assert_called_with("magic_link:test@example.com")


class TestInvalidateCode:
    """Tests for invalidate_code method."""

    @pytest.mark.asyncio
    async def test_invalidate_existing_code(self) -> None:
        """Test invalidating an existing code."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)

        service = MagicLinkService(redis_client=mock_redis)
        result = await service.invalidate_code("test@example.com")

        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_code(self) -> None:
        """Test invalidating a nonexistent code."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=0)

        service = MagicLinkService(redis_client=mock_redis)
        result = await service.invalidate_code("test@example.com")

        assert result is False


class TestGetRemainingTtl:
    """Tests for get_remaining_ttl method."""

    @pytest.mark.asyncio
    async def test_get_ttl_existing_code(self) -> None:
        """Test getting TTL for an existing code."""
        mock_redis = AsyncMock()
        mock_redis.ttl = AsyncMock(return_value=600)

        service = MagicLinkService(redis_client=mock_redis)
        result = await service.get_remaining_ttl("test@example.com")

        assert result == 600

    @pytest.mark.asyncio
    async def test_get_ttl_nonexistent_code(self) -> None:
        """Test getting TTL for a nonexistent code."""
        mock_redis = AsyncMock()
        mock_redis.ttl = AsyncMock(return_value=-2)

        service = MagicLinkService(redis_client=mock_redis)
        result = await service.get_remaining_ttl("test@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_ttl_no_expiry(self) -> None:
        """Test getting TTL for a code with no expiry."""
        mock_redis = AsyncMock()
        mock_redis.ttl = AsyncMock(return_value=-1)

        service = MagicLinkService(redis_client=mock_redis)
        result = await service.get_remaining_ttl("test@example.com")

        assert result is None


class TestLazyRedisConnection:
    """Tests for lazy Redis connection initialization."""

    @pytest.mark.asyncio
    async def test_redis_client_created_lazily(self) -> None:
        """Test that Redis client is created on first use."""
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_redis = MagicMock()
            mock_redis.setex = AsyncMock()
            mock_from_url.return_value = mock_redis

            service = MagicLinkService()
            await service.create_code("test@example.com")

            mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_client_reused(self) -> None:
        """Test that Redis client is reused on subsequent calls."""
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_redis = MagicMock()
            mock_redis.setex = AsyncMock()
            mock_redis.get = AsyncMock(return_value="123456:timestamp")
            mock_redis.delete = AsyncMock()
            mock_from_url.return_value = mock_redis

            service = MagicLinkService()
            await service.create_code("test@example.com")
            await service.verify_code("test@example.com", "123456")

            # Redis client should only be created once
            mock_from_url.assert_called_once()
