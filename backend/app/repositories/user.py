"""User repository for data access operations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

if TYPE_CHECKING:
    from app.models.user import UserType


class UserRepository:
    """Repository for User CRUD operations.

    Implements the repository pattern for user data access,
    providing an abstraction layer over SQLAlchemy operations.

    All methods use async patterns for non-blocking database access.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: An async SQLAlchemy session.
        """
        self._session = session

    async def create(self, user_data: UserCreate, password_hash: str) -> User:
        """Create a new user in the database (legacy, with password).

        DEPRECATED: Use create_passwordless() for new users.

        Args:
            user_data: The user creation data (email, names, user_type).
            password_hash: The pre-hashed password (never store plain text!).

        Returns:
            The newly created User instance.

        Note:
            The password field in user_data is ignored - only the
            pre-hashed password_hash parameter is stored.
        """
        user = User(
            email=user_data.email.lower(),  # Store email in lowercase
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            user_type=user_data.user_type,
            email_verified=False,
            is_active=True,
        )
        self._session.add(user)
        await self._session.flush()  # Flush to get the generated ID
        return user

    async def create_passwordless(self, user_data: UserCreate) -> User:
        """Create a new user without a password (passwordless auth).

        Args:
            user_data: The user creation data (email, names, user_type).

        Returns:
            The newly created User instance.
        """
        user = User(
            email=user_data.email.lower(),  # Store email in lowercase
            password_hash=None,  # No password for passwordless auth
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            user_type=user_data.user_type,
            email_verified=False,
            is_active=True,
        )
        self._session.add(user)
        await self._session.flush()  # Flush to get the generated ID
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get a user by their UUID.

        Args:
            user_id: The user's unique identifier.

        Returns:
            The User if found, None otherwise.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by their email address.

        Performs case-insensitive email lookup.

        Args:
            email: The email address to search for.

        Returns:
            The User if found, None otherwise.
        """
        stmt = select(User).where(func.lower(User.email) == email.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """Check if a user exists with the given email.

        More efficient than get_by_email when you only need to check existence.
        Performs case-insensitive email lookup.

        Args:
            email: The email address to check.

        Returns:
            True if a user exists with this email, False otherwise.
        """
        stmt = select(User.id).where(func.lower(User.email) == email.lower()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update(self, user_id: UUID, update_data: UserUpdate) -> User | None:
        """Update a user's information.

        Only updates fields that are explicitly set in update_data.
        Fields set to None in update_data are ignored (not set to null).

        Args:
            user_id: The user's unique identifier.
            update_data: The fields to update.

        Returns:
            The updated User if found, None if user doesn't exist.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        # Update only provided fields (exclude_unset=True)
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user, field, value)

        await self._session.flush()
        return user

    async def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete a user by setting is_active to False.

        Does not remove the user from the database. The user can be
        reactivated later if needed.

        Args:
            user_id: The user's unique identifier.

        Returns:
            True if the user was found and marked inactive,
            False if the user doesn't exist.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return False

        user.is_active = False
        await self._session.flush()
        return True

    async def update_user_type(self, user_id: UUID, user_type: UserType) -> User | None:
        """Update a user's user_type field.

        Used when a user becomes a host (changes from CLIENT to BOTH).

        Args:
            user_id: The user's unique identifier.
            user_type: The new user type to set.

        Returns:
            The updated User if found, None if user doesn't exist.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        user.user_type = user_type
        await self._session.flush()
        return user

    async def mark_email_verified(self, user_id: UUID) -> User | None:
        """Mark a user's email as verified.

        Called after successful magic link verification.

        Args:
            user_id: The user's unique identifier.

        Returns:
            The updated User if found, None if user doesn't exist.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        user.email_verified = True
        await self._session.flush()
        return user

    async def update_avatar(
        self,
        user_id: UUID,
        avatar_url: str,
        avatar_thumbnail_url: str,
    ) -> User | None:
        """Update a user's avatar URLs.

        Args:
            user_id: The user's unique identifier.
            avatar_url: URL to the main avatar image.
            avatar_thumbnail_url: URL to the thumbnail avatar image.

        Returns:
            The updated User if found, None if user doesn't exist.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        user.avatar_url = avatar_url
        user.avatar_thumbnail_url = avatar_thumbnail_url
        await self._session.flush()
        return user

    async def delete_avatar(self, user_id: UUID) -> User | None:
        """Remove a user's avatar URLs.

        Args:
            user_id: The user's unique identifier.

        Returns:
            The updated User if found, None if user doesn't exist.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        user.avatar_url = None
        user.avatar_thumbnail_url = None
        await self._session.flush()
        return user
