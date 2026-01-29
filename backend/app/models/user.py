"""User database model."""

import enum

from sqlalchemy import Boolean, Index, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserType(str, enum.Enum):
    """User type enumeration."""

    CLIENT = "client"
    HOST = "host"
    BOTH = "both"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User account model.

    Represents a user in the Strictly Dancing platform.
    Users can be clients, hosts, or both.

    Attributes:
        id: UUID primary key
        email: Unique email address (case-insensitive)
        password_hash: Hashed password
        first_name: User's first name
        last_name: User's last name
        user_type: Type of user (client, host, or both)
        email_verified: Whether email has been verified
        is_active: Whether account is active
        created_at: When the account was created
        updated_at: When the account was last updated
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    user_type: Mapped[UserType] = mapped_column(
        ENUM(UserType, name="user_type_enum", create_type=True),
        default=UserType.CLIENT,
        nullable=False,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Create a case-insensitive index on email for faster lookups
    __table_args__ = (
        Index(
            "ix_users_email_lower",
            email,
            postgresql_ops={"email": "varchar_pattern_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, type={self.user_type})>"
