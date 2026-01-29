"""Pydantic schemas for user operations."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserType


class UserBase(BaseModel):
    """Base schema with common user fields."""

    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's first name",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's last name",
    )


class UserCreate(UserBase):
    """Schema for creating a new user.

    Used for user registration. Includes password for account creation.
    Password is NOT stored - it's hashed before storage.
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (8-128 characters)",
    )
    user_type: UserType = Field(
        default=UserType.CLIENT,
        description="Type of user account",
    )


class UserUpdate(BaseModel):
    """Schema for updating user profile.

    All fields are optional - only provided fields will be updated.
    """

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="User's first name",
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="User's last name",
    )


class UserResponse(BaseModel):
    """Schema for user data in API responses.

    IMPORTANT: This schema explicitly excludes password_hash.
    Never expose password hashes in API responses.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User's unique identifier (UUID)")
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    user_type: UserType = Field(..., description="Type of user account")
    email_verified: bool = Field(..., description="Whether email is verified")
    is_active: bool = Field(..., description="Whether account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # password_hash is intentionally NOT included - never expose in responses
