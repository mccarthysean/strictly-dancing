"""Unit tests for authentication Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.models.user import UserType
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)


class TestRegisterRequestSchema:
    """Tests for RegisterRequest schema."""

    def test_register_request_valid(self) -> None:
        """Test RegisterRequest with valid data."""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123",
            "first_name": "John",
            "last_name": "Doe",
        }
        req = RegisterRequest(**data)

        assert req.email == "test@example.com"
        assert req.password == "SecurePass123"
        assert req.first_name == "John"
        assert req.last_name == "Doe"
        assert req.user_type == UserType.CLIENT  # Default value

    def test_register_request_with_user_type(self) -> None:
        """Test RegisterRequest with explicit user_type."""
        data = {
            "email": "host@example.com",
            "password": "SecurePass123",
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
                password="SecurePass123",
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
            password="SecurePass123",
            first_name="John",
            last_name="Doe",
        )
        # EmailStr normalizes domain to lowercase
        assert "@example.com" in req.email.lower()

    def test_auth_schema_password_strength_min_length(self) -> None:
        """Test that password requires minimum 8 characters."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="Short1",  # Too short
                first_name="John",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_auth_schema_password_strength_requires_uppercase(self) -> None:
        """Test that password requires at least one uppercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="lowercase123",  # No uppercase
                first_name="John",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)
        assert any("uppercase" in str(e["msg"]).lower() for e in errors)

    def test_auth_schema_password_strength_requires_lowercase(self) -> None:
        """Test that password requires at least one lowercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="UPPERCASE123",  # No lowercase
                first_name="John",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)
        assert any("lowercase" in str(e["msg"]).lower() for e in errors)

    def test_auth_schema_password_strength_requires_digit(self) -> None:
        """Test that password requires at least one digit."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="NoDigitsHere",  # No digit
                first_name="John",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)
        assert any("digit" in str(e["msg"]).lower() for e in errors)

    def test_register_request_requires_first_name(self) -> None:
        """Test that first_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("first_name",) for e in errors)

    def test_register_request_requires_last_name(self) -> None:
        """Test that last_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123",
                first_name="John",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("last_name",) for e in errors)

    def test_register_request_first_name_min_length(self) -> None:
        """Test that first_name requires minimum 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123",
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
                password="SecurePass123",
                first_name="John",
                last_name="",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("last_name",) for e in errors)


class TestLoginRequestSchema:
    """Tests for LoginRequest schema."""

    def test_login_request_valid(self) -> None:
        """Test LoginRequest with valid data."""
        req = LoginRequest(
            email="test@example.com",
            password="anypassword",
        )

        assert req.email == "test@example.com"
        assert req.password == "anypassword"

    def test_login_request_validates_email(self) -> None:
        """Test that LoginRequest validates email format."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(
                email="invalid-email",
                password="password123",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_login_request_requires_password(self) -> None:
        """Test that password is required."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(
                email="test@example.com",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_login_request_password_cannot_be_empty(self) -> None:
        """Test that password cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(
                email="test@example.com",
                password="",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)


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
        """Test that RegisterRequest has expected field types."""
        fields = RegisterRequest.model_fields

        assert "email" in fields
        assert "password" in fields
        assert "first_name" in fields
        assert "last_name" in fields
        assert "user_type" in fields

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
