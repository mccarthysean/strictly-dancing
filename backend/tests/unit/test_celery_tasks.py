"""Tests for Celery background tasks."""

from unittest.mock import patch


class TestCeleryAppConfiguration:
    """Tests for Celery app configuration."""

    def test_celery_app_exists(self):
        """Test that Celery app is properly configured."""
        from app.workers.celery import celery_app

        assert celery_app is not None
        assert celery_app.main == "strictly_dancing"

    def test_celery_broker_url_from_settings(self):
        """Test that Celery uses Redis URL from settings."""
        from app.workers.celery import celery_app

        # Should use redis URL
        assert "redis" in str(celery_app.conf.broker_url).lower()

    def test_celery_result_backend_configured(self):
        """Test that result backend is configured."""
        from app.workers.celery import celery_app

        assert celery_app.conf.result_backend is not None

    def test_celery_serializer_is_json(self):
        """Test that task serializer is JSON."""
        from app.workers.celery import celery_app

        assert celery_app.conf.task_serializer == "json"

    def test_celery_timezone_is_utc(self):
        """Test that timezone is UTC."""
        from app.workers.celery import celery_app

        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True

    def test_celery_includes_tasks_module(self):
        """Test that tasks module is included."""
        from app.workers.celery import celery_app

        assert "app.workers.tasks" in celery_app.conf.include

    def test_celery_beat_schedule_exists(self):
        """Test that beat schedule is configured."""
        from app.workers.celery import celery_app

        assert celery_app.conf.beat_schedule is not None
        assert "send-session-reminders" in celery_app.conf.beat_schedule


class TestSendEmailTask:
    """Tests for send_email_task."""

    def test_send_email_task_exists(self):
        """Test that send_email_task is registered."""
        from app.workers.tasks import send_email_task

        assert send_email_task is not None
        assert send_email_task.name == "app.workers.tasks.send_email_task"

    def test_send_email_task_has_max_retries(self):
        """Test that task has retry configuration."""
        from app.workers.tasks import send_email_task

        assert send_email_task.max_retries == 3

    @patch("app.workers.tasks.logger")
    def test_send_email_task_runs_successfully(self, mock_logger):
        """Test that task runs and returns correct structure."""
        from app.workers.tasks import send_email_task

        # Run task synchronously (without Celery worker)
        result = send_email_task.apply(
            args=("test@example.com", "Test Subject", "Test body"),
        ).get()

        assert result["status"] == "sent"
        assert result["to"] == "test@example.com"
        assert result["subject"] == "Test Subject"
        assert "message_id" in result

    @patch("app.workers.tasks.logger")
    def test_send_email_task_with_html_body(self, mock_logger):
        """Test task with HTML body."""
        from app.workers.tasks import send_email_task

        result = send_email_task.apply(
            args=("user@test.com", "Hello", "Plain body"),
            kwargs={"html_body": "<p>HTML body</p>"},
        ).get()

        assert result["status"] == "sent"


class TestBookingNotificationEmailTask:
    """Tests for send_booking_notification_email task."""

    def test_task_exists(self):
        """Test that task is registered."""
        from app.workers.tasks import send_booking_notification_email

        assert send_booking_notification_email is not None

    @patch("app.workers.tasks.send_email_task.delay")
    @patch("app.workers.tasks.logger")
    def test_task_queues_email(self, mock_logger, mock_send_email_delay):
        """Test that task queues email via send_email_task."""
        from app.workers.tasks import send_booking_notification_email

        result = send_booking_notification_email.apply(
            args=(
                "booking-123",
                "confirmed",
                "client@test.com",
                "John",
            ),
        ).get()

        assert result["status"] == "queued"
        assert result["booking_id"] == "booking-123"
        assert result["type"] == "confirmed"

        mock_send_email_delay.assert_called_once()

    @patch("app.workers.tasks.send_email_task.delay")
    @patch("app.workers.tasks.logger")
    def test_task_handles_different_notification_types(
        self, mock_logger, mock_send_email_delay
    ):
        """Test that task handles various notification types."""
        from app.workers.tasks import send_booking_notification_email

        notification_types = [
            "created",
            "confirmed",
            "cancelled",
            "completed",
            "reminder",
        ]

        for notification_type in notification_types:
            mock_send_email_delay.reset_mock()

            result = send_booking_notification_email.apply(
                args=(
                    f"booking-{notification_type}",
                    notification_type,
                    "test@test.com",
                    "Test",
                ),
            ).get()

            assert result["type"] == notification_type
            mock_send_email_delay.assert_called_once()


class TestMessageNotificationEmailTask:
    """Tests for send_message_notification_email task."""

    def test_task_exists(self):
        """Test that task is registered."""
        from app.workers.tasks import send_message_notification_email

        assert send_message_notification_email is not None

    @patch("app.workers.tasks.send_email_task.delay")
    @patch("app.workers.tasks.logger")
    def test_task_queues_email(self, mock_logger, mock_send_email_delay):
        """Test that task queues email."""
        from app.workers.tasks import send_message_notification_email

        result = send_message_notification_email.apply(
            args=(
                "conv-123",
                "Jane",
                "john@test.com",
                "John",
                "Hello, are you available?",
            ),
        ).get()

        assert result["status"] == "queued"
        assert result["conversation_id"] == "conv-123"

        mock_send_email_delay.assert_called_once()

    @patch("app.workers.tasks.send_email_task.delay")
    @patch("app.workers.tasks.logger")
    def test_task_truncates_long_message_preview(
        self, mock_logger, mock_send_email_delay
    ):
        """Test that long messages are truncated in preview."""
        from app.workers.tasks import send_message_notification_email

        long_message = "A" * 200  # 200 character message

        send_message_notification_email.apply(
            args=(
                "conv-123",
                "Jane",
                "john@test.com",
                "John",
                long_message,
            ),
        ).get()

        # Verify the email body contains truncated message
        call_args = mock_send_email_delay.call_args
        body = call_args.kwargs["body"]
        assert "..." in body


class TestSessionRemindersTask:
    """Tests for send_session_reminders_task."""

    def test_task_exists(self):
        """Test that task is registered."""
        from app.workers.tasks import send_session_reminders_task

        assert send_session_reminders_task is not None

    @patch("app.workers.tasks.logger")
    def test_task_returns_completed_status(self, mock_logger):
        """Test that task returns completed status."""
        from app.workers.tasks import send_session_reminders_task

        result = send_session_reminders_task.apply().get()

        assert result["status"] == "completed"
        assert "reminders_sent" in result

    @patch("app.workers.tasks.logger")
    def test_task_logs_execution(self, mock_logger):
        """Test that task logs its execution."""
        from app.workers.tasks import send_session_reminders_task

        send_session_reminders_task.apply().get()

        # Should log start and completion
        assert mock_logger.info.call_count >= 2


class TestWorkersModuleExports:
    """Tests for workers module exports."""

    def test_celery_app_exported(self):
        """Test that celery_app is exported from module."""
        from app.workers import celery_app

        assert celery_app is not None

    def test_send_email_task_exported(self):
        """Test that send_email_task is exported from module."""
        from app.workers import send_email_task

        assert send_email_task is not None


class TestCeleryTaskExecution:
    """Tests for Celery task synchronous execution."""

    @patch("app.workers.tasks.logger")
    def test_celery_task_runs_synchronously(self, mock_logger):
        """Test that tasks can be run synchronously for testing."""
        from app.workers.tasks import send_email_task

        # apply() runs task synchronously
        result = send_email_task.apply(
            args=("sync-test@example.com", "Sync Test", "Testing sync execution"),
        )

        # get() retrieves the result
        task_result = result.get()

        assert task_result["status"] == "sent"
        assert result.successful()
