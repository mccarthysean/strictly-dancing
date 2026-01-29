"""Pydantic schemas for authentication operations."""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserType


class RegisterRequest(BaseModel):
    """Schema for user registration request (passwordless).

    Only requires email and name. Authentication is via magic link.
    """

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
    user_type: UserType = Field(
        default=UserType.CLIENT,
        description="Type of user account",
    )


class MagicLinkRequest(BaseModel):
    """Schema for requesting a magic link login code."""

    email: EmailStr = Field(..., description="User's email address")


class MagicLinkResponse(BaseModel):
    """Schema for magic link request response."""

    message: str = Field(
        default="If this email is registered, a login code has been sent.",
        description="Status message (intentionally vague for security)",
    )
    expires_in_minutes: int = Field(
        default=15,
        description="Code expiry time in minutes",
    )


class VerifyMagicLinkRequest(BaseModel):
    """Schema for verifying a magic link code."""

    email: EmailStr = Field(..., description="User's email address")
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit verification code",
    )


# Legacy schemas - kept for backwards compatibility during transition
class LegacyRegisterRequest(BaseModel):
    """Legacy schema for user registration with password.

    DEPRECATED: Use RegisterRequest for passwordless registration.
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
        """Validate password meets strength requirements."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """Legacy schema for user login with password.

    DEPRECATED: Use MagicLinkRequest and VerifyMagicLinkRequest for passwordless auth.
    """

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
