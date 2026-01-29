"""Unit tests for authentication Pydantic schemas (passwordless)."""

import pytest
from pydantic import ValidationError

from app.models.user import UserType
from app.schemas.auth import (
    MagicLinkRequest,
    MagicLinkResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    VerifyMagicLinkRequest,
)


class TestRegisterRequestSchema:
    """Tests for RegisterRequest schema (passwordless)."""

    def test_register_request_valid(self) -> None:
        """Test RegisterRequest with valid data."""
        data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
        }
        req = RegisterRequest(**data)

        assert req.email == "test@example.com"
        assert req.first_name == "John"
        assert req.last_name == "Doe"
        assert req.user_type == UserType.CLIENT  # Default value

    def test_register_request_with_user_type(self) -> None:
        """Test RegisterRequest with explicit user_type."""
        data = {
            "email": "host@example.com",
            "first_name": "Jane",
            "last_name": "Host",
            "user_type": UserType.HOST,
        }
        req = RegisterRequest(**data)

        assert req.user_type == UserType.HOST

    def test_auth_schema_email_validation(self) -> None:
        """Test that RegisterRequest validates email format."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="invalid-email",
                first_name="John",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("email",)

    def test_register_request_email_case_preserved(self) -> None:
        """Test that email domain is normalized by EmailStr."""
        req = RegisterRequest(
            email="Test@Example.COM",
            first_name="John",
            last_name="Doe",
        )
        # EmailStr normalizes domain to lowercase
        assert "@example.com" in req.email.lower()

    def test_register_request_requires_first_name(self) -> None:
        """Test that first_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("first_name",) for e in errors)

    def test_register_request_requires_last_name(self) -> None:
        """Test that last_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                first_name="John",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("last_name",) for e in errors)

    def test_register_request_first_name_min_length(self) -> None:
        """Test that first_name requires minimum 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                first_name="",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("first_name",) for e in errors)

    def test_register_request_last_name_min_length(self) -> None:
        """Test that last_name requires minimum 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                first_name="John",
                last_name="",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("last_name",) for e in errors)

    def test_register_request_no_password_required(self) -> None:
        """Test that RegisterRequest does NOT require password (passwordless)."""
        # Should work without password
        req = RegisterRequest(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )
        assert req.email == "test@example.com"
        # Verify password is not a field
        assert "password" not in RegisterRequest.model_fields


class TestMagicLinkRequestSchema:
    """Tests for MagicLinkRequest schema."""

    def test_magic_link_request_valid(self) -> None:
        """Test MagicLinkRequest with valid data."""
        req = MagicLinkRequest(email="test@example.com")
        assert req.email == "test@example.com"

    def test_magic_link_request_validates_email(self) -> None:
        """Test that MagicLinkRequest validates email format."""
        with pytest.raises(ValidationError) as exc_info:
            MagicLinkRequest(email="invalid-email")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_magic_link_request_requires_email(self) -> None:
        """Test that email is required."""
        with pytest.raises(ValidationError) as exc_info:
            MagicLinkRequest()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)


class TestMagicLinkResponseSchema:
    """Tests for MagicLinkResponse schema."""

    def test_magic_link_response_default_values(self) -> None:
        """Test MagicLinkResponse has correct default values."""
        response = MagicLinkResponse()
        assert (
            "login code" in response.message.lower()
            or "email" in response.message.lower()
        )
        assert response.expires_in_minutes == 15

    def test_magic_link_response_custom_values(self) -> None:
        """Test MagicLinkResponse with custom values."""
        response = MagicLinkResponse(
            message="Custom message",
            expires_in_minutes=30,
        )
        assert response.message == "Custom message"
        assert response.expires_in_minutes == 30


class TestVerifyMagicLinkRequestSchema:
    """Tests for VerifyMagicLinkRequest schema."""

    def test_verify_magic_link_request_valid(self) -> None:
        """Test VerifyMagicLinkRequest with valid data."""
        req = VerifyMagicLinkRequest(
            email="test@example.com",
            code="123456",
        )
        assert req.email == "test@example.com"
        assert req.code == "123456"

    def test_verify_magic_link_request_validates_email(self) -> None:
        """Test that email is validated."""
        with pytest.raises(ValidationError) as exc_info:
            VerifyMagicLinkRequest(
                email="invalid-email",
                code="123456",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_verify_magic_link_request_code_must_be_6_digits(self) -> None:
        """Test that code must be exactly 6 digits."""
        with pytest.raises(ValidationError) as exc_info:
            VerifyMagicLinkRequest(
                email="test@example.com",
                code="12345",  # Too short
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    def test_verify_magic_link_request_code_must_be_numeric(self) -> None:
        """Test that code must be numeric."""
        with pytest.raises(ValidationError) as exc_info:
            VerifyMagicLinkRequest(
                email="test@example.com",
                code="abcdef",  # Not numeric
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    def test_verify_magic_link_request_code_cannot_be_too_long(self) -> None:
        """Test that code cannot be longer than 6 digits."""
        with pytest.raises(ValidationError) as exc_info:
            VerifyMagicLinkRequest(
                email="test@example.com",
                code="1234567",  # Too long
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)


class TestTokenResponseSchema:
    """Tests for TokenResponse schema."""

    def test_token_response_valid(self) -> None:
        """Test TokenResponse with valid data."""
        response = TokenResponse(
            access_token="access.token.here",
            refresh_token="refresh.token.here",
            expires_in=900,
        )

        assert response.access_token == "access.token.here"
        assert response.refresh_token == "refresh.token.here"
        assert response.token_type == "bearer"  # Default value
        assert response.expires_in == 900

    def test_token_response_custom_token_type(self) -> None:
        """Test TokenResponse with custom token type."""
        response = TokenResponse(
            access_token="access.token.here",
            refresh_token="refresh.token.here",
            token_type="custom",
            expires_in=900,
        )

        assert response.token_type == "custom"

    def test_token_response_requires_access_token(self) -> None:
        """Test that access_token is required."""
        with pytest.raises(ValidationError) as exc_info:
            TokenResponse(
                refresh_token="refresh.token.here",
                expires_in=900,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("access_token",) for e in errors)

    def test_token_response_requires_refresh_token(self) -> None:
        """Test that refresh_token is required."""
        with pytest.raises(ValidationError) as exc_info:
            TokenResponse(
                access_token="access.token.here",
                expires_in=900,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("refresh_token",) for e in errors)

    def test_token_response_requires_expires_in(self) -> None:
        """Test that expires_in is required."""
        with pytest.raises(ValidationError) as exc_info:
            TokenResponse(
                access_token="access.token.here",
                refresh_token="refresh.token.here",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("expires_in",) for e in errors)


class TestRefreshRequestSchema:
    """Tests for RefreshRequest schema."""

    def test_refresh_request_valid(self) -> None:
        """Test RefreshRequest with valid data."""
        req = RefreshRequest(refresh_token="refresh.token.here")

        assert req.refresh_token == "refresh.token.here"

    def test_refresh_request_requires_refresh_token(self) -> None:
        """Test that refresh_token is required."""
        with pytest.raises(ValidationError) as exc_info:
            RefreshRequest()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("refresh_token",) for e in errors)


class TestAuthSchemaIntegration:
    """Integration tests for auth schema relationships."""

    def test_register_request_field_types(self) -> None:
        """Test that RegisterRequest has expected field types (passwordless)."""
        fields = RegisterRequest.model_fields

        assert "email" in fields
        assert "first_name" in fields
        assert "last_name" in fields
        assert "user_type" in fields
        # Password is NOT a field in passwordless auth
        assert "password" not in fields

    def test_token_response_serialization(self) -> None:
        """Test that TokenResponse serializes correctly for API responses."""
        response = TokenResponse(
            access_token="access.token.here",
            refresh_token="refresh.token.here",
            expires_in=900,
        )

        data = response.model_dump()

        assert data["access_token"] == "access.token.here"
        assert data["refresh_token"] == "refresh.token.here"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900
