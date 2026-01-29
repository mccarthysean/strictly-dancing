"""Authentication router for user registration, login, and token management."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.password import password_service
from app.services.token import token_service

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, password, and profile information.",
)
async def register(
    request: RegisterRequest,
    db: DbSession,
) -> UserResponse:
    """Register a new user account.

    Validates that the email is not already registered (case-insensitive),
    hashes the password securely, and creates the user in the database.

    Args:
        request: The registration request with user details.
        db: The database session (injected).

    Returns:
        UserResponse with the newly created user's data.

    Raises:
        HTTPException 409: If email is already registered.
        HTTPException 422: If validation fails (invalid email, weak password, etc.).
    """
    user_repo = UserRepository(db)

    # Check if email already exists (case-insensitive)
    if await user_repo.exists_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Hash the password
    password_hash = password_service.hash_password(request.password)

    # Create UserCreate schema for the repository
    user_data = UserCreate(
        email=request.email,
        password=request.password,  # Not used by repo, but required by schema
        first_name=request.first_name,
        last_name=request.last_name,
        user_type=request.user_type,
    )

    # Create the user
    user = await user_repo.create(user_data=user_data, password_hash=password_hash)

    return UserResponse.model_validate(user)


# Generic invalid credentials error - intentionally vague to prevent user enumeration
INVALID_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user",
    description="Authenticate with email and password to receive access and refresh tokens.",
)
async def login(
    request: LoginRequest,
    db: DbSession,
) -> TokenResponse:
    """Authenticate user and return JWT tokens.

    Validates credentials and returns access/refresh tokens on success.
    Uses the same error message for both invalid email and invalid password
    to prevent user enumeration attacks.

    Args:
        request: The login request with email and password.
        db: The database session (injected).

    Returns:
        TokenResponse with access_token, refresh_token, and expiration info.

    Raises:
        HTTPException 401: If credentials are invalid.
    """
    user_repo = UserRepository(db)

    # Look up user by email (case-insensitive)
    user = await user_repo.get_by_email(request.email)
    if user is None:
        # User not found - return same error as wrong password
        raise INVALID_CREDENTIALS_ERROR

    # Check if user is active
    if not user.is_active:
        raise INVALID_CREDENTIALS_ERROR

    # Verify password
    if not password_service.verify_password(request.password, user.password_hash):
        raise INVALID_CREDENTIALS_ERROR

    # Create tokens
    access_token = token_service.create_access_token(user.id)
    refresh_token = token_service.create_refresh_token(user.id)

    # Get expiration time in seconds from settings
    settings = get_settings()
    expires_in = settings.jwt_access_token_expire_minutes * 60

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
    )


# Invalid token error
INVALID_TOKEN_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired refresh token",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token.",
)
async def refresh(
    request: RefreshRequest,
) -> RefreshResponse:
    """Refresh access token using a valid refresh token.

    Validates the refresh token and issues a new access token.
    The refresh token itself is not rotated.

    Args:
        request: The refresh request with the refresh token.

    Returns:
        RefreshResponse with new access_token and expiration info.

    Raises:
        HTTPException 401: If refresh token is invalid or expired.
    """
    # Verify the refresh token
    try:
        payload = token_service.verify_token(request.refresh_token)
    except ValueError as e:
        error_message = str(e).lower()
        if "expired" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        raise INVALID_TOKEN_ERROR from e

    # Ensure it's a refresh token, not an access token
    if payload.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: must be a refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create a new access token
    access_token = token_service.create_access_token(payload.sub)

    # Get expiration time in seconds from settings
    settings = get_settings()
    expires_in = settings.jwt_access_token_expire_minutes * 60

    return RefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Invalidate the current session. Client should discard tokens.",
)
async def logout(
    current_user: CurrentUser,  # noqa: ARG001 - User validated but not used
) -> None:
    """Logout the current authenticated user.

    This endpoint is idempotent - it always succeeds for authenticated users.
    Since we use stateless JWT tokens, the actual token invalidation happens
    client-side by discarding the tokens. The server validates authentication
    to ensure the request is legitimate.

    Args:
        current_user: The authenticated user (injected, validates auth).

    Returns:
        None (204 No Content).
    """
    # JWT is stateless, so logout is handled client-side by discarding tokens.
    # This endpoint exists for consistency and could be extended in the future
    # to support token blacklisting if needed.
    return None


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Retrieve the authenticated user's profile information.",
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserResponse:
    """Get the current authenticated user's profile.

    Returns the full user profile information for the authenticated user.
    This endpoint requires a valid access token.

    Args:
        current_user: The authenticated user (injected via auth middleware).

    Returns:
        UserResponse with the user's profile data.
    """
    return UserResponse.model_validate(current_user)
