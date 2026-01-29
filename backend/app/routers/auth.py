"""Authentication router for user registration, login, and token management.

Implements passwordless authentication using magic link codes sent via email.
Users request a code, receive it by email, and exchange it for JWT tokens.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.repositories.user import UserRepository
from app.schemas.auth import (
    MagicLinkRequest,
    MagicLinkResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
    VerifyMagicLinkRequest,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.magic_link import magic_link_service
from app.services.token import token_service
from app.workers import send_magic_link_email, send_welcome_email

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (passwordless)",
    description="Create a new user account with email and profile information. "
    "A magic link code will be sent to complete registration.",
)
async def register(
    request: RegisterRequest,
    db: DbSession,
) -> UserResponse:
    """Register a new user account (passwordless).

    Creates a new user and sends a welcome email. The user can then
    request a magic link to log in.

    Args:
        request: The registration request with user details.
        db: The database session (injected).

    Returns:
        UserResponse with the newly created user's data.

    Raises:
        HTTPException 409: If email is already registered.
        HTTPException 422: If validation fails.
    """
    user_repo = UserRepository(db)

    # Check if email already exists (case-insensitive)
    if await user_repo.exists_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create UserCreate schema for the repository (no password)
    user_data = UserCreate(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        user_type=request.user_type,
    )

    # Create the user without a password
    user = await user_repo.create_passwordless(user_data=user_data)

    # Send welcome email asynchronously
    send_welcome_email.delay(
        to_email=user.email,
        name=user.first_name,
    )

    return UserResponse.model_validate(user)


@router.post(
    "/request-magic-link",
    response_model=MagicLinkResponse,
    summary="Request a magic link login code",
    description="Request a 6-digit login code to be sent to the provided email. "
    "The code expires after 15 minutes.",
)
async def request_magic_link(
    request: MagicLinkRequest,
    db: DbSession,
) -> MagicLinkResponse:
    """Request a magic link login code.

    Generates a 6-digit code and sends it to the user's email.
    For security, the response is always the same whether the email
    exists or not (prevents user enumeration).

    Args:
        request: The magic link request with email.
        db: The database session (injected).

    Returns:
        MagicLinkResponse with a generic success message.
    """
    user_repo = UserRepository(db)

    # Look up user by email
    user = await user_repo.get_by_email(request.email)

    if user is not None and user.is_active:
        # Generate and store magic link code
        code = await magic_link_service.create_code(request.email)

        # Send magic link email asynchronously
        send_magic_link_email.delay(
            to_email=user.email,
            name=user.first_name,
            code=code,
            expires_minutes=magic_link_service.DEFAULT_EXPIRY_MINUTES,
        )

    # Always return success to prevent user enumeration
    return MagicLinkResponse(
        message="If this email is registered, a login code has been sent.",
        expires_in_minutes=magic_link_service.DEFAULT_EXPIRY_MINUTES,
    )


# Invalid code error - intentionally vague to prevent user enumeration
INVALID_CODE_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired code",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post(
    "/verify-magic-link",
    response_model=TokenResponse,
    summary="Verify magic link code and get tokens",
    description="Verify the 6-digit code sent to email and receive JWT tokens.",
)
async def verify_magic_link(
    request: VerifyMagicLinkRequest,
    db: DbSession,
) -> TokenResponse:
    """Verify magic link code and return JWT tokens.

    Validates the code and returns access/refresh tokens on success.
    The code is single-use and deleted after successful verification.

    Args:
        request: The verification request with email and code.
        db: The database session (injected).

    Returns:
        TokenResponse with access_token, refresh_token, and expiration info.

    Raises:
        HTTPException 401: If code is invalid or expired.
    """
    user_repo = UserRepository(db)

    # Verify the code first
    is_valid = await magic_link_service.verify_code(request.email, request.code)

    if not is_valid:
        raise INVALID_CODE_ERROR

    # Look up user by email
    user = await user_repo.get_by_email(request.email)

    if user is None or not user.is_active:
        raise INVALID_CODE_ERROR

    # Mark email as verified (first successful magic link login verifies email)
    if not user.email_verified:
        await user_repo.mark_email_verified(user.id)

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
