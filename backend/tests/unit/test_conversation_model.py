"""Unit tests for the Conversation and Message database models."""

from datetime import UTC, datetime

from app.models.conversation import Conversation, Message, MessageType


class TestMessageType:
    """Tests for MessageType enum."""

    def test_message_type_has_text(self) -> None:
        """Test that MessageType has TEXT value."""
        assert MessageType.TEXT.value == "text"

    def test_message_type_has_system(self) -> None:
        """Test that MessageType has SYSTEM value."""
        assert MessageType.SYSTEM.value == "system"

    def test_message_type_has_booking_request(self) -> None:
        """Test that MessageType has BOOKING_REQUEST value."""
        assert MessageType.BOOKING_REQUEST.value == "booking_request"

    def test_message_type_has_booking_confirmed(self) -> None:
        """Test that MessageType has BOOKING_CONFIRMED value."""
        assert MessageType.BOOKING_CONFIRMED.value == "booking_confirmed"

    def test_message_type_has_booking_cancelled(self) -> None:
        """Test that MessageType has BOOKING_CANCELLED value."""
        assert MessageType.BOOKING_CANCELLED.value == "booking_cancelled"

    def test_message_type_is_string_enum(self) -> None:
        """Test that MessageType is a string enum."""
        assert isinstance(MessageType.TEXT, str)
        assert isinstance(MessageType.TEXT.value, str)

    def test_message_type_count(self) -> None:
        """Test that MessageType has exactly 5 values."""
        assert len(list(MessageType)) == 5


class TestConversationModel:
    """Tests for Conversation model definition."""

    def test_conversation_model_instantiation(self) -> None:
        """Test that Conversation model can be instantiated with required fields."""
        # participant_1_id must be less than participant_2_id
        conversation = Conversation(
            participant_1_id="11111111-1111-1111-1111-111111111111",
            participant_2_id="22222222-2222-2222-2222-222222222222",
        )

        assert conversation.participant_1_id == "11111111-1111-1111-1111-111111111111"
        assert conversation.participant_2_id == "22222222-2222-2222-2222-222222222222"

    def test_conversation_model_with_all_fields(self) -> None:
        """Test that Conversation model can be instantiated with all fields."""
        now = datetime.now(UTC)
        conversation = Conversation(
            participant_1_id="11111111-1111-1111-1111-111111111111",
            participant_2_id="22222222-2222-2222-2222-222222222222",
            last_message_at=now,
            last_message_preview="Hello, how are you?",
            participant_1_unread_count=2,
            participant_2_unread_count=0,
        )

        assert conversation.participant_1_id == "11111111-1111-1111-1111-111111111111"
        assert conversation.participant_2_id == "22222222-2222-2222-2222-222222222222"
        assert conversation.last_message_at == now
        assert conversation.last_message_preview == "Hello, how are you?"
        assert conversation.participant_1_unread_count == 2
        assert conversation.participant_2_unread_count == 0

    def test_conversation_model_has_required_fields(self) -> None:
        """Test that Conversation model has all required fields."""
        columns = Conversation.__table__.columns.keys()

        required_fields = [
            "id",
            "participant_1_id",
            "participant_2_id",
            "last_message_at",
            "last_message_preview",
            "participant_1_unread_count",
            "participant_2_unread_count",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in columns, f"Missing field: {field}"

    def test_conversation_model_tablename(self) -> None:
        """Test that Conversation model has correct tablename."""
        assert Conversation.__tablename__ == "conversations"

    def test_conversation_participant_1_id_is_uuid(self) -> None:
        """Test that participant_1_id column is UUID type."""
        column = Conversation.__table__.columns["participant_1_id"]
        assert "UUID" in str(column.type)

    def test_conversation_participant_2_id_is_uuid(self) -> None:
        """Test that participant_2_id column is UUID type."""
        column = Conversation.__table__.columns["participant_2_id"]
        assert "UUID" in str(column.type)

    def test_conversation_participant_1_id_not_nullable(self) -> None:
        """Test that participant_1_id is not nullable."""
        column = Conversation.__table__.columns["participant_1_id"]
        assert not column.nullable

    def test_conversation_participant_2_id_not_nullable(self) -> None:
        """Test that participant_2_id is not nullable."""
        column = Conversation.__table__.columns["participant_2_id"]
        assert not column.nullable

    def test_conversation_last_message_at_nullable(self) -> None:
        """Test that last_message_at is nullable."""
        column = Conversation.__table__.columns["last_message_at"]
        assert column.nullable

    def test_conversation_last_message_preview_nullable(self) -> None:
        """Test that last_message_preview is nullable."""
        column = Conversation.__table__.columns["last_message_preview"]
        assert column.nullable

    def test_conversation_repr(self) -> None:
        """Test Conversation __repr__ method."""
        conversation = Conversation(
            id="33333333-3333-3333-3333-333333333333",
            participant_1_id="11111111-1111-1111-1111-111111111111",
            participant_2_id="22222222-2222-2222-2222-222222222222",
        )
        repr_str = repr(conversation)

        assert "Conversation" in repr_str
        assert "33333333-3333-3333-3333-333333333333" in repr_str
        assert "11111111-1111-1111-1111-111111111111" in repr_str
        assert "22222222-2222-2222-2222-222222222222" in repr_str

    def test_conversation_get_other_participant_id_for_participant_1(self) -> None:
        """Test get_other_participant_id returns participant_2 for participant_1."""
        conversation = Conversation(
            participant_1_id="11111111-1111-1111-1111-111111111111",
            participant_2_id="22222222-2222-2222-2222-222222222222",
        )

        result = conversation.get_other_participant_id(
            "11111111-1111-1111-1111-111111111111"
        )
        assert result == "22222222-2222-2222-2222-222222222222"

    def test_conversation_get_other_participant_id_for_participant_2(self) -> None:
        """Test get_other_participant_id returns participant_1 for participant_2."""
        conversation = Conversation(
            participant_1_id="11111111-1111-1111-1111-111111111111",
            participant_2_id="22222222-2222-2222-2222-222222222222",
        )

        result = conversation.get_other_participant_id(
            "22222222-2222-2222-2222-222222222222"
        )
        assert result == "11111111-1111-1111-1111-111111111111"

    def test_conversation_get_other_participant_id_for_non_participant(self) -> None:
        """Test get_other_participant_id returns None for non-participant."""
        conversation = Conversation(
            participant_1_id="11111111-1111-1111-1111-111111111111",
            participant_2_id="22222222-2222-2222-2222-222222222222",
        )

        result = conversation.get_other_participant_id(
            "33333333-3333-3333-3333-333333333333"
        )
        assert result is None

    def test_conversation_is_participant_returns_true_for_participant_1(self) -> None:
        """Test is_participant returns True for participant_1."""
        conversation = Conversation(
            participant_1_id="11111111-1111-1111-1111-111111111111",
            participant_2_id="22222222-2222-2222-2222-222222222222",
        )

        assert conversation.is_participant("11111111-1111-1111-1111-111111111111")

    def test_conversation_is_participant_returns_true_for_participant_2(self) -> None:
        """Test is_participant returns True for participant_2."""
        conversation = Conversation(
            participant_1_id="11111111-1111-1111-1111-111111111111",
            participant_2_id="22222222-2222-2222-2222-222222222222",
        )

        assert conversation.is_participant("22222222-2222-2222-2222-222222222222")

    def test_conversation_is_participant_returns_false_for_non_participant(
        self,
    ) -> None:
        """Test is_participant returns False for non-participant."""
        conversation = Conversation(
            participant_1_id="11111111-1111-1111-1111-111111111111",
            participant_2_id="22222222-2222-2222-2222-222222222222",
        )

        assert not conversation.is_participant("33333333-3333-3333-3333-333333333333")

    def test_conversation_has_unique_constraint_on_participants(self) -> None:
        """Test that Conversation has unique constraint on participant pair."""
        constraints = [c.name for c in Conversation.__table__.constraints]
        assert "uq_conversations_participants" in constraints

    def test_conversation_has_check_constraint_for_participant_order(self) -> None:
        """Test that Conversation has check constraint for participant order."""
        constraints = [c.name for c in Conversation.__table__.constraints]
        assert "ck_conversations_participant_order" in constraints

    def test_conversation_default_unread_count_is_zero(self) -> None:
        """Test that default unread counts are zero."""
        # Default values are applied at the database level, so checking column defaults
        col1 = Conversation.__table__.columns["participant_1_unread_count"]
        col2 = Conversation.__table__.columns["participant_2_unread_count"]
        assert col1.default.arg == 0
        assert col2.default.arg == 0


class TestMessageModel:
    """Tests for Message model definition."""

    def test_message_model_instantiation(self) -> None:
        """Test that Message model can be instantiated with required fields."""
        message = Message(
            conversation_id="11111111-1111-1111-1111-111111111111",
            sender_id="22222222-2222-2222-2222-222222222222",
            content="Hello, I'd like to book a lesson.",
        )

        assert message.conversation_id == "11111111-1111-1111-1111-111111111111"
        assert message.sender_id == "22222222-2222-2222-2222-222222222222"
        assert message.content == "Hello, I'd like to book a lesson."

    def test_message_model_with_all_fields(self) -> None:
        """Test that Message model can be instantiated with all fields."""
        now = datetime.now(UTC)
        message = Message(
            conversation_id="11111111-1111-1111-1111-111111111111",
            sender_id="22222222-2222-2222-2222-222222222222",
            content="Your booking has been confirmed.",
            message_type=MessageType.BOOKING_CONFIRMED,
            read_at=now,
        )

        assert message.conversation_id == "11111111-1111-1111-1111-111111111111"
        assert message.sender_id == "22222222-2222-2222-2222-222222222222"
        assert message.content == "Your booking has been confirmed."
        assert message.message_type == MessageType.BOOKING_CONFIRMED
        assert message.read_at == now

    def test_message_model_has_required_fields(self) -> None:
        """Test that Message model has all required fields."""
        columns = Message.__table__.columns.keys()

        required_fields = [
            "id",
            "conversation_id",
            "sender_id",
            "content",
            "message_type",
            "read_at",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in columns, f"Missing field: {field}"

    def test_message_model_tablename(self) -> None:
        """Test that Message model has correct tablename."""
        assert Message.__tablename__ == "messages"

    def test_message_conversation_id_is_uuid(self) -> None:
        """Test that conversation_id column is UUID type."""
        column = Message.__table__.columns["conversation_id"]
        assert "UUID" in str(column.type)

    def test_message_sender_id_is_uuid(self) -> None:
        """Test that sender_id column is UUID type."""
        column = Message.__table__.columns["sender_id"]
        assert "UUID" in str(column.type)

    def test_message_conversation_id_not_nullable(self) -> None:
        """Test that conversation_id is not nullable."""
        column = Message.__table__.columns["conversation_id"]
        assert not column.nullable

    def test_message_sender_id_not_nullable(self) -> None:
        """Test that sender_id is not nullable."""
        column = Message.__table__.columns["sender_id"]
        assert not column.nullable

    def test_message_content_not_nullable(self) -> None:
        """Test that content is not nullable."""
        column = Message.__table__.columns["content"]
        assert not column.nullable

    def test_message_type_not_nullable(self) -> None:
        """Test that message_type is not nullable."""
        column = Message.__table__.columns["message_type"]
        assert not column.nullable

    def test_message_read_at_nullable(self) -> None:
        """Test that read_at is nullable."""
        column = Message.__table__.columns["read_at"]
        assert column.nullable

    def test_message_default_type_is_text(self) -> None:
        """Test that default message_type is TEXT."""
        # Default value should be TEXT
        col = Message.__table__.columns["message_type"]
        assert col.default.arg == MessageType.TEXT

    def test_message_repr(self) -> None:
        """Test Message __repr__ method."""
        message = Message(
            id="33333333-3333-3333-3333-333333333333",
            conversation_id="11111111-1111-1111-1111-111111111111",
            sender_id="22222222-2222-2222-2222-222222222222",
            content="Hello!",
            message_type=MessageType.TEXT,
        )
        repr_str = repr(message)

        assert "Message" in repr_str
        assert "33333333-3333-3333-3333-333333333333" in repr_str
        assert "11111111-1111-1111-1111-111111111111" in repr_str
        assert "TEXT" in repr_str

    def test_message_is_read_returns_false_when_not_read(self) -> None:
        """Test is_read returns False when read_at is None."""
        message = Message(
            conversation_id="11111111-1111-1111-1111-111111111111",
            sender_id="22222222-2222-2222-2222-222222222222",
            content="Hello!",
            read_at=None,
        )

        assert not message.is_read()

    def test_message_is_read_returns_true_when_read(self) -> None:
        """Test is_read returns True when read_at is set."""
        now = datetime.now(UTC)
        message = Message(
            conversation_id="11111111-1111-1111-1111-111111111111",
            sender_id="22222222-2222-2222-2222-222222222222",
            content="Hello!",
            read_at=now,
        )

        assert message.is_read()

    def test_message_content_is_text_type(self) -> None:
        """Test that content column is Text type."""
        column = Message.__table__.columns["content"]
        assert "TEXT" in str(column.type).upper()


class TestConversationMessageRelationships:
    """Tests for relationships between Conversation and Message models."""

    def test_conversation_has_messages_relationship(self) -> None:
        """Test that Conversation has messages relationship."""
        assert hasattr(Conversation, "messages")

    def test_conversation_has_participant_1_relationship(self) -> None:
        """Test that Conversation has participant_1 relationship."""
        assert hasattr(Conversation, "participant_1")

    def test_conversation_has_participant_2_relationship(self) -> None:
        """Test that Conversation has participant_2 relationship."""
        assert hasattr(Conversation, "participant_2")

    def test_message_has_conversation_relationship(self) -> None:
        """Test that Message has conversation relationship."""
        assert hasattr(Message, "conversation")

    def test_message_has_sender_relationship(self) -> None:
        """Test that Message has sender relationship."""
        assert hasattr(Message, "sender")


class TestConversationIndexes:
    """Tests for Conversation model indexes."""

    def test_conversation_has_participant_1_index(self) -> None:
        """Test that Conversation has index on participant_1_id."""
        indexes = [idx.name for idx in Conversation.__table__.indexes]
        assert "ix_conversations_participant_1" in indexes

    def test_conversation_has_participant_2_index(self) -> None:
        """Test that Conversation has index on participant_2_id."""
        indexes = [idx.name for idx in Conversation.__table__.indexes]
        assert "ix_conversations_participant_2" in indexes

    def test_conversation_has_last_message_at_index(self) -> None:
        """Test that Conversation has index on last_message_at."""
        indexes = [idx.name for idx in Conversation.__table__.indexes]
        assert "ix_conversations_last_message_at" in indexes


class TestMessageIndexes:
    """Tests for Message model indexes."""

    def test_message_has_conversation_created_composite_index(self) -> None:
        """Test that Message has composite index on conversation_id and created_at."""
        indexes = [idx.name for idx in Message.__table__.indexes]
        assert "ix_messages_conversation_created" in indexes

    def test_message_has_conversation_read_at_composite_index(self) -> None:
        """Test that Message has composite index on conversation_id and read_at."""
        indexes = [idx.name for idx in Message.__table__.indexes]
        assert "ix_messages_conversation_read_at" in indexes
