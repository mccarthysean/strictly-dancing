"""Pydantic schemas for host verification."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.host_profile import VerificationStatus
from app.models.verification_document import DocumentType


class SubmitVerificationRequest(BaseModel):
    """Request schema for submitting verification documents."""

    document_type: DocumentType = Field(
        ...,
        description="Type of document being submitted",
    )
    document_url: str | None = Field(
        None,
        description="URL/path to the uploaded document file",
        max_length=1024,
    )
    document_number: str | None = Field(
        None,
        description="Masked document number (e.g., last 4 digits)",
        max_length=50,
    )
    notes: str | None = Field(
        None,
        description="Optional notes from the host",
        max_length=2000,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_type": "government_id",
                "document_url": "https://storage.example.com/docs/id-123.jpg",
                "document_number": "***1234",
                "notes": "Front side of my driver's license",
            }
        }
    )


class VerificationDocumentResponse(BaseModel):
    """Response schema for a verification document."""

    id: str = Field(..., description="Document UUID")
    document_type: DocumentType = Field(..., description="Type of document")
    document_url: str | None = Field(None, description="URL to the document")
    document_number: str | None = Field(None, description="Masked document number")
    notes: str | None = Field(None, description="Notes from the host")
    reviewer_notes: str | None = Field(None, description="Notes from the reviewer")
    reviewed_at: datetime | None = Field(
        None, description="When the document was reviewed"
    )
    created_at: datetime = Field(..., description="When the document was submitted")

    model_config = ConfigDict(from_attributes=True)


class VerificationStatusResponse(BaseModel):
    """Response schema for verification status."""

    status: VerificationStatus = Field(..., description="Current verification status")
    can_submit: bool = Field(
        ...,
        description="Whether the host can submit new verification documents",
    )
    rejection_reason: str | None = Field(
        None,
        description="Reason for rejection if status is rejected",
    )
    documents: list[VerificationDocumentResponse] = Field(
        default_factory=list,
        description="List of submitted verification documents",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "pending",
                "can_submit": False,
                "rejection_reason": None,
                "documents": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "document_type": "government_id",
                        "document_url": "https://storage.example.com/docs/id-123.jpg",
                        "document_number": "***1234",
                        "notes": "Front side of my driver's license",
                        "reviewer_notes": None,
                        "reviewed_at": None,
                        "created_at": "2026-01-29T10:00:00Z",
                    }
                ],
            }
        }
    )


class SubmitVerificationResponse(BaseModel):
    """Response schema for successful verification submission."""

    success: bool = Field(..., description="Whether the submission was successful")
    document_id: str | None = Field(None, description="ID of the created document")
    message: str = Field(..., description="Status message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Verification documents submitted successfully. Please allow 1-3 business days for review.",
            }
        }
    )


class ApproveVerificationRequest(BaseModel):
    """Request schema for approving verification (admin only)."""

    notes: str | None = Field(
        None,
        description="Optional notes from the reviewer",
        max_length=2000,
    )


class RejectVerificationRequest(BaseModel):
    """Request schema for rejecting verification (admin only)."""

    reason: str = Field(
        ...,
        description="Reason for rejection",
        min_length=10,
        max_length=2000,
    )
