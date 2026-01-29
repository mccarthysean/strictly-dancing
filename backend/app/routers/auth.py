"""Authentication router for user registration, login, and token management."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserCreate, UserResponse
from app.services.password import password_service

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
