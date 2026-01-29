"""Unit tests for user Pydantic schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.user import UserType
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class TestUserCreateSchema:
    """Tests for UserCreate schema."""

    def test_user_create_valid(self) -> None:
        """Test UserCreate with valid data."""
        data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
        }
        user = UserCreate(**data)

        assert user.email == "test@example.com"
        assert user.password == "securepassword123"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.user_type == UserType.CLIENT  # Default value

    def test_user_create_with_user_type(self) -> None:
        """Test UserCreate with explicit user_type."""
        data = {
            "email": "host@example.com",
            "password": "securepassword123",
            "first_name": "Jane",
            "last_name": "Host",
            "user_type": UserType.HOST,
        }
        user = UserCreate(**data)

        assert user.user_type == UserType.HOST

    def test_user_create_schema_validates_email(self) -> None:
        """Test that UserCreate validates email format."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="invalid-email",
                password="securepassword123",
                first_name="John",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("email",)
        assert (
            "email" in errors[0]["type"].lower() or "value" in errors[0]["type"].lower()
        )

    def test_user_create_email_case_insensitive_stored(self) -> None:
        """Test that email is stored as provided (validation only checks format)."""
        user = UserCreate(
            email="Test@Example.COM",
            password="securepassword123",
            first_name="John",
            last_name="Doe",
        )
        # EmailStr normalizes domain to lowercase but preserves local part
        assert "@example.com" in user.email.lower()

    def test_user_create_password_min_length(self) -> None:
        """Test that password requires minimum 8 characters."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="short",  # Only 5 characters
                first_name="John",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_user_create_requires_first_name(self) -> None:
        """Test that first_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="securepassword123",
                last_name="Doe",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("first_name",) for e in errors)

    def test_user_create_requires_last_name(self) -> None:
        """Test that last_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="securepassword123",
                first_name="John",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("last_name",) for e in errors)


class TestUserUpdateSchema:
    """Tests for UserUpdate schema."""

    def test_user_update_all_optional(self) -> None:
        """Test that UserUpdate allows all fields to be optional."""
        user = UserUpdate()

        assert user.first_name is None
        assert user.last_name is None

    def test_user_update_partial(self) -> None:
        """Test partial update with some fields."""
        user = UserUpdate(first_name="Jane")

        assert user.first_name == "Jane"
        assert user.last_name is None

    def test_user_update_first_name_min_length(self) -> None:
        """Test that first_name requires minimum 1 character when provided."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(first_name="")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("first_name",) for e in errors)


class TestUserResponseSchema:
    """Tests for UserResponse schema."""

    def test_user_response_excludes_password_hash(self) -> None:
        """Test that password_hash is NOT in UserResponse fields."""
        # Get all field names from the schema
        field_names = set(UserResponse.model_fields.keys())

        assert "password_hash" not in field_names
        assert "password" not in field_names

    def test_user_response_from_dict(self) -> None:
        """Test creating UserResponse from dictionary data."""
        data = {
            "id": "12345678-1234-1234-1234-123456789012",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "user_type": UserType.CLIENT,
            "email_verified": False,
            "is_active": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        user = UserResponse(**data)

        assert user.id == "12345678-1234-1234-1234-123456789012"
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"

    def test_user_response_with_password_hash_in_input_ignored(self) -> None:
        """Test that password_hash in input data is ignored (not exposed)."""
        data = {
            "id": "12345678-1234-1234-1234-123456789012",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "user_type": UserType.CLIENT,
            "email_verified": False,
            "is_active": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "password_hash": "secret_hash_value",  # This should be ignored
        }
        user = UserResponse.model_validate(data)

        # Verify password_hash is not accessible
        assert (
            not hasattr(user, "password_hash")
            or getattr(user, "password_hash", None) is None
        )

    def test_user_response_from_attributes(self) -> None:
        """Test that UserResponse can be created from ORM model attributes."""

        # Simulate an ORM object with attributes
        class MockUser:
            id = "12345678-1234-1234-1234-123456789012"
            email = "test@example.com"
            password_hash = "should_not_be_exposed"
            first_name = "John"
            last_name = "Doe"
            user_type = UserType.CLIENT
            email_verified = True
            is_active = True
            created_at = datetime.now(UTC)
            updated_at = datetime.now(UTC)

        # Need to pass an instance, not the class
        user = UserResponse.model_validate(MockUser(), from_attributes=True)

        assert user.email == "test@example.com"
        # Verify password_hash is not in the response
        response_dict = user.model_dump()
        assert "password_hash" not in response_dict

    def test_user_response_has_all_required_fields(self) -> None:
        """Test that UserResponse includes all expected fields."""
        expected_fields = {
            "id",
            "email",
            "first_name",
            "last_name",
            "user_type",
            "email_verified",
            "is_active",
            "created_at",
            "updated_at",
        }
        actual_fields = set(UserResponse.model_fields.keys())

        assert expected_fields == actual_fields


class TestSchemaIntegration:
    """Integration tests for schema relationships."""

    def test_create_to_response_field_mapping(self) -> None:
        """Test that UserCreate fields map correctly to UserResponse fields."""
        # UserCreate fields (excluding password)
        create_fields = set(UserCreate.model_fields.keys()) - {"password"}

        # UserResponse fields (excluding timestamps and other server-side fields)
        response_fields = set(UserResponse.model_fields.keys())

        # All UserCreate fields (except password) should be in UserResponse
        for field in create_fields:
            assert field in response_fields, (
                f"Field '{field}' missing from UserResponse"
            )
