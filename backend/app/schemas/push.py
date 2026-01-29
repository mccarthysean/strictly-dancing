"""Pydantic schemas for push notification operations."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.push_token import DevicePlatform


class RegisterPushTokenRequest(BaseModel):
    """Schema for registering a push token."""

    token: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="The Expo push token (ExponentPushToken[...])",
    )
    platform: DevicePlatform = Field(
        ..., description="Device platform (ios, android, web)"
    )
    device_id: str | None = Field(
        default=None,
        max_length=255,
        description="Optional unique device identifier",
    )
    device_name: str | None = Field(
        default=None,
        max_length=255,
        description="Optional human-readable device name",
    )

    @field_validator("token")
    @classmethod
    def validate_token_format(cls, v: str) -> str:
        """Validate that token has proper Expo format."""
        if not (
            v.startswith("ExponentPushToken[") or v.startswith("ExpoPushToken[")
        ) or not v.endswith("]"):
            msg = "Token must be in Expo format: ExponentPushToken[...] or ExpoPushToken[...]"
            raise ValueError(msg)
        return v


class UnregisterPushTokenRequest(BaseModel):
    """Schema for unregistering a push token."""

    token: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="The Expo push token to unregister",
    )


class PushTokenResponse(BaseModel):
    """Schema for push token in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Push token UUID")
    token: str = Field(..., description="The Expo push token")
    platform: DevicePlatform = Field(..., description="Device platform")
    device_id: str | None = Field(None, description="Device identifier")
    device_name: str | None = Field(None, description="Device name")
    is_active: bool = Field(..., description="Whether the token is active")


class PushTokenListResponse(BaseModel):
    """Response containing list of push tokens."""

    items: list[PushTokenResponse] = Field(
        ..., description="List of registered push tokens"
    )
    count: int = Field(..., description="Total number of tokens")
