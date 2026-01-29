"""Unit tests for host verification functionality."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.host_profile import HostProfile, VerificationStatus
from app.models.verification_document import DocumentType, VerificationDocument
from app.services.verification import (
    VerificationResult,
    VerificationService,
    VerificationStatusResult,
)


class TestVerificationDocument:
    """Tests for VerificationDocument model."""

    def test_document_type_enum_values(self):
        """Document type enum has expected values."""
        assert DocumentType.GOVERNMENT_ID == "government_id"
        assert DocumentType.PASSPORT == "passport"
        assert DocumentType.DRIVERS_LICENSE == "drivers_license"
        assert DocumentType.OTHER == "other"

    def test_verification_document_fields(self):
        """VerificationDocument has expected fields."""
        doc = VerificationDocument(
            id=str(uuid4()),
            host_profile_id=str(uuid4()),
            document_type=DocumentType.GOVERNMENT_ID,
            document_url="https://example.com/doc.jpg",
            document_number="***1234",
            notes="Front side",
        )

        assert doc.document_type == DocumentType.GOVERNMENT_ID
        assert doc.document_url == "https://example.com/doc.jpg"
        assert doc.document_number == "***1234"
        assert doc.notes == "Front side"
        assert doc.reviewer_notes is None
        assert doc.reviewed_at is None
        assert doc.reviewed_by is None

    def test_verification_document_repr(self):
        """VerificationDocument has a valid string representation."""
        doc_id = str(uuid4())
        host_id = str(uuid4())
        doc = VerificationDocument(
            id=doc_id,
            host_profile_id=host_id,
            document_type=DocumentType.PASSPORT,
        )

        repr_str = repr(doc)
        assert "VerificationDocument" in repr_str
        assert doc_id in repr_str


class TestVerificationService:
    """Tests for VerificationService."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def verification_service(self, mock_session):
        """Create a VerificationService with mock session."""
        return VerificationService(mock_session)

    @pytest.fixture
    def mock_host_profile(self):
        """Create a mock host profile."""
        profile = MagicMock(spec=HostProfile)
        profile.id = str(uuid4())
        profile.user_id = str(uuid4())
        profile.verification_status = VerificationStatus.UNVERIFIED
        return profile

    @pytest.mark.asyncio
    async def test_submit_verification_success(
        self, verification_service, mock_session, mock_host_profile
    ):
        """Submit verification creates document and updates status."""
        # Setup mock to return the profile
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_host_profile
        mock_session.execute.return_value = mock_result

        result = await verification_service.submit_verification(
            host_profile_id=UUID(mock_host_profile.id),
            document_type=DocumentType.GOVERNMENT_ID,
            document_url="https://example.com/doc.jpg",
            notes="Test submission",
        )

        assert result.success is True
        # Note: document_id is the actual ID from the VerificationDocument model
        # which gets a default UUID from UUIDPrimaryKeyMixin
        assert result.error_message is None

        # Verify profile status was updated
        assert mock_host_profile.verification_status == VerificationStatus.PENDING

        # Verify session.add was called with a document
        mock_session.add.assert_called_once()
        # Verify the added document is a VerificationDocument
        added_doc = mock_session.add.call_args[0][0]
        assert isinstance(added_doc, VerificationDocument)
        assert added_doc.document_type == DocumentType.GOVERNMENT_ID
        assert added_doc.document_url == "https://example.com/doc.jpg"

    @pytest.mark.asyncio
    async def test_submit_verification_profile_not_found(
        self, verification_service, mock_session
    ):
        """Submit verification fails if profile not found."""
        # Setup mock to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await verification_service.submit_verification(
            host_profile_id=uuid4(),
            document_type=DocumentType.PASSPORT,
        )

        assert result.success is False
        assert result.error_message == "Host profile not found"

    @pytest.mark.asyncio
    async def test_submit_verification_already_verified(
        self, verification_service, mock_session, mock_host_profile
    ):
        """Submit verification fails if already verified."""
        mock_host_profile.verification_status = VerificationStatus.VERIFIED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_host_profile
        mock_session.execute.return_value = mock_result

        result = await verification_service.submit_verification(
            host_profile_id=UUID(mock_host_profile.id),
            document_type=DocumentType.GOVERNMENT_ID,
        )

        assert result.success is False
        assert result.error_message == "Host is already verified"

    @pytest.mark.asyncio
    async def test_submit_verification_already_pending(
        self, verification_service, mock_session, mock_host_profile
    ):
        """Submit verification fails if already pending."""
        mock_host_profile.verification_status = VerificationStatus.PENDING

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_host_profile
        mock_session.execute.return_value = mock_result

        result = await verification_service.submit_verification(
            host_profile_id=UUID(mock_host_profile.id),
            document_type=DocumentType.GOVERNMENT_ID,
        )

        assert result.success is False
        assert "already pending" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_get_verification_status_not_found(
        self, verification_service, mock_session
    ):
        """Get verification status returns None if profile not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await verification_service.get_verification_status(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_verification_status_unverified(
        self, verification_service, mock_session, mock_host_profile
    ):
        """Get verification status for unverified host."""
        mock_host_profile.verification_status = VerificationStatus.UNVERIFIED

        # First call returns profile, second returns empty documents list
        mock_result_profile = MagicMock()
        mock_result_profile.scalar_one_or_none.return_value = mock_host_profile
        mock_result_docs = MagicMock()
        mock_result_docs.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_result_profile, mock_result_docs]

        result = await verification_service.get_verification_status(
            UUID(mock_host_profile.id)
        )

        assert result is not None
        assert result.status == VerificationStatus.UNVERIFIED
        assert result.can_submit is True
        assert result.documents == []

    @pytest.mark.asyncio
    async def test_get_verification_status_pending(
        self, verification_service, mock_session, mock_host_profile
    ):
        """Get verification status for pending host."""
        mock_host_profile.verification_status = VerificationStatus.PENDING

        mock_doc = MagicMock(spec=VerificationDocument)
        mock_doc.created_at = datetime.now()
        mock_doc.reviewer_notes = None

        mock_result_profile = MagicMock()
        mock_result_profile.scalar_one_or_none.return_value = mock_host_profile
        mock_result_docs = MagicMock()
        mock_result_docs.scalars.return_value.all.return_value = [mock_doc]

        mock_session.execute.side_effect = [mock_result_profile, mock_result_docs]

        result = await verification_service.get_verification_status(
            UUID(mock_host_profile.id)
        )

        assert result is not None
        assert result.status == VerificationStatus.PENDING
        assert result.can_submit is False  # Can't submit while pending

    @pytest.mark.asyncio
    async def test_approve_verification_success(
        self, verification_service, mock_session, mock_host_profile
    ):
        """Approve verification updates status to verified."""
        mock_host_profile.verification_status = VerificationStatus.PENDING

        mock_doc = MagicMock(spec=VerificationDocument)
        mock_doc.created_at = datetime.now()

        mock_result_profile = MagicMock()
        mock_result_profile.scalar_one_or_none.return_value = mock_host_profile
        mock_result_docs = MagicMock()
        mock_result_docs.scalars.return_value.all.return_value = [mock_doc]

        mock_session.execute.side_effect = [mock_result_profile, mock_result_docs]

        reviewer_id = uuid4()
        result = await verification_service.approve_verification(
            host_profile_id=UUID(mock_host_profile.id),
            reviewer_id=reviewer_id,
            reviewer_notes="Looks good!",
        )

        assert result.success is True
        assert mock_host_profile.verification_status == VerificationStatus.VERIFIED
        assert mock_doc.reviewer_notes == "Looks good!"

    @pytest.mark.asyncio
    async def test_reject_verification_success(
        self, verification_service, mock_session, mock_host_profile
    ):
        """Reject verification updates status and records reason."""
        mock_host_profile.verification_status = VerificationStatus.PENDING

        mock_doc = MagicMock(spec=VerificationDocument)
        mock_doc.created_at = datetime.now()

        mock_result_profile = MagicMock()
        mock_result_profile.scalar_one_or_none.return_value = mock_host_profile
        mock_result_docs = MagicMock()
        mock_result_docs.scalars.return_value.all.return_value = [mock_doc]

        mock_session.execute.side_effect = [mock_result_profile, mock_result_docs]

        reviewer_id = uuid4()
        rejection_reason = "Document image is blurry"

        result = await verification_service.reject_verification(
            host_profile_id=UUID(mock_host_profile.id),
            reviewer_id=reviewer_id,
            rejection_reason=rejection_reason,
        )

        assert result.success is True
        assert mock_host_profile.verification_status == VerificationStatus.REJECTED
        assert mock_doc.reviewer_notes == rejection_reason


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_success_result(self):
        """Create successful verification result."""
        result = VerificationResult(success=True, document_id="doc-123")

        assert result.success is True
        assert result.document_id == "doc-123"
        assert result.error_message is None

    def test_failure_result(self):
        """Create failed verification result."""
        result = VerificationResult(
            success=False,
            error_message="Host profile not found",
        )

        assert result.success is False
        assert result.document_id is None
        assert result.error_message == "Host profile not found"


class TestVerificationStatusResult:
    """Tests for VerificationStatusResult dataclass."""

    def test_status_result_verified(self):
        """Create verification status result for verified host."""
        result = VerificationStatusResult(
            status=VerificationStatus.VERIFIED,
            documents=[],
            can_submit=False,
        )

        assert result.status == VerificationStatus.VERIFIED
        assert result.can_submit is False
        assert result.rejection_reason is None

    def test_status_result_rejected(self):
        """Create verification status result for rejected host."""
        result = VerificationStatusResult(
            status=VerificationStatus.REJECTED,
            documents=[],
            can_submit=True,
            rejection_reason="Document unclear",
        )

        assert result.status == VerificationStatus.REJECTED
        assert result.can_submit is True
        assert result.rejection_reason == "Document unclear"


class TestVerificationSchemas:
    """Tests for verification Pydantic schemas."""

    def test_submit_verification_request_valid(self):
        """SubmitVerificationRequest with valid data."""
        from app.schemas.verification import SubmitVerificationRequest

        request = SubmitVerificationRequest(
            document_type=DocumentType.GOVERNMENT_ID,
            document_url="https://example.com/doc.jpg",
            document_number="***1234",
            notes="Front of ID",
        )

        assert request.document_type == DocumentType.GOVERNMENT_ID
        assert request.document_url == "https://example.com/doc.jpg"
        assert request.document_number == "***1234"
        assert request.notes == "Front of ID"

    def test_submit_verification_request_minimal(self):
        """SubmitVerificationRequest with minimal required fields."""
        from app.schemas.verification import SubmitVerificationRequest

        request = SubmitVerificationRequest(
            document_type=DocumentType.PASSPORT,
        )

        assert request.document_type == DocumentType.PASSPORT
        assert request.document_url is None
        assert request.document_number is None
        assert request.notes is None

    def test_verification_status_response(self):
        """VerificationStatusResponse structure."""
        from app.schemas.verification import VerificationStatusResponse

        response = VerificationStatusResponse(
            status=VerificationStatus.PENDING,
            can_submit=False,
            rejection_reason=None,
            documents=[],
        )

        assert response.status == VerificationStatus.PENDING
        assert response.can_submit is False
        assert response.rejection_reason is None
        assert response.documents == []

    def test_submit_verification_response(self):
        """SubmitVerificationResponse structure."""
        from app.schemas.verification import SubmitVerificationResponse

        response = SubmitVerificationResponse(
            success=True,
            document_id="doc-123",
            message="Submitted successfully",
        )

        assert response.success is True
        assert response.document_id == "doc-123"
        assert response.message == "Submitted successfully"

    def test_approve_verification_request(self):
        """ApproveVerificationRequest with notes."""
        from app.schemas.verification import ApproveVerificationRequest

        request = ApproveVerificationRequest(notes="All documents verified")

        assert request.notes == "All documents verified"

    def test_reject_verification_request_validates_reason_length(self):
        """RejectVerificationRequest requires minimum reason length."""
        from pydantic import ValidationError

        from app.schemas.verification import RejectVerificationRequest

        # Valid - 10+ chars
        request = RejectVerificationRequest(reason="Document is unclear")
        assert len(request.reason) >= 10

        # Invalid - less than 10 chars
        with pytest.raises(ValidationError):
            RejectVerificationRequest(reason="Too short")


class TestVerificationEndpoints:
    """Tests for verification API endpoints."""

    @pytest.fixture
    def mock_current_user(self):
        """Create a mock current user."""
        from app.models.user import User

        user = MagicMock(spec=User)
        user.id = str(uuid4())
        user.email = "host@example.com"
        user.first_name = "Test"
        user.last_name = "Host"
        user.is_active = True
        return user

    @pytest.mark.asyncio
    async def test_submit_verification_endpoint_exists(self):
        """POST /api/v1/hosts/verification/submit endpoint exists."""
        # Get the route from the router
        routes = [r for r in app.routes if hasattr(r, "path")]
        paths = [r.path for r in routes]

        assert "/api/v1/hosts/verification/submit" in paths

    @pytest.mark.asyncio
    async def test_get_verification_status_endpoint_exists(self):
        """GET /api/v1/hosts/verification/status endpoint exists."""
        routes = [r for r in app.routes if hasattr(r, "path")]
        paths = [r.path for r in routes]

        assert "/api/v1/hosts/verification/status" in paths

    @pytest.mark.asyncio
    async def test_submit_verification_requires_auth(self):
        """Submit verification endpoint requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/hosts/verification/submit",
                json={"document_type": "government_id"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_verification_status_requires_auth(self):
        """Get verification status endpoint requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/hosts/verification/status")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestVerificationIntegration:
    """Integration tests for verification workflow."""

    @pytest.mark.asyncio
    async def test_verification_workflow_unverified_to_verified(
        self,
    ):
        """Test complete verification workflow."""
        from app.services.verification import VerificationService

        # Create mock session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        # Create mock profile that starts unverified
        mock_profile = MagicMock(spec=HostProfile)
        mock_profile.id = str(uuid4())
        mock_profile.verification_status = VerificationStatus.UNVERIFIED

        # Setup mock execute to return profile
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile

        mock_docs_result = MagicMock()
        mock_docs_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            mock_result,  # For submit_verification _get_host_profile
        ]

        service = VerificationService(mock_session)

        # Step 1: Submit verification
        submit_result = await service.submit_verification(
            host_profile_id=UUID(mock_profile.id),
            document_type=DocumentType.GOVERNMENT_ID,
            document_url="https://example.com/id.jpg",
        )

        assert submit_result.success is True
        assert mock_profile.verification_status == VerificationStatus.PENDING

        # Step 2: Approve verification
        mock_doc = MagicMock(spec=VerificationDocument)
        mock_doc.created_at = datetime.now()

        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = mock_profile
        mock_docs_result2 = MagicMock()
        mock_docs_result2.scalars.return_value.all.return_value = [mock_doc]

        mock_session.execute.side_effect = [mock_result2, mock_docs_result2]

        approve_result = await service.approve_verification(
            host_profile_id=UUID(mock_profile.id),
            reviewer_id=uuid4(),
        )

        assert approve_result.success is True
        assert mock_profile.verification_status == VerificationStatus.VERIFIED

    @pytest.mark.asyncio
    async def test_verification_workflow_rejected_can_resubmit(self):
        """Test that rejected hosts can resubmit verification."""
        from app.services.verification import VerificationService

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        # Create mock profile with REJECTED status
        mock_profile = MagicMock(spec=HostProfile)
        mock_profile.id = str(uuid4())
        mock_profile.verification_status = VerificationStatus.REJECTED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile

        mock_session.execute.return_value = mock_result

        service = VerificationService(mock_session)

        # Rejected hosts can submit new verification
        submit_result = await service.submit_verification(
            host_profile_id=UUID(mock_profile.id),
            document_type=DocumentType.PASSPORT,
        )

        assert submit_result.success is True
        assert mock_profile.verification_status == VerificationStatus.PENDING
