"""Verification service for host identity verification."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host_profile import HostProfile, VerificationStatus
from app.models.verification_document import DocumentType, VerificationDocument


@dataclass
class VerificationResult:
    """Result of a verification operation."""

    success: bool
    document_id: str | None = None
    error_message: str | None = None


@dataclass
class VerificationStatusResult:
    """Result of getting verification status."""

    status: VerificationStatus
    documents: list[VerificationDocument]
    can_submit: bool
    rejection_reason: str | None = None


class VerificationService:
    """Service for managing host verification.

    Handles submission of verification documents and status tracking.
    In a production system, this would integrate with an external
    ID verification service (e.g., Stripe Identity, Jumio, Onfido).

    Attributes:
        session: The async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the verification service.

        Args:
            session: An async SQLAlchemy session.
        """
        self._session = session

    async def submit_verification(
        self,
        host_profile_id: UUID,
        document_type: DocumentType,
        document_url: str | None = None,
        document_number: str | None = None,
        notes: str | None = None,
    ) -> VerificationResult:
        """Submit verification documents for a host profile.

        Creates a new verification document record and updates the
        host profile's verification_status to PENDING.

        Args:
            host_profile_id: The host profile's unique identifier.
            document_type: Type of document being submitted.
            document_url: URL/path to the uploaded document file.
            document_number: Masked document ID (e.g., last 4 digits).
            notes: Optional notes from the host.

        Returns:
            VerificationResult with success status and document ID.
        """
        # Verify host profile exists
        profile = await self._get_host_profile(host_profile_id)
        if profile is None:
            return VerificationResult(
                success=False,
                error_message="Host profile not found",
            )

        # Check if already verified
        if profile.verification_status == VerificationStatus.VERIFIED:
            return VerificationResult(
                success=False,
                error_message="Host is already verified",
            )

        # Check if already has pending verification
        if profile.verification_status == VerificationStatus.PENDING:
            return VerificationResult(
                success=False,
                error_message="Verification already pending. Please wait for review.",
            )

        # Create verification document
        document = VerificationDocument(
            host_profile_id=str(host_profile_id),
            document_type=document_type,
            document_url=document_url,
            document_number=document_number,
            notes=notes,
        )
        self._session.add(document)

        # Update host profile status to PENDING
        profile.verification_status = VerificationStatus.PENDING

        await self._session.flush()

        return VerificationResult(
            success=True,
            document_id=document.id,
        )

    async def get_verification_status(
        self,
        host_profile_id: UUID,
    ) -> VerificationStatusResult | None:
        """Get the verification status for a host profile.

        Args:
            host_profile_id: The host profile's unique identifier.

        Returns:
            VerificationStatusResult with current status and documents,
            or None if profile not found.
        """
        profile = await self._get_host_profile(host_profile_id)
        if profile is None:
            return None

        # Get all documents for this profile
        documents = await self._get_documents(host_profile_id)

        # Determine if host can submit new verification
        can_submit = profile.verification_status in (
            VerificationStatus.UNVERIFIED,
            VerificationStatus.REJECTED,
        )

        # Get rejection reason if rejected
        rejection_reason = None
        if profile.verification_status == VerificationStatus.REJECTED and documents:
            # Get the most recent document's reviewer notes
            latest_doc = max(documents, key=lambda d: d.created_at)
            rejection_reason = latest_doc.reviewer_notes

        return VerificationStatusResult(
            status=profile.verification_status,
            documents=documents,
            can_submit=can_submit,
            rejection_reason=rejection_reason,
        )

    async def approve_verification(
        self,
        host_profile_id: UUID,
        reviewer_id: UUID,
        reviewer_notes: str | None = None,
    ) -> VerificationResult:
        """Approve a host's verification (admin action).

        Updates the host profile's verification_status to VERIFIED
        and records the reviewer information.

        Args:
            host_profile_id: The host profile's unique identifier.
            reviewer_id: UUID of the admin approving.
            reviewer_notes: Optional notes from the reviewer.

        Returns:
            VerificationResult with success status.
        """
        profile = await self._get_host_profile(host_profile_id)
        if profile is None:
            return VerificationResult(
                success=False,
                error_message="Host profile not found",
            )

        if profile.verification_status != VerificationStatus.PENDING:
            return VerificationResult(
                success=False,
                error_message="Verification is not pending",
            )

        # Update most recent document with review info
        documents = await self._get_documents(host_profile_id)
        if documents:
            latest_doc = max(documents, key=lambda d: d.created_at)
            latest_doc.reviewed_at = datetime.now(UTC).isoformat()
            latest_doc.reviewed_by = str(reviewer_id)
            latest_doc.reviewer_notes = reviewer_notes

        # Update profile status
        profile.verification_status = VerificationStatus.VERIFIED

        await self._session.flush()

        return VerificationResult(success=True)

    async def reject_verification(
        self,
        host_profile_id: UUID,
        reviewer_id: UUID,
        rejection_reason: str,
    ) -> VerificationResult:
        """Reject a host's verification (admin action).

        Updates the host profile's verification_status to REJECTED
        and records the rejection reason.

        Args:
            host_profile_id: The host profile's unique identifier.
            reviewer_id: UUID of the admin rejecting.
            rejection_reason: Reason for rejection.

        Returns:
            VerificationResult with success status.
        """
        profile = await self._get_host_profile(host_profile_id)
        if profile is None:
            return VerificationResult(
                success=False,
                error_message="Host profile not found",
            )

        if profile.verification_status != VerificationStatus.PENDING:
            return VerificationResult(
                success=False,
                error_message="Verification is not pending",
            )

        # Update most recent document with review info
        documents = await self._get_documents(host_profile_id)
        if documents:
            latest_doc = max(documents, key=lambda d: d.created_at)
            latest_doc.reviewed_at = datetime.now(UTC).isoformat()
            latest_doc.reviewed_by = str(reviewer_id)
            latest_doc.reviewer_notes = rejection_reason

        # Update profile status
        profile.verification_status = VerificationStatus.REJECTED

        await self._session.flush()

        return VerificationResult(success=True)

    async def _get_host_profile(self, host_profile_id: UUID) -> HostProfile | None:
        """Get a host profile by ID.

        Args:
            host_profile_id: The host profile's unique identifier.

        Returns:
            The HostProfile if found, None otherwise.
        """
        stmt = select(HostProfile).where(HostProfile.id == str(host_profile_id))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_documents(self, host_profile_id: UUID) -> list[VerificationDocument]:
        """Get all verification documents for a host profile.

        Args:
            host_profile_id: The host profile's unique identifier.

        Returns:
            List of VerificationDocument records.
        """
        stmt = (
            select(VerificationDocument)
            .where(VerificationDocument.host_profile_id == str(host_profile_id))
            .order_by(VerificationDocument.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


def get_verification_service(session: AsyncSession) -> VerificationService:
    """Factory function to create a VerificationService instance.

    Args:
        session: An async SQLAlchemy session.

    Returns:
        A new VerificationService instance.
    """
    return VerificationService(session)
