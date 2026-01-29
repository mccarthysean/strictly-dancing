"""Unit tests for Stripe Connect service."""

from unittest.mock import MagicMock, patch

import pytest
import stripe

from app.services.stripe import (
    AccountStatus,
    StripeAccountStatus,
    StripeService,
)


class TestStripeServiceInit:
    """Tests for StripeService initialization."""

    def test_init_with_provided_key(self):
        """Service should use provided API key."""
        service = StripeService(secret_key="sk_test_123")
        assert service._secret_key == "sk_test_123"

    def test_init_without_key_uses_settings(self):
        """Service should use settings if no key provided."""
        with patch("app.services.stripe.get_settings") as mock_settings:
            mock_settings.return_value.stripe_secret_key = "sk_from_settings"
            service = StripeService()
            assert service._secret_key == "sk_from_settings"

    def test_ensure_api_key_raises_without_key(self):
        """Service should raise ValueError if no API key configured."""
        service = StripeService(secret_key="")
        with pytest.raises(ValueError, match="not configured"):
            service._ensure_api_key()

    def test_ensure_api_key_sets_stripe_api_key(self):
        """Service should set stripe.api_key when ensured."""
        service = StripeService(secret_key="sk_test_123")
        service._ensure_api_key()
        assert stripe.api_key == "sk_test_123"


class TestCreateConnectAccount:
    """Tests for create_connect_account method."""

    @pytest.mark.asyncio
    async def test_create_connect_account_success(self):
        """Should create Express account and return account ID."""
        service = StripeService(secret_key="sk_test_123")

        mock_account = MagicMock()
        mock_account.id = "acct_123test"

        with patch.object(stripe.Account, "create", return_value=mock_account):
            account_id = await service.create_connect_account(
                email="host@example.com",
            )

            assert account_id == "acct_123test"

    @pytest.mark.asyncio
    async def test_create_connect_account_with_country(self):
        """Should create account with specified country."""
        service = StripeService(secret_key="sk_test_123")

        mock_account = MagicMock()
        mock_account.id = "acct_uk123"

        with patch.object(stripe.Account, "create", return_value=mock_account) as mock:
            await service.create_connect_account(
                email="host@example.com",
                country="GB",
            )

            mock.assert_called_once()
            call_kwargs = mock.call_args[1]
            assert call_kwargs["country"] == "GB"

    @pytest.mark.asyncio
    async def test_create_connect_account_with_business_type(self):
        """Should create account with specified business type."""
        service = StripeService(secret_key="sk_test_123")

        mock_account = MagicMock()
        mock_account.id = "acct_co123"

        with patch.object(stripe.Account, "create", return_value=mock_account) as mock:
            await service.create_connect_account(
                email="company@example.com",
                business_type="company",
            )

            mock.assert_called_once()
            call_kwargs = mock.call_args[1]
            assert call_kwargs["business_type"] == "company"

    @pytest.mark.asyncio
    async def test_create_connect_account_without_api_key(self):
        """Should raise ValueError if no API key."""
        service = StripeService(secret_key="")

        with pytest.raises(ValueError, match="not configured"):
            await service.create_connect_account(email="host@example.com")

    @pytest.mark.asyncio
    async def test_create_connect_account_creates_express_type(self):
        """Should create Express account type for simplified onboarding."""
        service = StripeService(secret_key="sk_test_123")

        mock_account = MagicMock()
        mock_account.id = "acct_express"

        with patch.object(stripe.Account, "create", return_value=mock_account) as mock:
            await service.create_connect_account(email="host@example.com")

            mock.assert_called_once()
            call_kwargs = mock.call_args[1]
            assert call_kwargs["type"] == "express"

    @pytest.mark.asyncio
    async def test_create_connect_account_requests_capabilities(self):
        """Should request card_payments and transfers capabilities."""
        service = StripeService(secret_key="sk_test_123")

        mock_account = MagicMock()
        mock_account.id = "acct_cap"

        with patch.object(stripe.Account, "create", return_value=mock_account) as mock:
            await service.create_connect_account(email="host@example.com")

            mock.assert_called_once()
            call_kwargs = mock.call_args[1]
            assert "capabilities" in call_kwargs
            assert call_kwargs["capabilities"]["card_payments"]["requested"] is True
            assert call_kwargs["capabilities"]["transfers"]["requested"] is True


class TestCreateAccountLink:
    """Tests for create_account_link method."""

    @pytest.mark.asyncio
    async def test_create_account_link_success(self):
        """Should create account link and return URL."""
        service = StripeService(secret_key="sk_test_123")

        mock_link = MagicMock()
        mock_link.url = "https://connect.stripe.com/onboard/123"

        with patch.object(stripe.AccountLink, "create", return_value=mock_link):
            url = await service.create_account_link(
                account_id="acct_123",
                refresh_url="https://example.com/refresh",
                return_url="https://example.com/return",
            )

            assert url == "https://connect.stripe.com/onboard/123"

    @pytest.mark.asyncio
    async def test_create_account_link_with_correct_params(self):
        """Should call Stripe with correct parameters."""
        service = StripeService(secret_key="sk_test_123")

        mock_link = MagicMock()
        mock_link.url = "https://connect.stripe.com/onboard"

        with patch.object(stripe.AccountLink, "create", return_value=mock_link) as mock:
            await service.create_account_link(
                account_id="acct_test",
                refresh_url="https://example.com/refresh",
                return_url="https://example.com/return",
            )

            mock.assert_called_once_with(
                account="acct_test",
                refresh_url="https://example.com/refresh",
                return_url="https://example.com/return",
                type="account_onboarding",
            )

    @pytest.mark.asyncio
    async def test_create_account_link_without_api_key(self):
        """Should raise ValueError if no API key."""
        service = StripeService(secret_key="")

        with pytest.raises(ValueError, match="not configured"):
            await service.create_account_link(
                account_id="acct_123",
                refresh_url="https://example.com/refresh",
                return_url="https://example.com/return",
            )


class TestGetAccountStatus:
    """Tests for get_account_status method."""

    @pytest.mark.asyncio
    async def test_get_account_status_active(self):
        """Should return ACTIVE status when fully enabled."""
        service = StripeService(secret_key="sk_test_123")

        mock_account = MagicMock()
        mock_account.id = "acct_active"
        mock_account.charges_enabled = True
        mock_account.payouts_enabled = True
        mock_account.details_submitted = True
        mock_account.requirements = {"currently_due": []}

        with patch.object(stripe.Account, "retrieve", return_value=mock_account):
            status = await service.get_account_status("acct_active")

            assert status.status == StripeAccountStatus.ACTIVE
            assert status.charges_enabled is True
            assert status.payouts_enabled is True

    @pytest.mark.asyncio
    async def test_get_account_status_pending(self):
        """Should return PENDING status when details not submitted."""
        service = StripeService(secret_key="sk_test_123")

        mock_account = MagicMock()
        mock_account.id = "acct_pending"
        mock_account.charges_enabled = False
        mock_account.payouts_enabled = False
        mock_account.details_submitted = False
        mock_account.requirements = {"currently_due": ["individual.first_name"]}

        with patch.object(stripe.Account, "retrieve", return_value=mock_account):
            status = await service.get_account_status("acct_pending")

            assert status.status == StripeAccountStatus.PENDING
            assert status.details_submitted is False

    @pytest.mark.asyncio
    async def test_get_account_status_restricted(self):
        """Should return RESTRICTED status when requirements due."""
        service = StripeService(secret_key="sk_test_123")

        mock_account = MagicMock()
        mock_account.id = "acct_restricted"
        mock_account.charges_enabled = False
        mock_account.payouts_enabled = False
        mock_account.details_submitted = True
        mock_account.requirements = {
            "currently_due": ["bank_account"],
            "disabled_reason": None,
        }

        with patch.object(stripe.Account, "retrieve", return_value=mock_account):
            status = await service.get_account_status("acct_restricted")

            assert status.status == StripeAccountStatus.RESTRICTED

    @pytest.mark.asyncio
    async def test_get_account_status_rejected(self):
        """Should return REJECTED status when disabled."""
        service = StripeService(secret_key="sk_test_123")

        mock_account = MagicMock()
        mock_account.id = "acct_rejected"
        mock_account.charges_enabled = False
        mock_account.payouts_enabled = False
        mock_account.details_submitted = True
        mock_account.requirements = {
            "disabled_reason": "rejected.fraud",
            "currently_due": [],
        }

        with patch.object(stripe.Account, "retrieve", return_value=mock_account):
            status = await service.get_account_status("acct_rejected")

            assert status.status == StripeAccountStatus.REJECTED

    @pytest.mark.asyncio
    async def test_get_account_status_returns_requirements(self):
        """Should return list of requirements due."""
        service = StripeService(secret_key="sk_test_123")

        mock_account = MagicMock()
        mock_account.id = "acct_reqs"
        mock_account.charges_enabled = False
        mock_account.payouts_enabled = False
        mock_account.details_submitted = False
        mock_account.requirements = {
            "currently_due": ["individual.first_name", "individual.last_name"],
        }

        with patch.object(stripe.Account, "retrieve", return_value=mock_account):
            status = await service.get_account_status("acct_reqs")

            assert len(status.requirements_due) == 2
            assert "individual.first_name" in status.requirements_due
            assert "individual.last_name" in status.requirements_due

    @pytest.mark.asyncio
    async def test_get_account_status_without_api_key(self):
        """Should raise ValueError if no API key."""
        service = StripeService(secret_key="")

        with pytest.raises(ValueError, match="not configured"):
            await service.get_account_status("acct_123")


class TestCreatePaymentIntent:
    """Tests for create_payment_intent method."""

    @pytest.mark.asyncio
    async def test_create_payment_intent_success(self):
        """Should create payment intent and return ID and secret."""
        service = StripeService(secret_key="sk_test_123")

        mock_intent = MagicMock()
        mock_intent.id = "pi_test123"
        mock_intent.client_secret = "pi_test123_secret_abc"

        with patch.object(stripe.PaymentIntent, "create", return_value=mock_intent):
            pi_id, client_secret = await service.create_payment_intent(
                amount_cents=5000,
            )

            assert pi_id == "pi_test123"
            assert client_secret == "pi_test123_secret_abc"

    @pytest.mark.asyncio
    async def test_create_payment_intent_with_connected_account(self):
        """Should set transfer_data when connected account provided."""
        service = StripeService(secret_key="sk_test_123")

        mock_intent = MagicMock()
        mock_intent.id = "pi_connected"
        mock_intent.client_secret = "secret"

        with patch.object(
            stripe.PaymentIntent, "create", return_value=mock_intent
        ) as mock:
            await service.create_payment_intent(
                amount_cents=5000,
                connected_account_id="acct_host",
            )

            mock.assert_called_once()
            call_kwargs = mock.call_args[1]
            assert call_kwargs["transfer_data"]["destination"] == "acct_host"

    @pytest.mark.asyncio
    async def test_create_payment_intent_with_platform_fee(self):
        """Should set application_fee_amount when fee provided."""
        service = StripeService(secret_key="sk_test_123")

        mock_intent = MagicMock()
        mock_intent.id = "pi_fee"
        mock_intent.client_secret = "secret"

        with patch.object(
            stripe.PaymentIntent, "create", return_value=mock_intent
        ) as mock:
            await service.create_payment_intent(
                amount_cents=5000,
                connected_account_id="acct_host",
                platform_fee_cents=500,
            )

            mock.assert_called_once()
            call_kwargs = mock.call_args[1]
            assert call_kwargs["application_fee_amount"] == 500

    @pytest.mark.asyncio
    async def test_create_payment_intent_manual_capture(self):
        """Should use manual capture by default."""
        service = StripeService(secret_key="sk_test_123")

        mock_intent = MagicMock()
        mock_intent.id = "pi_manual"
        mock_intent.client_secret = "secret"

        with patch.object(
            stripe.PaymentIntent, "create", return_value=mock_intent
        ) as mock:
            await service.create_payment_intent(amount_cents=5000)

            mock.assert_called_once()
            call_kwargs = mock.call_args[1]
            assert call_kwargs["capture_method"] == "manual"


class TestCapturePaymentIntent:
    """Tests for capture_payment_intent method."""

    @pytest.mark.asyncio
    async def test_capture_payment_intent_success(self):
        """Should capture payment and return True on success."""
        service = StripeService(secret_key="sk_test_123")

        mock_intent = MagicMock()
        mock_intent.status = "succeeded"

        with patch.object(stripe.PaymentIntent, "capture", return_value=mock_intent):
            result = await service.capture_payment_intent("pi_123")

            assert result is True

    @pytest.mark.asyncio
    async def test_capture_payment_intent_failure(self):
        """Should return False if capture fails."""
        service = StripeService(secret_key="sk_test_123")

        mock_intent = MagicMock()
        mock_intent.status = "requires_capture"

        with patch.object(stripe.PaymentIntent, "capture", return_value=mock_intent):
            result = await service.capture_payment_intent("pi_123")

            assert result is False


class TestCancelPaymentIntent:
    """Tests for cancel_payment_intent method."""

    @pytest.mark.asyncio
    async def test_cancel_payment_intent_success(self):
        """Should cancel payment and return True on success."""
        service = StripeService(secret_key="sk_test_123")

        mock_intent = MagicMock()
        mock_intent.status = "canceled"

        with patch.object(stripe.PaymentIntent, "cancel", return_value=mock_intent):
            result = await service.cancel_payment_intent("pi_123")

            assert result is True

    @pytest.mark.asyncio
    async def test_cancel_payment_intent_failure(self):
        """Should return False if cancel fails."""
        service = StripeService(secret_key="sk_test_123")

        mock_intent = MagicMock()
        mock_intent.status = "requires_payment_method"

        with patch.object(stripe.PaymentIntent, "cancel", return_value=mock_intent):
            result = await service.cancel_payment_intent("pi_123")

            assert result is False


class TestAccountStatusDataclass:
    """Tests for AccountStatus dataclass."""

    def test_account_status_creation(self):
        """Should create AccountStatus with all fields."""
        status = AccountStatus(
            account_id="acct_123",
            status=StripeAccountStatus.ACTIVE,
            charges_enabled=True,
            payouts_enabled=True,
            details_submitted=True,
            requirements_due=[],
        )

        assert status.account_id == "acct_123"
        assert status.status == StripeAccountStatus.ACTIVE
        assert status.charges_enabled is True
        assert status.payouts_enabled is True
        assert status.details_submitted is True
        assert status.requirements_due == []

    def test_account_status_with_requirements(self):
        """Should store requirements list."""
        status = AccountStatus(
            account_id="acct_456",
            status=StripeAccountStatus.PENDING,
            charges_enabled=False,
            payouts_enabled=False,
            details_submitted=False,
            requirements_due=["external_account", "individual.verification.document"],
        )

        assert len(status.requirements_due) == 2


class TestStripeAccountStatusEnum:
    """Tests for StripeAccountStatus enum."""

    def test_enum_values(self):
        """Should have all expected status values."""
        assert StripeAccountStatus.NOT_CREATED == "not_created"
        assert StripeAccountStatus.PENDING == "pending"
        assert StripeAccountStatus.ACTIVE == "active"
        assert StripeAccountStatus.RESTRICTED == "restricted"
        assert StripeAccountStatus.REJECTED == "rejected"

    def test_enum_is_str_enum(self):
        """Enum values should be strings."""
        assert isinstance(StripeAccountStatus.ACTIVE.value, str)


class TestSingletonInstance:
    """Tests for singleton stripe_service instance."""

    def test_singleton_exists(self):
        """Should export stripe_service singleton."""
        from app.services.stripe import stripe_service

        assert stripe_service is not None
        assert isinstance(stripe_service, StripeService)
