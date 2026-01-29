"""Email sending service with SendGrid integration."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

import structlog

from app.core.config import get_settings

logger = structlog.get_logger()


class EmailTemplate(str, Enum):
    """Available email templates."""

    MAGIC_LINK = "magic_link"
    BOOKING_CREATED = "booking_created"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_COMPLETED = "booking_completed"
    SESSION_REMINDER = "session_reminder"
    REVIEW_REQUEST = "review_request"
    NEW_MESSAGE = "new_message"
    WELCOME = "welcome"


@dataclass
class EmailMessage:
    """Email message data class."""

    to_email: str
    subject: str
    plain_text: str
    html_content: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None


class EmailProvider(Protocol):
    """Protocol for email providers."""

    async def send(self, message: EmailMessage) -> str:
        """Send an email and return message ID."""
        ...


class SendGridProvider:
    """SendGrid email provider implementation."""

    def __init__(self, api_key: str, from_email: str, from_name: str) -> None:
        """Initialize SendGrid provider.

        Args:
            api_key: SendGrid API key.
            from_email: Default sender email address.
            from_name: Default sender name.
        """
        self._api_key = api_key
        self._from_email = from_email
        self._from_name = from_name
        self._client = None

    def _get_client(self):
        """Lazy-load the SendGrid client."""
        if self._client is None:
            try:
                from sendgrid import SendGridAPIClient

                self._client = SendGridAPIClient(self._api_key)
            except ImportError:
                logger.warning(
                    "sendgrid_not_installed",
                    message="SendGrid package not installed. Falling back to logging.",
                )
                return None
        return self._client

    async def send(self, message: EmailMessage) -> str:
        """Send email via SendGrid.

        Args:
            message: Email message to send.

        Returns:
            Message ID from SendGrid.

        Raises:
            Exception: On SendGrid API error.
        """
        client = self._get_client()

        # Use provided from_email or fall back to default
        from_email = message.from_email or self._from_email
        from_name = message.from_name or self._from_name

        if client is None:
            # Fallback: log the email instead
            logger.info(
                "email_logged_fallback",
                to=message.to_email,
                subject=message.subject,
                from_email=from_email,
            )
            return f"logged_{message.to_email}_{message.subject[:20]}"

        try:
            from sendgrid.helpers.mail import Content, Email, Mail, To

            mail = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(message.to_email),
                subject=message.subject,
            )

            # Add plain text content
            mail.add_content(Content("text/plain", message.plain_text))

            # Add HTML content if provided
            if message.html_content:
                mail.add_content(Content("text/html", message.html_content))

            # Add reply-to if provided
            if message.reply_to:
                from sendgrid.helpers.mail import ReplyTo

                mail.reply_to = ReplyTo(message.reply_to)

            response = client.send(mail)

            message_id = response.headers.get("X-Message-Id", "unknown")

            logger.info(
                "sendgrid_email_sent",
                to=message.to_email,
                subject=message.subject,
                status_code=response.status_code,
                message_id=message_id,
            )

            return message_id

        except Exception as e:
            logger.error(
                "sendgrid_send_failed",
                to=message.to_email,
                subject=message.subject,
                error=str(e),
            )
            raise


class ConsoleEmailProvider:
    """Console email provider for development/testing."""

    async def send(self, message: EmailMessage) -> str:
        """Log email to console instead of sending.

        Args:
            message: Email message to log.

        Returns:
            Mock message ID.
        """
        logger.info(
            "console_email",
            to=message.to_email,
            subject=message.subject,
            plain_text_preview=message.plain_text[:200] if message.plain_text else None,
            has_html=message.html_content is not None,
        )
        return f"console_{message.to_email}"


class EmailService:
    """Email service for sending templated emails.

    Supports SendGrid for production and console logging for development.
    """

    def __init__(self, provider: EmailProvider) -> None:
        """Initialize email service with a provider.

        Args:
            provider: Email provider implementation.
        """
        self._provider = provider

    async def send(self, message: EmailMessage) -> str:
        """Send an email message.

        Args:
            message: Email message to send.

        Returns:
            Message ID from the provider.
        """
        return await self._provider.send(message)

    async def send_template(
        self,
        template: EmailTemplate,
        to_email: str,
        context: dict,
    ) -> str:
        """Send an email using a template.

        Args:
            template: Email template to use.
            to_email: Recipient email address.
            context: Template context variables.

        Returns:
            Message ID from the provider.
        """
        subject, plain_text, html_content = self._render_template(template, context)

        message = EmailMessage(
            to_email=to_email,
            subject=subject,
            plain_text=plain_text,
            html_content=html_content,
        )

        return await self._provider.send(message)

    def _render_template(
        self,
        template: EmailTemplate,
        context: dict,
    ) -> tuple[str, str, str]:
        """Render an email template.

        Args:
            template: Template to render.
            context: Template context variables.

        Returns:
            Tuple of (subject, plain_text, html_content).
        """
        templates = {
            EmailTemplate.MAGIC_LINK: self._template_magic_link,
            EmailTemplate.BOOKING_CREATED: self._template_booking_created,
            EmailTemplate.BOOKING_CONFIRMED: self._template_booking_confirmed,
            EmailTemplate.BOOKING_CANCELLED: self._template_booking_cancelled,
            EmailTemplate.BOOKING_COMPLETED: self._template_booking_completed,
            EmailTemplate.SESSION_REMINDER: self._template_session_reminder,
            EmailTemplate.REVIEW_REQUEST: self._template_review_request,
            EmailTemplate.NEW_MESSAGE: self._template_new_message,
            EmailTemplate.WELCOME: self._template_welcome,
        }

        renderer = templates.get(template)
        if renderer is None:
            raise ValueError(f"Unknown email template: {template}")

        return renderer(context)

    def _template_magic_link(self, ctx: dict) -> tuple[str, str, str]:
        """Render magic link email template."""
        code = ctx.get("code", "000000")
        name = ctx.get("name", "there")
        expires_minutes = ctx.get("expires_minutes", 15)

        subject = "Your Strictly Dancing Login Code"

        plain_text = f"""Hi {name},

Your login code is: {code}

This code will expire in {expires_minutes} minutes.

If you didn't request this code, you can safely ignore this email.

- The Strictly Dancing Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #e11d48; margin: 0 0 24px;">Strictly Dancing</h1>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Hi {name},</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Your login code is:</p>
        <div style="background: #fef2f2; border: 2px solid #e11d48; border-radius: 8px; padding: 24px; text-align: center; margin: 24px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #e11d48;">{code}</span>
        </div>
        <p style="color: #6b7280; font-size: 14px;">This code will expire in {expires_minutes} minutes.</p>
        <p style="color: #6b7280; font-size: 14px;">If you didn't request this code, you can safely ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">- The Strictly Dancing Team</p>
    </div>
</body>
</html>
"""

        return subject, plain_text, html_content

    def _template_booking_created(self, ctx: dict) -> tuple[str, str, str]:
        """Render booking created email template."""
        recipient_name = ctx.get("recipient_name", "there")
        host_name = ctx.get("host_name", "your host")
        client_name = ctx.get("client_name", "a client")
        date = ctx.get("date", "TBD")
        time = ctx.get("time", "TBD")
        duration = ctx.get("duration", "1 hour")
        dance_style = ctx.get("dance_style", "Dance")
        is_host = ctx.get("is_host", False)

        if is_host:
            subject = f"New Booking Request from {client_name}"
            intro = f"You have a new booking request from {client_name}!"
            action = "Please log in to confirm or decline this booking."
        else:
            subject = f"Booking Request Sent to {host_name}"
            intro = f"Your booking request has been sent to {host_name}!"
            action = "You'll receive an email when they respond."

        plain_text = f"""Hi {recipient_name},

{intro}

Session Details:
- Date: {date}
- Time: {time}
- Duration: {duration}
- Style: {dance_style}

{action}

- The Strictly Dancing Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #e11d48; margin: 0 0 24px;">Strictly Dancing</h1>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Hi {recipient_name},</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">{intro}</p>
        <div style="background: #f9fafb; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <h3 style="margin: 0 0 12px; color: #111827;">Session Details</h3>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Date:</strong> {date}</p>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Time:</strong> {time}</p>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Duration:</strong> {duration}</p>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Style:</strong> {dance_style}</p>
        </div>
        <p style="color: #6b7280; font-size: 14px;">{action}</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">- The Strictly Dancing Team</p>
    </div>
</body>
</html>
"""

        return subject, plain_text, html_content

    def _template_booking_confirmed(self, ctx: dict) -> tuple[str, str, str]:
        """Render booking confirmed email template."""
        recipient_name = ctx.get("recipient_name", "there")
        host_name = ctx.get("host_name", "your host")
        date = ctx.get("date", "TBD")
        time = ctx.get("time", "TBD")
        duration = ctx.get("duration", "1 hour")
        dance_style = ctx.get("dance_style", "Dance")
        location = ctx.get("location", "")

        subject = "Booking Confirmed!"

        plain_text = f"""Hi {recipient_name},

Great news! Your dance session with {host_name} has been confirmed!

Session Details:
- Date: {date}
- Time: {time}
- Duration: {duration}
- Style: {dance_style}
{f"- Location: {location}" if location else ""}

We'll send you a reminder before your session.

- The Strictly Dancing Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #e11d48; margin: 0 0 24px;">Strictly Dancing</h1>
        <div style="background: #d1fae5; border-radius: 8px; padding: 16px; text-align: center; margin-bottom: 24px;">
            <span style="color: #065f46; font-weight: bold; font-size: 18px;">✓ Booking Confirmed!</span>
        </div>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Hi {recipient_name},</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Great news! Your dance session with <strong>{host_name}</strong> has been confirmed!</p>
        <div style="background: #f9fafb; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <h3 style="margin: 0 0 12px; color: #111827;">Session Details</h3>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Date:</strong> {date}</p>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Time:</strong> {time}</p>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Duration:</strong> {duration}</p>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Style:</strong> {dance_style}</p>
            {f'<p style="margin: 4px 0; color: #4b5563;"><strong>Location:</strong> {location}</p>' if location else ""}
        </div>
        <p style="color: #6b7280; font-size: 14px;">We'll send you a reminder before your session.</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">- The Strictly Dancing Team</p>
    </div>
</body>
</html>
"""

        return subject, plain_text, html_content

    def _template_booking_cancelled(self, ctx: dict) -> tuple[str, str, str]:
        """Render booking cancelled email template."""
        recipient_name = ctx.get("recipient_name", "there")
        cancelled_by = ctx.get("cancelled_by", "the other party")
        reason = ctx.get("reason", "")
        date = ctx.get("date", "TBD")
        time = ctx.get("time", "TBD")

        subject = "Booking Cancelled"

        plain_text = f"""Hi {recipient_name},

Unfortunately, your booking for {date} at {time} has been cancelled by {cancelled_by}.

{f"Reason: {reason}" if reason else ""}

If you have any questions, please contact support.

- The Strictly Dancing Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #e11d48; margin: 0 0 24px;">Strictly Dancing</h1>
        <div style="background: #fee2e2; border-radius: 8px; padding: 16px; text-align: center; margin-bottom: 24px;">
            <span style="color: #991b1b; font-weight: bold; font-size: 18px;">Booking Cancelled</span>
        </div>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Hi {recipient_name},</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Unfortunately, your booking for <strong>{date}</strong> at <strong>{time}</strong> has been cancelled by {cancelled_by}.</p>
        {f'<p style="color: #6b7280; font-size: 14px;"><strong>Reason:</strong> {reason}</p>' if reason else ""}
        <p style="color: #6b7280; font-size: 14px;">If you have any questions, please contact support.</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">- The Strictly Dancing Team</p>
    </div>
</body>
</html>
"""

        return subject, plain_text, html_content

    def _template_booking_completed(self, ctx: dict) -> tuple[str, str, str]:
        """Render booking completed email template."""
        recipient_name = ctx.get("recipient_name", "there")
        host_name = ctx.get("host_name", "your host")
        date = ctx.get("date", "TBD")

        subject = "Session Completed - How was your experience?"

        plain_text = f"""Hi {recipient_name},

Your dance session with {host_name} on {date} has been completed!

We'd love to hear about your experience. Please take a moment to leave a review.

Thanks for using Strictly Dancing!

- The Strictly Dancing Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #e11d48; margin: 0 0 24px;">Strictly Dancing</h1>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Hi {recipient_name},</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Your dance session with <strong>{host_name}</strong> on <strong>{date}</strong> has been completed!</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">We'd love to hear about your experience. Please take a moment to leave a review.</p>
        <div style="text-align: center; margin: 32px 0;">
            <a href="#" style="display: inline-block; background: #e11d48; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: bold;">Leave a Review</a>
        </div>
        <p style="color: #6b7280; font-size: 14px;">Thanks for using Strictly Dancing!</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">- The Strictly Dancing Team</p>
    </div>
</body>
</html>
"""

        return subject, plain_text, html_content

    def _template_session_reminder(self, ctx: dict) -> tuple[str, str, str]:
        """Render session reminder email template."""
        recipient_name = ctx.get("recipient_name", "there")
        partner_name = ctx.get("partner_name", "your partner")
        date = ctx.get("date", "TBD")
        time = ctx.get("time", "TBD")
        minutes_until = ctx.get("minutes_until", 30)
        location = ctx.get("location", "")

        subject = f"Reminder: Dance session in {minutes_until} minutes"

        plain_text = f"""Hi {recipient_name},

Just a reminder that your dance session with {partner_name} starts in {minutes_until} minutes!

Session Details:
- Date: {date}
- Time: {time}
{f"- Location: {location}" if location else ""}

Have a great session!

- The Strictly Dancing Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #e11d48; margin: 0 0 24px;">Strictly Dancing</h1>
        <div style="background: #fef3c7; border-radius: 8px; padding: 16px; text-align: center; margin-bottom: 24px;">
            <span style="color: #92400e; font-weight: bold; font-size: 18px;">⏰ Session in {minutes_until} minutes!</span>
        </div>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Hi {recipient_name},</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Just a reminder that your dance session with <strong>{partner_name}</strong> starts soon!</p>
        <div style="background: #f9fafb; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <p style="margin: 4px 0; color: #4b5563;"><strong>Date:</strong> {date}</p>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Time:</strong> {time}</p>
            {f'<p style="margin: 4px 0; color: #4b5563;"><strong>Location:</strong> {location}</p>' if location else ""}
        </div>
        <p style="color: #6b7280; font-size: 14px;">Have a great session!</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">- The Strictly Dancing Team</p>
    </div>
</body>
</html>
"""

        return subject, plain_text, html_content

    def _template_review_request(self, ctx: dict) -> tuple[str, str, str]:
        """Render review request email template."""
        recipient_name = ctx.get("recipient_name", "there")
        host_name = ctx.get("host_name", "your host")
        date = ctx.get("date", "recently")

        subject = "How was your dance session?"

        plain_text = f"""Hi {recipient_name},

You recently had a dance session with {host_name} on {date}.

We'd really appreciate if you could take a moment to share your experience with the community.

Your review helps other dancers find great hosts!

- The Strictly Dancing Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #e11d48; margin: 0 0 24px;">Strictly Dancing</h1>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Hi {recipient_name},</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">You recently had a dance session with <strong>{host_name}</strong> on <strong>{date}</strong>.</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">We'd really appreciate if you could take a moment to share your experience with the community.</p>
        <div style="text-align: center; margin: 32px 0;">
            <a href="#" style="display: inline-block; background: #e11d48; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: bold;">Leave a Review</a>
        </div>
        <p style="color: #6b7280; font-size: 14px;">Your review helps other dancers find great hosts!</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">- The Strictly Dancing Team</p>
    </div>
</body>
</html>
"""

        return subject, plain_text, html_content

    def _template_new_message(self, ctx: dict) -> tuple[str, str, str]:
        """Render new message email template."""
        recipient_name = ctx.get("recipient_name", "there")
        sender_name = ctx.get("sender_name", "Someone")
        message_preview = ctx.get("message_preview", "")

        # Truncate preview if too long
        if len(message_preview) > 100:
            message_preview = message_preview[:100] + "..."

        subject = f"New message from {sender_name}"

        plain_text = f"""Hi {recipient_name},

You have a new message from {sender_name}:

"{message_preview}"

Log in to reply.

- The Strictly Dancing Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #e11d48; margin: 0 0 24px;">Strictly Dancing</h1>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Hi {recipient_name},</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">You have a new message from <strong>{sender_name}</strong>:</p>
        <div style="background: #f9fafb; border-radius: 8px; padding: 20px; margin: 24px 0; border-left: 4px solid #e11d48;">
            <p style="margin: 0; color: #4b5563; font-style: italic;">"{message_preview}"</p>
        </div>
        <div style="text-align: center; margin: 32px 0;">
            <a href="#" style="display: inline-block; background: #e11d48; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: bold;">Reply Now</a>
        </div>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">- The Strictly Dancing Team</p>
    </div>
</body>
</html>
"""

        return subject, plain_text, html_content

    def _template_welcome(self, ctx: dict) -> tuple[str, str, str]:
        """Render welcome email template."""
        name = ctx.get("name", "there")

        subject = "Welcome to Strictly Dancing!"

        plain_text = f"""Hi {name},

Welcome to Strictly Dancing - the global marketplace for dance hosts!

Whether you're looking to improve your skills, explore a new city, or just have fun on the dance floor, we're here to connect you with amazing hosts around the world.

Here's how to get started:
1. Complete your profile
2. Browse dance hosts near you
3. Book your first session

Have questions? Just reply to this email.

Happy dancing!

- The Strictly Dancing Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #e11d48; margin: 0 0 24px;">Welcome to Strictly Dancing!</h1>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Hi {name},</p>
        <p style="color: #374151; font-size: 16px; line-height: 1.5;">Whether you're looking to improve your skills, explore a new city, or just have fun on the dance floor, we're here to connect you with amazing hosts around the world.</p>
        <div style="background: #f9fafb; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <h3 style="margin: 0 0 12px; color: #111827;">Here's how to get started:</h3>
            <ol style="margin: 0; padding-left: 20px; color: #4b5563;">
                <li style="margin-bottom: 8px;">Complete your profile</li>
                <li style="margin-bottom: 8px;">Browse dance hosts near you</li>
                <li>Book your first session</li>
            </ol>
        </div>
        <div style="text-align: center; margin: 32px 0;">
            <a href="#" style="display: inline-block; background: #e11d48; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: bold;">Find Hosts</a>
        </div>
        <p style="color: #6b7280; font-size: 14px;">Have questions? Just reply to this email.</p>
        <p style="color: #6b7280; font-size: 14px;">Happy dancing! 💃🕺</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">- The Strictly Dancing Team</p>
    </div>
</body>
</html>
"""

        return subject, plain_text, html_content


def _create_email_service() -> EmailService:
    """Create email service from application settings."""
    settings = get_settings()

    # Use SendGrid if API key is configured
    if settings.sendgrid_api_key:
        provider = SendGridProvider(
            api_key=settings.sendgrid_api_key,
            from_email=settings.email_from_address,
            from_name=settings.email_from_name,
        )
    else:
        # Fall back to console provider for development
        provider = ConsoleEmailProvider()

    return EmailService(provider)


# Singleton instance for convenience
email_service = _create_email_service()
