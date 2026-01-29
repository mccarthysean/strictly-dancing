"""Pydantic schemas for Stripe Connect operations."""

from pydantic import BaseModel, Field, HttpUrl


class StripeOnboardRequest(BaseModel):
    """Request body for initiating Stripe Connect onboarding."""

    refresh_url: HttpUrl = Field(
        ...,
        description="URL to redirect to if the onboarding link expires",
    )
    return_url: HttpUrl = Field(
        ...,
        description="URL to redirect to after onboarding completion",
    )


class StripeOnboardResponse(BaseModel):
    """Response for Stripe Connect onboarding initiation."""

    account_id: str = Field(
        ...,
        description="The Stripe Connect account ID",
    )
    onboarding_url: str = Field(
        ...,
        description="URL to redirect the host to for onboarding",
    )


class StripeAccountStatusResponse(BaseModel):
    """Response with Stripe account status details."""

    account_id: str = Field(
        ...,
        description="The Stripe Connect account ID",
    )
    status: str = Field(
        ...,
        description="Account status: not_created, pending, active, restricted, or rejected",
    )
    charges_enabled: bool = Field(
        ...,
        description="Whether the account can accept charges",
    )
    payouts_enabled: bool = Field(
        ...,
        description="Whether the account can receive payouts",
    )
    details_submitted: bool = Field(
        ...,
        description="Whether onboarding details have been submitted",
    )
    requirements_due: list[str] = Field(
        default_factory=list,
        description="List of requirements that need to be fulfilled",
    )


class StripeDashboardLinkResponse(BaseModel):
    """Response with link to Stripe Express Dashboard."""

    login_url: str = Field(
        ...,
        description="URL to the Stripe Express Dashboard",
    )
