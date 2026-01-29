"""Pydantic schemas for authentication operations."""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserType


class RegisterRequest(BaseModel):
    """Schema for user registration request.

    Validates email format and enforces password strength requirements.
    """

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (8-128 characters, requires uppercase, lowercase, and number)",
    )
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
    user_type: UserType = Field(
        default=UserType.CLIENT,
        description="Type of user account",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets strength requirements.

        Requirements:
        - At least 8 characters (enforced by Field min_length)
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """Schema for user login request."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ...,
        min_length=1,
        description="User's password",
    )


class TokenResponse(BaseModel):
    """Schema for authentication token response.

    Returned after successful login or token refresh.
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(
        default="bearer", description="Token type (always 'bearer')"
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
    )


class RefreshRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="The refresh token to use")


class RefreshResponse(BaseModel):
    """Schema for token refresh response.

    Returns a new access token (refresh token is not rotated).
    """

    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(
        default="bearer", description="Token type (always 'bearer')"
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
    )
