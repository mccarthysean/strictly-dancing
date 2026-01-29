"""Host dance style junction model."""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class HostDanceStyle(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Host dance style junction model.

    Represents the many-to-many relationship between hosts and dance styles,
    with an additional skill_level attribute indicating the host's proficiency
    in that dance style.

    Attributes:
        id: UUID primary key
        host_profile_id: Foreign key to host_profiles table
        dance_style_id: Foreign key to dance_styles table
        skill_level: Host's skill level in this dance style (1-5)
        created_at: When the record was created
        updated_at: When the record was last updated
    """

    __tablename__ = "host_dance_styles"

    # Foreign key to host profile
    host_profile_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("host_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key to dance style
    dance_style_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("dance_styles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Skill level (1-5)
    skill_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    # Table constraints
    __table_args__ = (
        # Unique constraint on (host_profile_id, dance_style_id) pair
        UniqueConstraint(
            "host_profile_id",
            "dance_style_id",
            name="uq_host_dance_style_host_profile_dance_style",
        ),
        # Check constraint for skill_level range (1-5)
        CheckConstraint(
            "skill_level >= 1 AND skill_level <= 5",
            name="ck_host_dance_style_skill_level_range",
        ),
    )

    # Relationships with cascade delete configured via foreign key ondelete
    host_profile = relationship(
        "HostProfile",
        backref="dance_styles",
        lazy="joined",
    )
    dance_style = relationship(
        "DanceStyle",
        backref="host_profiles",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<HostDanceStyle(host_profile_id={self.host_profile_id}, dance_style_id={self.dance_style_id}, skill_level={self.skill_level})>"
