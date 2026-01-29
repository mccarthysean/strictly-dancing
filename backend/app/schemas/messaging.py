"""Pydantic schemas for messaging operations."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.conversation import MessageType

# --- User Summary for Messaging ---


class MessageUserSummary(BaseModel):
    """Condensed user info for messaging responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User UUID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")


# --- Request Schemas ---


class StartConversationRequest(BaseModel):
    """Schema for starting a new conversation with a user.

    Creates a conversation if one doesn't exist, or returns existing one.
    """

    participant_id: str = Field(
        ..., description="UUID of the user to start conversation with"
    )
    initial_message: str | None = Field(
        default=None,
        min_length=1,
        max_length=5000,
        description="Optional initial message to send",
    )

    @field_validator("participant_id")
    @classmethod
    def validate_participant_id(cls, v: str) -> str:
        """Validate participant_id is not empty."""
        if not v.strip():
            msg = "participant_id cannot be empty"
            raise ValueError(msg)
        return v


class CreateMessageRequest(BaseModel):
    """Schema for creating a new message in a conversation."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Message content",
    )
    message_type: MessageType = Field(
        default=MessageType.TEXT,
        description="Type of message (default: text)",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, v: str) -> str:
        """Validate content is not just whitespace."""
        if not v.strip():
            msg = "Message content cannot be blank"
            raise ValueError(msg)
        return v


# --- Response Schemas ---


class MessageResponse(BaseModel):
    """Schema for a message in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Message UUID")
    conversation_id: str = Field(..., description="Conversation UUID")
    sender_id: str = Field(..., description="Sender user UUID")
    content: str = Field(..., description="Message content")
    message_type: MessageType = Field(..., description="Type of message")
    read_at: datetime | None = Field(None, description="When the message was read")
    created_at: datetime = Field(..., description="When the message was sent")
    updated_at: datetime = Field(..., description="Last update timestamp")


class MessageWithSenderResponse(MessageResponse):
    """Message response with sender details."""

    sender: MessageUserSummary | None = Field(None, description="Sender details")


class ConversationResponse(BaseModel):
    """Schema for a conversation in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Conversation UUID")
    participant_1_id: str = Field(..., description="First participant UUID")
    participant_2_id: str = Field(..., description="Second participant UUID")
    last_message_at: datetime | None = Field(
        None, description="When the last message was sent"
    )
    last_message_preview: str | None = Field(
        None, description="Preview of the last message"
    )
    participant_1_unread_count: int = Field(
        ..., description="Unread count for participant 1"
    )
    participant_2_unread_count: int = Field(
        ..., description="Unread count for participant 2"
    )
    created_at: datetime = Field(..., description="When conversation was created")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ConversationWithParticipantsResponse(ConversationResponse):
    """Conversation response with participant details."""

    participant_1: MessageUserSummary | None = Field(
        None, description="First participant details"
    )
    participant_2: MessageUserSummary | None = Field(
        None, description="Second participant details"
    )


class ConversationSummaryResponse(BaseModel):
    """Summary response for conversation list views.

    Includes the other participant and unread count for the current user.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Conversation UUID")
    other_participant: MessageUserSummary = Field(
        ..., description="The other participant in the conversation"
    )
    last_message_at: datetime | None = Field(
        None, description="When the last message was sent"
    )
    last_message_preview: str | None = Field(
        None, description="Preview of the last message"
    )
    unread_count: int = Field(..., description="Number of unread messages")
    created_at: datetime = Field(..., description="When conversation was created")


class ConversationWithMessagesResponse(ConversationWithParticipantsResponse):
    """Conversation response with messages included."""

    messages: list[MessageWithSenderResponse] = Field(
        default_factory=list, description="Messages in the conversation"
    )


# --- Paginated Response Schemas ---


class ConversationListResponse(BaseModel):
    """Cursor-based paginated response for conversation list."""

    items: list[ConversationSummaryResponse] = Field(
        ..., description="List of conversations"
    )
    next_cursor: str | None = Field(
        None, description="Cursor for next page (conversation ID)"
    )
    has_more: bool = Field(
        ..., description="Whether there are more results after this page"
    )
    limit: int = Field(..., description="Maximum number of results per page")


class MessageListResponse(BaseModel):
    """Cursor-based paginated response for message list."""

    items: list[MessageWithSenderResponse] = Field(..., description="List of messages")
    next_cursor: str | None = Field(
        None, description="Cursor for next page (message ID)"
    )
    has_more: bool = Field(
        ..., description="Whether there are more results after this page"
    )
    limit: int = Field(..., description="Maximum number of results per page")


# --- Unread Count Response ---


class UnreadCountResponse(BaseModel):
    """Response for unread message count."""

    total_unread: int = Field(
        ..., description="Total unread messages across all conversations"
    )
