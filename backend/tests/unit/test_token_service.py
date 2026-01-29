"""Unit tests for JWT token service."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.services.token import TokenPayload, TokenService, token_service


class TestTokenService:
    """Tests for TokenService class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = TokenService(
            secret_key="test-secret-key-for-unit-tests",
            algorithm="HS256",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        )
        self.user_id = uuid.uuid4()

    def test_create_access_token_returns_string(self) -> None:
        """Test that create_access_token returns a JWT string."""
        token = self.service.create_access_token(user_id=self.user_id)
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT format: header.payload.signature
        assert token.count(".") == 2

    def test_create_access_token_with_uuid(self) -> None:
        """Test that create_access_token works with UUID user_id."""
        token = self.service.create_access_token(user_id=self.user_id)
        payload = self.service.verify_token(token)
        assert payload.sub == str(self.user_id)

    def test_create_access_token_with_string_uuid(self) -> None:
        """Test that create_access_token works with string user_id."""
        user_id_str = str(self.user_id)
        token = self.service.create_access_token(user_id=user_id_str)
        payload = self.service.verify_token(token)
        assert payload.sub == user_id_str

    def test_create_refresh_token_returns_string(self) -> None:
        """Test that create_refresh_token returns a JWT string."""
        token = self.service.create_refresh_token(user_id=self.user_id)
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2

    def test_access_token_has_15_minute_expiration(self) -> None:
        """Test that access tokens expire in 15 minutes."""
        token = self.service.create_access_token(user_id=self.user_id)
        payload = self.service.verify_token(token)

        # Check expiration is approximately 15 minutes from now
        now = datetime.now(UTC)
        expected_exp = now + timedelta(minutes=15)
        # Allow 1 minute tolerance for test execution time
        assert abs((payload.exp - expected_exp).total_seconds()) < 60

    def test_refresh_token_has_7_day_expiration(self) -> None:
        """Test that refresh tokens expire in 7 days."""
        token = self.service.create_refresh_token(user_id=self.user_id)
        payload = self.service.verify_token(token)

        # Check expiration is approximately 7 days from now
        now = datetime.now(UTC)
        expected_exp = now + timedelta(days=7)
        # Allow 1 minute tolerance for test execution time
        assert abs((payload.exp - expected_exp).total_seconds()) < 60

    def test_token_payload_includes_sub(self) -> None:
        """Test that token payload includes sub (user_id)."""
        token = self.service.create_access_token(user_id=self.user_id)
        payload = self.service.verify_token(token)
        assert payload.sub == str(self.user_id)

    def test_token_payload_includes_exp(self) -> None:
        """Test that token payload includes exp (expiration)."""
        token = self.service.create_access_token(user_id=self.user_id)
        payload = self.service.verify_token(token)
        assert payload.exp is not None
        assert isinstance(payload.exp, datetime)

    def test_token_payload_includes_iat(self) -> None:
        """Test that token payload includes iat (issued at)."""
        token = self.service.create_access_token(user_id=self.user_id)
        payload = self.service.verify_token(token)
        assert payload.iat is not None
        assert isinstance(payload.iat, datetime)
        # iat should be close to now
        now = datetime.now(UTC)
        assert abs((payload.iat - now).total_seconds()) < 60

    def test_token_payload_includes_jti(self) -> None:
        """Test that token payload includes jti (JWT ID)."""
        token = self.service.create_access_token(user_id=self.user_id)
        payload = self.service.verify_token(token)
        assert payload.jti is not None
        assert len(payload.jti) > 0
        # jti should be a valid UUID
        uuid.UUID(payload.jti)

    def test_token_payload_includes_token_type(self) -> None:
        """Test that token payload includes token_type."""
        access_token = self.service.create_access_token(user_id=self.user_id)
        access_payload = self.service.verify_token(access_token)
        assert access_payload.token_type == "access"

        refresh_token = self.service.create_refresh_token(user_id=self.user_id)
        refresh_payload = self.service.verify_token(refresh_token)
        assert refresh_payload.token_type == "refresh"

    def test_verify_token_returns_payload(self) -> None:
        """Test that verify_token returns TokenPayload."""
        token = self.service.create_access_token(user_id=self.user_id)
        payload = self.service.verify_token(token)
        assert isinstance(payload, TokenPayload)

    def test_verify_token_validates_signature(self) -> None:
        """Test that verify_token validates signature."""
        token = self.service.create_access_token(user_id=self.user_id)

        # Tamper with the token by changing the signature
        parts = token.split(".")
        parts[2] = "invalid_signature"
        tampered_token = ".".join(parts)

        with pytest.raises(ValueError, match="Invalid token"):
            self.service.verify_token(tampered_token)

    def test_verify_token_validates_expiration(self) -> None:
        """Test that verify_token rejects expired tokens."""
        # Create a service and manually create an expired token
        service = TokenService(
            secret_key="test-secret-key",
            algorithm="HS256",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        )

        # Mock datetime to create token in the past
        past_time = datetime.now(UTC) - timedelta(hours=1)
        with patch("app.services.token.datetime") as mock_datetime:
            mock_datetime.now.return_value = past_time
            # Make sure timedelta still works
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            token = service.create_access_token(user_id=self.user_id)

        # Token should be expired now
        with pytest.raises(ValueError, match="Token has expired"):
            service.verify_token(token)

    def test_verify_token_rejects_invalid_format(self) -> None:
        """Test that verify_token rejects tokens with invalid format."""
        with pytest.raises(ValueError, match="Invalid token"):
            self.service.verify_token("not.a.valid.token")

    def test_verify_token_rejects_empty_string(self) -> None:
        """Test that verify_token rejects empty string."""
        with pytest.raises(ValueError, match="Invalid token"):
            self.service.verify_token("")

    def test_different_tokens_have_different_jti(self) -> None:
        """Test that each token has a unique jti."""
        token1 = self.service.create_access_token(user_id=self.user_id)
        token2 = self.service.create_access_token(user_id=self.user_id)

        payload1 = self.service.verify_token(token1)
        payload2 = self.service.verify_token(token2)

        assert payload1.jti != payload2.jti

    def test_access_and_refresh_tokens_are_different(self) -> None:
        """Test that access and refresh tokens for same user are different."""
        access_token = self.service.create_access_token(user_id=self.user_id)
        refresh_token = self.service.create_refresh_token(user_id=self.user_id)

        assert access_token != refresh_token

    def test_verify_token_with_wrong_secret_fails(self) -> None:
        """Test that verifying token with wrong secret fails."""
        token = self.service.create_access_token(user_id=self.user_id)

        # Create a service with a different secret
        other_service = TokenService(
            secret_key="different-secret-key",
            algorithm="HS256",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        )

        with pytest.raises(ValueError, match="Invalid token"):
            other_service.verify_token(token)


class TestTokenPayload:
    """Tests for TokenPayload dataclass."""

    def test_token_payload_creation(self) -> None:
        """Test TokenPayload can be created with all fields."""
        now = datetime.now(UTC)
        payload = TokenPayload(
            sub="user-123",
            exp=now + timedelta(hours=1),
            iat=now,
            jti="unique-id",
            token_type="access",
        )
        assert payload.sub == "user-123"
        assert payload.token_type == "access"


class TestTokenServiceSingleton:
    """Tests for the singleton token_service instance."""

    def test_singleton_instance_exists(self) -> None:
        """Test that token_service singleton exists."""
        assert token_service is not None
        assert isinstance(token_service, TokenService)

    def test_singleton_uses_settings(self) -> None:
        """Test that singleton uses application settings."""
        # The singleton should be configured from settings
        # We can test by creating a token and verifying it works
        user_id = uuid.uuid4()
        token = token_service.create_access_token(user_id=user_id)
        assert isinstance(token, str)


class TestExpiredToken:
    """Tests for expired token handling."""

    def test_expired_access_token_raises_error(self) -> None:
        """Test that expired access token raises ValueError."""
        service = TokenService(
            secret_key="test-secret",
            algorithm="HS256",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        )
        user_id = uuid.uuid4()

        # Mock datetime to create token in the past
        past_time = datetime.now(UTC) - timedelta(hours=1)
        with patch("app.services.token.datetime") as mock_datetime:
            mock_datetime.now.return_value = past_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            token = service.create_access_token(user_id=user_id)

        # Token should be expired now
        with pytest.raises(ValueError, match="Token has expired"):
            service.verify_token(token)
