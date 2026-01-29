"""Stripe Connect service for host onboarding and payments."""

from dataclasses import dataclass
from enum import StrEnum

import stripe

from app.core.config import get_settings


class StripeAccountStatus(StrEnum):
    """Status of a Stripe Connect account."""

    NOT_CREATED = "not_created"
    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    REJECTED = "rejected"


@dataclass
class AccountStatus:
    """Stripe account status details."""

    account_id: str
    status: StripeAccountStatus
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    requirements_due: list[str]


class StripeService:
    """Service for Stripe Connect operations.

    Handles host onboarding with Stripe Connect Express accounts,
    payment processing, and account management.
    """

    def __init__(self, secret_key: str | None = None) -> None:
        """Initialize the Stripe service.

        Args:
            secret_key: Stripe secret API key. If not provided,
                       uses the key from application settings.
        """
        self._secret_key = secret_key or get_settings().stripe_secret_key
        if self._secret_key:
            stripe.api_key = self._secret_key

    def _ensure_api_key(self) -> None:
        """Ensure Stripe API key is configured.

        Raises:
            ValueError: If Stripe API key is not configured.
        """
        if not self._secret_key:
            raise ValueError("Stripe API key is not configured")
        stripe.api_key = self._secret_key

    async def create_connect_account(
        self,
        email: str,
        country: str = "US",
        business_type: str = "individual",
    ) -> str:
        """Create a new Stripe Connect Express account.

        Creates a Stripe Connect account for a host to receive payments.
        Uses Express account type for simplified onboarding.

        Args:
            email: The host's email address.
            country: Two-letter ISO country code (default US).
            business_type: Business type - 'individual' or 'company'.

        Returns:
            The Stripe Connect account ID.

        Raises:
            ValueError: If Stripe API key is not configured.
            stripe.StripeError: If account creation fails.
        """
        self._ensure_api_key()

        # Create Express account for simplified onboarding
        account = stripe.Account.create(
            type="express",
            country=country,
            email=email,
            business_type=business_type,
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
            settings={
                "payouts": {
                    "schedule": {
                        "interval": "daily",
                    },
                },
            },
        )

        return account.id

    async def create_account_link(
        self,
        account_id: str,
        refresh_url: str,
        return_url: str,
    ) -> str:
        """Create an account link for Connect onboarding.

        Generates a URL for the host to complete their Stripe onboarding
        through the hosted Connect Onboarding flow.

        Args:
            account_id: The Stripe Connect account ID.
            refresh_url: URL to redirect to if the link expires.
            return_url: URL to redirect to after onboarding.

        Returns:
            The onboarding URL for the host to visit.

        Raises:
            ValueError: If Stripe API key is not configured.
            stripe.StripeError: If link creation fails.
        """
        self._ensure_api_key()

        account_link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type="account_onboarding",
        )

        return account_link.url

    async def get_account_status(self, account_id: str) -> AccountStatus:
        """Get the status of a Stripe Connect account.

        Retrieves the current status and capabilities of a connected account.

        Args:
            account_id: The Stripe Connect account ID.

        Returns:
            AccountStatus with current status details.

        Raises:
            ValueError: If Stripe API key is not configured.
            stripe.StripeError: If account retrieval fails.
        """
        self._ensure_api_key()

        account = stripe.Account.retrieve(account_id)

        # Determine overall status
        if account.charges_enabled and account.payouts_enabled:
            status = StripeAccountStatus.ACTIVE
        elif account.details_submitted:
            # Account submitted but not fully enabled
            if hasattr(account, "requirements") and account.requirements:
                if account.requirements.get("disabled_reason"):
                    status = StripeAccountStatus.REJECTED
                elif account.requirements.get("currently_due"):
                    status = StripeAccountStatus.RESTRICTED
                else:
                    status = StripeAccountStatus.PENDING
            else:
                status = StripeAccountStatus.PENDING
        else:
            status = StripeAccountStatus.PENDING

        # Get requirements that are currently due
        requirements_due = []
        if hasattr(account, "requirements") and account.requirements:
            requirements_due = account.requirements.get("currently_due", []) or []

        return AccountStatus(
            account_id=account.id,
            status=status,
            charges_enabled=bool(account.charges_enabled),
            payouts_enabled=bool(account.payouts_enabled),
            details_submitted=bool(account.details_submitted),
            requirements_due=list(requirements_due),
        )

    async def create_payment_intent(
        self,
        amount_cents: int,
        currency: str = "usd",
        connected_account_id: str | None = None,
        platform_fee_cents: int = 0,
        metadata: dict[str, str] | None = None,
        capture_method: str = "manual",
    ) -> tuple[str, str]:
        """Create a PaymentIntent for booking payment.

        Creates a PaymentIntent that authorizes but doesn't capture
        the payment until the session is completed.

        Args:
            amount_cents: Total amount in cents.
            currency: Three-letter ISO currency code.
            connected_account_id: Stripe account ID to receive payment.
            platform_fee_cents: Platform fee to deduct in cents.
            metadata: Additional metadata for the payment.
            capture_method: 'manual' for auth-and-capture, 'automatic' for immediate.

        Returns:
            Tuple of (payment_intent_id, client_secret).

        Raises:
            ValueError: If Stripe API key is not configured.
            stripe.StripeError: If payment intent creation fails.
        """
        self._ensure_api_key()

        create_params: dict = {
            "amount": amount_cents,
            "currency": currency,
            "capture_method": capture_method,
            "metadata": metadata or {},
        }

        # If we have a connected account, set up the transfer
        if connected_account_id:
            create_params["transfer_data"] = {
                "destination": connected_account_id,
            }
            if platform_fee_cents > 0:
                create_params["application_fee_amount"] = platform_fee_cents

        payment_intent = stripe.PaymentIntent.create(**create_params)

        return payment_intent.id, payment_intent.client_secret

    async def capture_payment_intent(self, payment_intent_id: str) -> bool:
        """Capture a previously authorized PaymentIntent.

        Args:
            payment_intent_id: The PaymentIntent ID to capture.

        Returns:
            True if capture was successful.

        Raises:
            ValueError: If Stripe API key is not configured.
            stripe.StripeError: If capture fails.
        """
        self._ensure_api_key()

        payment_intent = stripe.PaymentIntent.capture(payment_intent_id)
        return payment_intent.status == "succeeded"

    async def cancel_payment_intent(self, payment_intent_id: str) -> bool:
        """Cancel a PaymentIntent and release authorization.

        Args:
            payment_intent_id: The PaymentIntent ID to cancel.

        Returns:
            True if cancellation was successful.

        Raises:
            ValueError: If Stripe API key is not configured.
            stripe.StripeError: If cancellation fails.
        """
        self._ensure_api_key()

        payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)
        return payment_intent.status == "canceled"

    async def create_transfer(
        self,
        amount_cents: int,
        destination_account_id: str,
        source_transaction: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Create a transfer to a connected account.

        Transfers funds from the platform to a connected account
        after a booking session is completed.

        Args:
            amount_cents: Amount to transfer in cents.
            destination_account_id: Stripe Connect account ID to receive funds.
            source_transaction: Optional source transaction (charge/payment_intent).
            metadata: Optional metadata for the transfer.

        Returns:
            The Stripe Transfer ID.

        Raises:
            ValueError: If Stripe API key is not configured.
            stripe.StripeError: If transfer creation fails.
        """
        self._ensure_api_key()

        create_params: dict = {
            "amount": amount_cents,
            "currency": "usd",
            "destination": destination_account_id,
            "metadata": metadata or {},
        }

        if source_transaction:
            create_params["source_transaction"] = source_transaction

        transfer = stripe.Transfer.create(**create_params)
        return transfer.id


# Singleton instance
stripe_service = StripeService()
