"""Pydantic schemas for request/response validation."""

from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.host_profile import (
    CreateHostProfileRequest,
    DanceStyleRequest,
    DanceStyleResponse,
    HostDanceStyleResponse,
    HostProfileResponse,
    HostProfileSummaryResponse,
    HostProfileWithUserResponse,
    HostSearchRequest,
    HostSearchResponse,
    LocationRequest,
    UpdateHostProfileRequest,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate

__all__ = [
    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Auth schemas
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "RefreshResponse",
    # Host profile schemas
    "CreateHostProfileRequest",
    "UpdateHostProfileRequest",
    "HostProfileResponse",
    "HostProfileWithUserResponse",
    "HostProfileSummaryResponse",
    "HostSearchRequest",
    "HostSearchResponse",
    "LocationRequest",
    "DanceStyleRequest",
    "DanceStyleResponse",
    "HostDanceStyleResponse",
]
