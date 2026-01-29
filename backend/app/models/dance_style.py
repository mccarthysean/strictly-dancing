"""Dance style database model."""

import enum

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DanceStyleCategory(str, enum.Enum):
    """Dance style category enumeration."""

    LATIN = "latin"
    BALLROOM = "ballroom"
    SWING = "swing"
    SOCIAL = "social"
    OTHER = "other"


class DanceStyle(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Dance style model.

    Represents a dance style available on the Strictly Dancing platform.
    Dance styles are categorized and have unique slugs for URL-friendly lookups.

    Attributes:
        id: UUID primary key
        name: Display name of the dance style (e.g., "Salsa")
        slug: URL-friendly identifier (e.g., "salsa")
        category: Category of the dance style (Latin, Ballroom, etc.)
        description: Optional description of the dance style
        created_at: When the record was created
        updated_at: When the record was last updated
    """

    __tablename__ = "dance_styles"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    category: Mapped[DanceStyleCategory] = mapped_column(
        ENUM(DanceStyleCategory, name="dance_style_category_enum", create_type=True),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<DanceStyle(id={self.id}, name={self.name}, category={self.category})>"
