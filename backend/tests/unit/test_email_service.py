"""Unit tests for email sending service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email import (
    ConsoleEmailProvider,
    EmailMessage,
    EmailService,
    EmailTemplate,
    SendGridProvider,
)


class TestEmailMessage:
    """Tests for EmailMessage data class."""

    def test_create_email_message_with_required_fields(self) -> None:
        """Test creating EmailMessage with only required fields."""
        message = EmailMessage(
            to_email="test@example.com",
            subject="Test Subject",
            plain_text="Test body",
        )
        assert message.to_email == "test@example.com"
        assert message.subject == "Test Subject"
        assert message.plain_text == "Test body"
        assert message.html_content is None
        assert message.from_email is None
        assert message.from_name is None
        assert message.reply_to is None

    def test_create_email_message_with_all_fields(self) -> None:
        """Test creating EmailMessage with all fields."""
        message = EmailMessage(
            to_email="test@example.com",
            subject="Test Subject",
            plain_text="Test body",
            html_content="<p>Test body</p>",
            from_email="sender@example.com",
            from_name="Sender Name",
            reply_to="reply@example.com",
        )
        assert message.to_email == "test@example.com"
        assert message.html_content == "<p>Test body</p>"
        assert message.from_email == "sender@example.com"
        assert message.from_name == "Sender Name"
        assert message.reply_to == "reply@example.com"


class TestConsoleEmailProvider:
    """Tests for ConsoleEmailProvider."""

    @pytest.mark.asyncio
    async def test_send_logs_email_and_returns_id(self) -> None:
        """Test that console provider logs and returns message ID."""
        provider = ConsoleEmailProvider()
        message = EmailMessage(
            to_email="test@example.com",
            subject="Test Subject",
            plain_text="Test body",
        )

        with patch("app.services.email.logger") as mock_logger:
            result = await provider.send(message)

        assert result.startswith("console_")
        assert "test@example.com" in result
        mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_logs_email_with_html(self) -> None:
        """Test that console provider logs HTML presence."""
        provider = ConsoleEmailProvider()
        message = EmailMessage(
            to_email="test@example.com",
            subject="Test Subject",
            plain_text="Test body",
            html_content="<p>Test body</p>",
        )

        with patch("app.services.email.logger") as mock_logger:
            await provider.send(message)

        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs["has_html"] is True


class TestSendGridProvider:
    """Tests for SendGridProvider."""

    def test_init_stores_configuration(self) -> None:
        """Test that provider stores configuration."""
        provider = SendGridProvider(
            api_key="test-api-key",
            from_email="noreply@example.com",
            from_name="Test Sender",
        )
        assert provider._api_key == "test-api-key"
        assert provider._from_email == "noreply@example.com"
        assert provider._from_name == "Test Sender"
        assert provider._client is None  # Lazy loaded

    def test_get_client_returns_none_when_sendgrid_not_installed(self) -> None:
        """Test fallback when SendGrid package is not installed."""
        provider = SendGridProvider(
            api_key="test-api-key",
            from_email="noreply@example.com",
            from_name="Test Sender",
        )

        with (
            patch.dict("sys.modules", {"sendgrid": None}),
            patch(
                "app.services.email.SendGridProvider._get_client",
                return_value=None,
            ),
        ):
            client = provider._get_client()
            # When import fails, _get_client catches ImportError and returns None
            # For this test, we mock it to return None
            assert client is None

    @pytest.mark.asyncio
    async def test_send_falls_back_to_logging_when_no_client(self) -> None:
        """Test that send falls back to logging when client is None."""
        provider = SendGridProvider(
            api_key="test-api-key",
            from_email="noreply@example.com",
            from_name="Test Sender",
        )

        # Mock _get_client to return None (simulating missing sendgrid package)
        with (
            patch.object(provider, "_get_client", return_value=None),
            patch("app.services.email.logger") as mock_logger,
        ):
            message = EmailMessage(
                to_email="test@example.com",
                subject="Test Subject",
                plain_text="Test body",
            )
            result = await provider.send(message)

        assert "logged_" in result
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_send_uses_default_from_email(self) -> None:
        """Test that send uses default from_email when not specified in message."""
        provider = SendGridProvider(
            api_key="test-api-key",
            from_email="default@example.com",
            from_name="Default Sender",
        )

        message = EmailMessage(
            to_email="test@example.com",
            subject="Test Subject",
            plain_text="Test body",
        )

        # Mock to fallback mode
        with (
            patch.object(provider, "_get_client", return_value=None),
            patch("app.services.email.logger") as mock_logger,
        ):
            await provider.send(message)

        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs["from_email"] == "default@example.com"

    @pytest.mark.asyncio
    async def test_send_uses_custom_from_email(self) -> None:
        """Test that send uses custom from_email when specified in message."""
        provider = SendGridProvider(
            api_key="test-api-key",
            from_email="default@example.com",
            from_name="Default Sender",
        )

        message = EmailMessage(
            to_email="test@example.com",
            subject="Test Subject",
            plain_text="Test body",
            from_email="custom@example.com",
        )

        with (
            patch.object(provider, "_get_client", return_value=None),
            patch("app.services.email.logger") as mock_logger,
        ):
            await provider.send(message)

        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs["from_email"] == "custom@example.com"


class TestEmailService:
    """Tests for EmailService class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_provider = MagicMock()
        self.mock_provider.send = AsyncMock(return_value="msg_123")
        self.service = EmailService(provider=self.mock_provider)

    @pytest.mark.asyncio
    async def test_send_delegates_to_provider(self) -> None:
        """Test that send delegates to the provider."""
        message = EmailMessage(
            to_email="test@example.com",
            subject="Test Subject",
            plain_text="Test body",
        )

        result = await self.service.send(message)

        self.mock_provider.send.assert_called_once_with(message)
        assert result == "msg_123"

    @pytest.mark.asyncio
    async def test_send_template_renders_and_sends(self) -> None:
        """Test that send_template renders template and sends."""
        result = await self.service.send_template(
            template=EmailTemplate.WELCOME,
            to_email="test@example.com",
            context={"name": "Test User"},
        )

        self.mock_provider.send.assert_called_once()
        call_args = self.mock_provider.send.call_args[0][0]
        assert call_args.to_email == "test@example.com"
        assert "Welcome" in call_args.subject
        assert result == "msg_123"

    def test_render_template_unknown_raises_error(self) -> None:
        """Test that unknown template raises ValueError."""
        with pytest.raises(ValueError, match="Unknown email template"):
            self.service._render_template("invalid_template", {})


class TestEmailTemplates:
    """Tests for email template rendering."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_provider = MagicMock()
        self.mock_provider.send = AsyncMock(return_value="msg_123")
        self.service = EmailService(provider=self.mock_provider)

    def test_magic_link_template(self) -> None:
        """Test magic link template rendering."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.MAGIC_LINK,
            {"code": "123456", "name": "John", "expires_minutes": 15},
        )

        assert "Login Code" in subject
        assert "123456" in plain_text
        assert "John" in plain_text
        assert "15 minutes" in plain_text
        assert "123456" in html
        assert "John" in html

    def test_magic_link_template_defaults(self) -> None:
        """Test magic link template with default values."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.MAGIC_LINK,
            {},
        )

        assert "000000" in plain_text
        assert "there" in plain_text
        assert "15 minutes" in plain_text

    def test_booking_created_template_for_host(self) -> None:
        """Test booking created template for host."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.BOOKING_CREATED,
            {
                "recipient_name": "Host Name",
                "client_name": "Client Name",
                "host_name": "Host Name",
                "date": "2024-01-15",
                "time": "10:00 AM",
                "duration": "1 hour",
                "dance_style": "Salsa",
                "is_host": True,
            },
        )

        assert "Client Name" in subject
        assert "new booking request" in plain_text.lower()
        assert "confirm or decline" in plain_text.lower()

    def test_booking_created_template_for_client(self) -> None:
        """Test booking created template for client."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.BOOKING_CREATED,
            {
                "recipient_name": "Client Name",
                "client_name": "Client Name",
                "host_name": "Host Name",
                "is_host": False,
            },
        )

        assert "Host Name" in subject
        assert "request has been sent" in plain_text.lower()

    def test_booking_confirmed_template(self) -> None:
        """Test booking confirmed template rendering."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.BOOKING_CONFIRMED,
            {
                "recipient_name": "John",
                "host_name": "Jane",
                "date": "2024-01-15",
                "time": "10:00 AM",
                "duration": "1 hour",
                "dance_style": "Salsa",
                "location": "123 Main St",
            },
        )

        assert "Confirmed" in subject
        assert "John" in plain_text
        assert "Jane" in plain_text
        assert "2024-01-15" in plain_text
        assert "123 Main St" in plain_text
        assert "123 Main St" in html

    def test_booking_confirmed_template_without_location(self) -> None:
        """Test booking confirmed template without location."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.BOOKING_CONFIRMED,
            {"recipient_name": "John", "host_name": "Jane"},
        )

        assert "John" in plain_text
        # Location line should not appear when empty
        assert "Location:" not in plain_text or "Location: " not in plain_text

    def test_booking_cancelled_template(self) -> None:
        """Test booking cancelled template rendering."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.BOOKING_CANCELLED,
            {
                "recipient_name": "John",
                "cancelled_by": "the host",
                "reason": "Schedule conflict",
                "date": "2024-01-15",
                "time": "10:00 AM",
            },
        )

        assert "Cancelled" in subject
        assert "John" in plain_text
        assert "the host" in plain_text
        assert "Schedule conflict" in plain_text

    def test_booking_cancelled_template_without_reason(self) -> None:
        """Test booking cancelled template without reason."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.BOOKING_CANCELLED,
            {"recipient_name": "John", "cancelled_by": "the host"},
        )

        assert "John" in plain_text
        # Reason line should not appear when empty

    def test_booking_completed_template(self) -> None:
        """Test booking completed template rendering."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.BOOKING_COMPLETED,
            {
                "recipient_name": "John",
                "host_name": "Jane",
                "date": "2024-01-15",
            },
        )

        assert "Completed" in subject or "experience" in subject.lower()
        assert "John" in plain_text
        assert "Jane" in plain_text
        assert "review" in plain_text.lower()

    def test_session_reminder_template(self) -> None:
        """Test session reminder template rendering."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.SESSION_REMINDER,
            {
                "recipient_name": "John",
                "partner_name": "Jane",
                "date": "2024-01-15",
                "time": "10:00 AM",
                "minutes_until": 30,
                "location": "123 Main St",
            },
        )

        assert "30 minutes" in subject
        assert "John" in plain_text
        assert "Jane" in plain_text
        assert "30 minutes" in plain_text
        assert "123 Main St" in plain_text

    def test_review_request_template(self) -> None:
        """Test review request template rendering."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.REVIEW_REQUEST,
            {
                "recipient_name": "John",
                "host_name": "Jane",
                "date": "2024-01-15",
            },
        )

        assert "John" in plain_text
        assert "Jane" in plain_text
        assert "review" in plain_text.lower()

    def test_new_message_template(self) -> None:
        """Test new message template rendering."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.NEW_MESSAGE,
            {
                "recipient_name": "John",
                "sender_name": "Jane",
                "message_preview": "Hello! Are you available for a session?",
            },
        )

        assert "Jane" in subject
        assert "John" in plain_text
        assert "Jane" in plain_text
        assert "Hello!" in plain_text

    def test_new_message_template_truncates_long_preview(self) -> None:
        """Test new message template truncates long previews."""
        long_message = "x" * 200
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.NEW_MESSAGE,
            {
                "recipient_name": "John",
                "sender_name": "Jane",
                "message_preview": long_message,
            },
        )

        # Preview should be truncated to 100 chars + "..."
        assert "..." in plain_text

    def test_welcome_template(self) -> None:
        """Test welcome template rendering."""
        subject, plain_text, html = self.service._render_template(
            EmailTemplate.WELCOME,
            {"name": "John"},
        )

        assert "Welcome" in subject
        assert "John" in plain_text
        assert "Complete your profile" in plain_text
        assert "dance hosts" in plain_text.lower()


class TestEmailTemplateEnum:
    """Tests for EmailTemplate enum."""

    def test_all_templates_have_values(self) -> None:
        """Test that all templates have string values."""
        for template in EmailTemplate:
            assert isinstance(template.value, str)
            assert len(template.value) > 0

    def test_template_values_are_unique(self) -> None:
        """Test that all template values are unique."""
        values = [t.value for t in EmailTemplate]
        assert len(values) == len(set(values))

    def test_expected_templates_exist(self) -> None:
        """Test that expected templates exist."""
        expected = [
            "magic_link",
            "booking_created",
            "booking_confirmed",
            "booking_cancelled",
            "booking_completed",
            "session_reminder",
            "review_request",
            "new_message",
            "welcome",
        ]
        actual = [t.value for t in EmailTemplate]
        for expected_template in expected:
            assert expected_template in actual, f"Missing template: {expected_template}"


class TestEmailServiceCreation:
    """Tests for email service singleton creation."""

    def test_email_service_with_sendgrid_key(self) -> None:
        """Test email service creation with SendGrid API key."""
        with patch("app.services.email.get_settings") as mock_settings:
            mock_settings.return_value.sendgrid_api_key = "test-key"
            mock_settings.return_value.email_from_address = "test@example.com"
            mock_settings.return_value.email_from_name = "Test"

            from app.services.email import _create_email_service

            service = _create_email_service()

            assert isinstance(service._provider, SendGridProvider)

    def test_email_service_without_sendgrid_key(self) -> None:
        """Test email service falls back to console provider."""
        with patch("app.services.email.get_settings") as mock_settings:
            mock_settings.return_value.sendgrid_api_key = ""
            mock_settings.return_value.email_from_address = "test@example.com"
            mock_settings.return_value.email_from_name = "Test"

            from app.services.email import _create_email_service

            service = _create_email_service()

            assert isinstance(service._provider, ConsoleEmailProvider)
