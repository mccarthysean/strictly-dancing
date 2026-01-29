"""Verification document database model."""

import enum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentType(str, enum.Enum):
    """Types of verification documents."""

    GOVERNMENT_ID = "government_id"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    OTHER = "other"


class VerificationDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Verification document model.

    Stores documents submitted by hosts for identity verification.
    Each submission creates a new document record and updates the
    host profile's verification_status to PENDING.

    Attributes:
        id: UUID primary key
        host_profile_id: Foreign key to host_profiles table
        document_type: Type of document submitted
        document_url: URL/path to stored document (S3 or local)
        document_number: Masked document number (e.g., "***1234")
        notes: Optional notes from the host
        reviewer_notes: Internal notes from reviewer (admin)
        reviewed_at: When the document was reviewed
        reviewed_by: UUID of admin who reviewed
        created_at: When the document was submitted
        updated_at: When the record was last updated
    """

    __tablename__ = "verification_documents"

    # Foreign key to host profile
    host_profile_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("host_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Document information
    document_type: Mapped[DocumentType] = mapped_column(
        ENUM(DocumentType, name="document_type_enum", create_type=True),
        nullable=False,
    )
    document_url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )
    document_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Review information
    reviewer_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    reviewed_at: Mapped[str | None] = mapped_column(
        nullable=True,
    )
    reviewed_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )

    # Relationship to HostProfile
    host_profile = relationship("HostProfile", backref="verification_documents")

    def __repr__(self) -> str:
        return (
            f"<VerificationDocument(id={self.id}, "
            f"host_profile_id={self.host_profile_id}, "
            f"type={self.document_type})>"
        )
