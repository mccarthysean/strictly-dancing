"""Unit tests for messaging Pydantic schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.conversation import MessageType
from app.schemas.messaging import (
    ConversationListResponse,
    ConversationResponse,
    ConversationSummaryResponse,
    ConversationWithMessagesResponse,
    ConversationWithParticipantsResponse,
    CreateMessageRequest,
    MessageListResponse,
    MessageResponse,
    MessageUserSummary,
    MessageWithSenderResponse,
    StartConversationRequest,
    UnreadCountResponse,
)


class TestMessageUserSummary:
    """Tests for MessageUserSummary schema."""

    def test_valid_user_summary(self):
        """Test creating a valid user summary."""
        summary = MessageUserSummary(
            id="123e4567-e89b-12d3-a456-426614174000",
            first_name="John",
            last_name="Doe",
        )
        assert summary.id == "123e4567-e89b-12d3-a456-426614174000"
        assert summary.first_name == "John"
        assert summary.last_name == "Doe"

    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            MessageUserSummary(id="123")  # Missing first_name and last_name


class TestStartConversationRequest:
    """Tests for StartConversationRequest schema."""

    def test_valid_request_without_message(self):
        """Test creating request without initial message."""
        request = StartConversationRequest(
            participant_id="123e4567-e89b-12d3-a456-426614174000"
        )
        assert request.participant_id == "123e4567-e89b-12d3-a456-426614174000"
        assert request.initial_message is None

    def test_valid_request_with_message(self):
        """Test creating request with initial message."""
        request = StartConversationRequest(
            participant_id="123e4567-e89b-12d3-a456-426614174000",
            initial_message="Hello, I'd like to book a session!",
        )
        assert request.participant_id == "123e4567-e89b-12d3-a456-426614174000"
        assert request.initial_message == "Hello, I'd like to book a session!"

    def test_empty_participant_id_rejected(self):
        """Test that empty participant_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StartConversationRequest(participant_id="   ")
        assert "participant_id cannot be empty" in str(exc_info.value)

    def test_missing_participant_id_rejected(self):
        """Test that missing participant_id is rejected."""
        with pytest.raises(ValidationError):
            StartConversationRequest()

    def test_message_too_long_rejected(self):
        """Test that message exceeding 5000 chars is rejected."""
        with pytest.raises(ValidationError):
            StartConversationRequest(
                participant_id="123e4567-e89b-12d3-a456-426614174000",
                initial_message="a" * 5001,
            )

    def test_empty_message_rejected(self):
        """Test that empty initial message is rejected."""
        with pytest.raises(ValidationError):
            StartConversationRequest(
                participant_id="123e4567-e89b-12d3-a456-426614174000",
                initial_message="",
            )


class TestCreateMessageRequest:
    """Tests for CreateMessageRequest schema."""

    def test_valid_text_message(self):
        """Test creating a valid text message."""
        request = CreateMessageRequest(content="Hello!")
        assert request.content == "Hello!"
        assert request.message_type == MessageType.TEXT

    def test_valid_message_with_type(self):
        """Test creating message with explicit type."""
        request = CreateMessageRequest(
            content="Your booking has been confirmed!",
            message_type=MessageType.BOOKING_CONFIRMED,
        )
        assert request.content == "Your booking has been confirmed!"
        assert request.message_type == MessageType.BOOKING_CONFIRMED

    def test_empty_content_rejected(self):
        """Test that empty content is rejected."""
        with pytest.raises(ValidationError):
            CreateMessageRequest(content="")

    def test_whitespace_only_content_rejected(self):
        """Test that whitespace-only content is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CreateMessageRequest(content="   \t\n   ")
        assert "Message content cannot be blank" in str(exc_info.value)

    def test_content_too_long_rejected(self):
        """Test that content exceeding 5000 chars is rejected."""
        with pytest.raises(ValidationError):
            CreateMessageRequest(content="a" * 5001)

    def test_valid_content_at_max_length(self):
        """Test that content at exactly 5000 chars is valid."""
        request = CreateMessageRequest(content="a" * 5000)
        assert len(request.content) == 5000

    def test_all_message_types_valid(self):
        """Test that all message types are valid."""
        for msg_type in MessageType:
            request = CreateMessageRequest(content="Test", message_type=msg_type)
            assert request.message_type == msg_type


class TestMessageResponse:
    """Tests for MessageResponse schema."""

    def test_valid_message_response(self):
        """Test creating a valid message response."""
        now = datetime.now(UTC)
        response = MessageResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            conversation_id="223e4567-e89b-12d3-a456-426614174000",
            sender_id="323e4567-e89b-12d3-a456-426614174000",
            content="Hello!",
            message_type=MessageType.TEXT,
            read_at=None,
            created_at=now,
            updated_at=now,
        )
        assert response.id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.conversation_id == "223e4567-e89b-12d3-a456-426614174000"
        assert response.sender_id == "323e4567-e89b-12d3-a456-426614174000"
        assert response.content == "Hello!"
        assert response.message_type == MessageType.TEXT
        assert response.read_at is None

    def test_message_response_with_read_at(self):
        """Test message response with read timestamp."""
        now = datetime.now(UTC)
        response = MessageResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            conversation_id="223e4567-e89b-12d3-a456-426614174000",
            sender_id="323e4567-e89b-12d3-a456-426614174000",
            content="Hello!",
            message_type=MessageType.TEXT,
            read_at=now,
            created_at=now,
            updated_at=now,
        )
        assert response.read_at == now


class TestMessageWithSenderResponse:
    """Tests for MessageWithSenderResponse schema."""

    def test_message_with_sender(self):
        """Test message response with sender details."""
        now = datetime.now(UTC)
        response = MessageWithSenderResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            conversation_id="223e4567-e89b-12d3-a456-426614174000",
            sender_id="323e4567-e89b-12d3-a456-426614174000",
            content="Hello!",
            message_type=MessageType.TEXT,
            read_at=None,
            created_at=now,
            updated_at=now,
            sender=MessageUserSummary(
                id="323e4567-e89b-12d3-a456-426614174000",
                first_name="John",
                last_name="Doe",
            ),
        )
        assert response.sender is not None
        assert response.sender.first_name == "John"


class TestConversationResponse:
    """Tests for ConversationResponse schema."""

    def test_valid_conversation_response(self):
        """Test creating a valid conversation response."""
        now = datetime.now(UTC)
        response = ConversationResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            participant_1_id="223e4567-e89b-12d3-a456-426614174000",
            participant_2_id="323e4567-e89b-12d3-a456-426614174000",
            last_message_at=now,
            last_message_preview="Hello!",
            participant_1_unread_count=0,
            participant_2_unread_count=2,
            created_at=now,
            updated_at=now,
        )
        assert response.id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.participant_1_unread_count == 0
        assert response.participant_2_unread_count == 2

    def test_conversation_without_messages(self):
        """Test new conversation without messages."""
        now = datetime.now(UTC)
        response = ConversationResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            participant_1_id="223e4567-e89b-12d3-a456-426614174000",
            participant_2_id="323e4567-e89b-12d3-a456-426614174000",
            last_message_at=None,
            last_message_preview=None,
            participant_1_unread_count=0,
            participant_2_unread_count=0,
            created_at=now,
            updated_at=now,
        )
        assert response.last_message_at is None
        assert response.last_message_preview is None


class TestConversationWithParticipantsResponse:
    """Tests for ConversationWithParticipantsResponse schema."""

    def test_conversation_with_participants(self):
        """Test conversation with participant details."""
        now = datetime.now(UTC)
        response = ConversationWithParticipantsResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            participant_1_id="223e4567-e89b-12d3-a456-426614174000",
            participant_2_id="323e4567-e89b-12d3-a456-426614174000",
            last_message_at=now,
            last_message_preview="Hello!",
            participant_1_unread_count=0,
            participant_2_unread_count=2,
            created_at=now,
            updated_at=now,
            participant_1=MessageUserSummary(
                id="223e4567-e89b-12d3-a456-426614174000",
                first_name="John",
                last_name="Doe",
            ),
            participant_2=MessageUserSummary(
                id="323e4567-e89b-12d3-a456-426614174000",
                first_name="Jane",
                last_name="Smith",
            ),
        )
        assert response.participant_1 is not None
        assert response.participant_1.first_name == "John"
        assert response.participant_2 is not None
        assert response.participant_2.first_name == "Jane"


class TestConversationSummaryResponse:
    """Tests for ConversationSummaryResponse schema."""

    def test_valid_conversation_summary(self):
        """Test creating a valid conversation summary."""
        now = datetime.now(UTC)
        response = ConversationSummaryResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            other_participant=MessageUserSummary(
                id="323e4567-e89b-12d3-a456-426614174000",
                first_name="Jane",
                last_name="Smith",
            ),
            last_message_at=now,
            last_message_preview="Hello!",
            unread_count=3,
            created_at=now,
        )
        assert response.other_participant.first_name == "Jane"
        assert response.unread_count == 3


class TestConversationWithMessagesResponse:
    """Tests for ConversationWithMessagesResponse schema."""

    def test_conversation_with_messages(self):
        """Test conversation with messages included."""
        now = datetime.now(UTC)
        response = ConversationWithMessagesResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            participant_1_id="223e4567-e89b-12d3-a456-426614174000",
            participant_2_id="323e4567-e89b-12d3-a456-426614174000",
            last_message_at=now,
            last_message_preview="How are you?",
            participant_1_unread_count=0,
            participant_2_unread_count=0,
            created_at=now,
            updated_at=now,
            messages=[
                MessageWithSenderResponse(
                    id="msg1",
                    conversation_id="123e4567-e89b-12d3-a456-426614174000",
                    sender_id="223e4567-e89b-12d3-a456-426614174000",
                    content="Hello!",
                    message_type=MessageType.TEXT,
                    read_at=now,
                    created_at=now,
                    updated_at=now,
                ),
                MessageWithSenderResponse(
                    id="msg2",
                    conversation_id="123e4567-e89b-12d3-a456-426614174000",
                    sender_id="323e4567-e89b-12d3-a456-426614174000",
                    content="How are you?",
                    message_type=MessageType.TEXT,
                    read_at=None,
                    created_at=now,
                    updated_at=now,
                ),
            ],
        )
        assert len(response.messages) == 2
        assert response.messages[0].content == "Hello!"
        assert response.messages[1].content == "How are you?"


class TestConversationListResponse:
    """Tests for ConversationListResponse schema."""

    def test_valid_list_response(self):
        """Test creating a valid conversation list response."""
        now = datetime.now(UTC)
        response = ConversationListResponse(
            items=[
                ConversationSummaryResponse(
                    id="conv1",
                    other_participant=MessageUserSummary(
                        id="user1", first_name="John", last_name="Doe"
                    ),
                    last_message_at=now,
                    last_message_preview="Hello!",
                    unread_count=2,
                    created_at=now,
                ),
            ],
            next_cursor="conv2",
            has_more=True,
            limit=20,
        )
        assert len(response.items) == 1
        assert response.next_cursor == "conv2"
        assert response.has_more is True

    def test_empty_list_response(self):
        """Test empty conversation list response."""
        response = ConversationListResponse(
            items=[],
            next_cursor=None,
            has_more=False,
            limit=20,
        )
        assert len(response.items) == 0
        assert response.next_cursor is None
        assert response.has_more is False


class TestMessageListResponse:
    """Tests for MessageListResponse schema."""

    def test_valid_message_list(self):
        """Test creating a valid message list response."""
        now = datetime.now(UTC)
        response = MessageListResponse(
            items=[
                MessageWithSenderResponse(
                    id="msg1",
                    conversation_id="conv1",
                    sender_id="user1",
                    content="Hello!",
                    message_type=MessageType.TEXT,
                    read_at=None,
                    created_at=now,
                    updated_at=now,
                ),
            ],
            next_cursor="msg2",
            has_more=True,
            limit=50,
        )
        assert len(response.items) == 1
        assert response.next_cursor == "msg2"
        assert response.has_more is True
        assert response.limit == 50

    def test_empty_message_list(self):
        """Test empty message list response."""
        response = MessageListResponse(
            items=[],
            next_cursor=None,
            has_more=False,
            limit=50,
        )
        assert len(response.items) == 0


class TestUnreadCountResponse:
    """Tests for UnreadCountResponse schema."""

    def test_valid_unread_count(self):
        """Test creating valid unread count response."""
        response = UnreadCountResponse(total_unread=5)
        assert response.total_unread == 5

    def test_zero_unread_count(self):
        """Test zero unread messages."""
        response = UnreadCountResponse(total_unread=0)
        assert response.total_unread == 0
