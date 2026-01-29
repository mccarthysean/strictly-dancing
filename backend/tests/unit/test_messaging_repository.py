"""Unit tests for MessagingRepository."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message, MessageType
from app.repositories.messaging import MessagingRepository


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    session.execute.return_value = mock_result
    return session


@pytest.fixture
def messaging_repository(mock_session):
    """Create a MessagingRepository with a mock session."""
    return MessagingRepository(mock_session)


@pytest.fixture
def user_1_id():
    """Create a sample user 1 UUID."""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def user_2_id():
    """Create a sample user 2 UUID."""
    return uuid.UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def user_3_id():
    """Create a sample user 3 UUID."""
    return uuid.UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def sample_conversation(user_1_id, user_2_id):
    """Create a sample conversation for testing."""
    conversation = Conversation(
        id=str(uuid.uuid4()),
        participant_1_id=str(user_1_id),
        participant_2_id=str(user_2_id),
        last_message_at=datetime.now(UTC),
        last_message_preview="Hello!",
        participant_1_unread_count=0,
        participant_2_unread_count=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    return conversation


@pytest.fixture
def sample_message(sample_conversation, user_1_id):
    """Create a sample message for testing."""
    message = Message(
        id=str(uuid.uuid4()),
        conversation_id=sample_conversation.id,
        sender_id=str(user_1_id),
        content="Hello, how are you?",
        message_type=MessageType.TEXT,
        read_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    return message


class TestMessagingRepositoryInit:
    """Tests for MessagingRepository initialization."""

    def test_init_stores_session(self, mock_session):
        """Test that init stores the session."""
        repo = MessagingRepository(mock_session)
        assert repo._session == mock_session


class TestGetOrCreateConversation:
    """Tests for MessagingRepository.get_or_create_conversation() method."""

    async def test_get_or_create_returns_existing_conversation(
        self,
        messaging_repository,
        mock_session,
        sample_conversation,
        user_1_id,
        user_2_id,
    ):
        """Test that existing conversation is returned."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        conversation, created = await messaging_repository.get_or_create_conversation(
            user_1_id, user_2_id
        )

        assert conversation == sample_conversation
        assert created is False

    async def test_get_or_create_creates_new_conversation(
        self, messaging_repository, mock_session, user_1_id, user_2_id
    ):
        """Test that new conversation is created when none exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        conversation, created = await messaging_repository.get_or_create_conversation(
            user_1_id, user_2_id
        )

        assert created is True
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    async def test_get_or_create_ensures_participant_ordering(
        self, messaging_repository, mock_session, user_1_id, user_2_id
    ):
        """Test that participants are ordered (smaller UUID first)."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Pass user_2 first, user_1 second (wrong order)
        conversation, created = await messaging_repository.get_or_create_conversation(
            user_2_id, user_1_id
        )

        # The conversation should have user_1 as participant_1 (smaller UUID)
        assert created is True
        # Verify add was called and participant ordering
        added_conversation = mock_session.add.call_args[0][0]
        assert added_conversation.participant_1_id == str(user_1_id)
        assert added_conversation.participant_2_id == str(user_2_id)

    async def test_get_or_create_raises_for_same_user(
        self, messaging_repository, user_1_id
    ):
        """Test that ValueError is raised when user_1_id == user_2_id."""
        with pytest.raises(ValueError, match="Cannot create conversation with self"):
            await messaging_repository.get_or_create_conversation(user_1_id, user_1_id)

    async def test_get_or_create_initializes_unread_counts(
        self, messaging_repository, mock_session, user_1_id, user_2_id
    ):
        """Test that new conversation has zero unread counts."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        conversation, created = await messaging_repository.get_or_create_conversation(
            user_1_id, user_2_id
        )

        assert created is True
        added_conversation = mock_session.add.call_args[0][0]
        assert added_conversation.participant_1_unread_count == 0
        assert added_conversation.participant_2_unread_count == 0


class TestGetConversationById:
    """Tests for MessagingRepository.get_conversation_by_id() method."""

    async def test_get_conversation_by_id_found(
        self, messaging_repository, mock_session, sample_conversation
    ):
        """Test getting conversation by ID when it exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.get_conversation_by_id(
            uuid.UUID(sample_conversation.id)
        )

        assert result == sample_conversation

    async def test_get_conversation_by_id_not_found(
        self, messaging_repository, mock_session
    ):
        """Test getting conversation by ID when it doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.get_conversation_by_id(uuid.uuid4())

        assert result is None


class TestGetConversationsForUser:
    """Tests for MessagingRepository.get_conversations_for_user() method."""

    async def test_get_conversations_returns_list(
        self, messaging_repository, mock_session, sample_conversation, user_1_id
    ):
        """Test that conversations are returned as a list."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_conversation]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.get_conversations_for_user(user_1_id)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == sample_conversation

    async def test_get_conversations_returns_empty_list(
        self, messaging_repository, mock_session, user_1_id
    ):
        """Test that empty list is returned when no conversations."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.get_conversations_for_user(user_1_id)

        assert result == []

    async def test_get_conversations_respects_limit(
        self, messaging_repository, mock_session, user_1_id
    ):
        """Test that limit parameter is respected."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        await messaging_repository.get_conversations_for_user(user_1_id, limit=5)

        mock_session.execute.assert_called_once()


class TestGetMessages:
    """Tests for MessagingRepository.get_messages() method."""

    async def test_get_messages_returns_list(
        self, messaging_repository, mock_session, sample_message, sample_conversation
    ):
        """Test that messages are returned as a list."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_message]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.get_messages(
            uuid.UUID(sample_conversation.id)
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == sample_message

    async def test_get_messages_returns_empty_list(
        self, messaging_repository, mock_session, sample_conversation
    ):
        """Test that empty list is returned when no messages."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.get_messages(
            uuid.UUID(sample_conversation.id)
        )

        assert result == []

    async def test_get_messages_respects_limit(
        self, messaging_repository, mock_session, sample_conversation
    ):
        """Test that limit parameter is respected."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        await messaging_repository.get_messages(
            uuid.UUID(sample_conversation.id), limit=10
        )

        mock_session.execute.assert_called_once()

    async def test_get_messages_with_cursor(
        self, messaging_repository, mock_session, sample_message, sample_conversation
    ):
        """Test cursor-based pagination for messages."""
        # First call returns cursor timestamp, second returns messages
        mock_result_cursor = MagicMock()
        mock_result_cursor.scalar_one_or_none.return_value = datetime.now(UTC)

        mock_result_messages = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result_messages.scalars.return_value = mock_scalars

        mock_session.execute.side_effect = [mock_result_cursor, mock_result_messages]

        cursor_id = uuid.uuid4()
        await messaging_repository.get_messages(
            uuid.UUID(sample_conversation.id), cursor=cursor_id
        )

        assert mock_session.execute.call_count == 2


class TestCreateMessage:
    """Tests for MessagingRepository.create_message() method."""

    async def test_create_message_success(
        self, messaging_repository, mock_session, sample_conversation, user_1_id
    ):
        """Test successful message creation."""
        # Mock get_conversation_by_id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        message = await messaging_repository.create_message(
            conversation_id=uuid.UUID(sample_conversation.id),
            sender_id=user_1_id,
            content="Hello!",
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert message.content == "Hello!"
        assert message.sender_id == str(user_1_id)

    async def test_create_message_updates_conversation_metadata(
        self, messaging_repository, mock_session, sample_conversation, user_1_id
    ):
        """Test that creating message updates conversation last_message_at and preview."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        original_last_message_at = sample_conversation.last_message_at

        await messaging_repository.create_message(
            conversation_id=uuid.UUID(sample_conversation.id),
            sender_id=user_1_id,
            content="New message",
        )

        assert sample_conversation.last_message_at != original_last_message_at
        assert sample_conversation.last_message_preview == "New message"

    async def test_create_message_increments_recipient_unread_count(
        self, messaging_repository, mock_session, sample_conversation, user_1_id
    ):
        """Test that recipient's unread count is incremented."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        original_count = sample_conversation.participant_2_unread_count

        # user_1 is participant_1, so participant_2's count should increase
        await messaging_repository.create_message(
            conversation_id=uuid.UUID(sample_conversation.id),
            sender_id=user_1_id,
            content="Hello!",
        )

        assert sample_conversation.participant_2_unread_count == original_count + 1

    async def test_create_message_with_message_type(
        self, messaging_repository, mock_session, sample_conversation, user_1_id
    ):
        """Test creating message with specific message type."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        message = await messaging_repository.create_message(
            conversation_id=uuid.UUID(sample_conversation.id),
            sender_id=user_1_id,
            content="Booking confirmed!",
            message_type=MessageType.BOOKING_CONFIRMED,
        )

        assert message.message_type == MessageType.BOOKING_CONFIRMED

    async def test_create_message_conversation_not_found_raises(
        self, messaging_repository, mock_session, user_1_id
    ):
        """Test that ValueError is raised when conversation not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Conversation not found"):
            await messaging_repository.create_message(
                conversation_id=uuid.uuid4(),
                sender_id=user_1_id,
                content="Hello!",
            )

    async def test_create_message_sender_not_participant_raises(
        self, messaging_repository, mock_session, sample_conversation, user_3_id
    ):
        """Test that ValueError is raised when sender is not a participant."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Sender is not a participant"):
            await messaging_repository.create_message(
                conversation_id=uuid.UUID(sample_conversation.id),
                sender_id=user_3_id,
                content="Hello!",
            )

    async def test_create_message_truncates_long_preview(
        self, messaging_repository, mock_session, sample_conversation, user_1_id
    ):
        """Test that message preview is truncated to 255 chars."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        long_content = "A" * 300

        await messaging_repository.create_message(
            conversation_id=uuid.UUID(sample_conversation.id),
            sender_id=user_1_id,
            content=long_content,
        )

        assert len(sample_conversation.last_message_preview) == 255


class TestMarkAsRead:
    """Tests for MessagingRepository.mark_as_read() method."""

    async def test_mark_as_read_returns_count(
        self, messaging_repository, mock_session, sample_conversation, user_2_id
    ):
        """Test that mark_as_read returns number of messages marked."""
        # First execute for update, second for get_conversation_by_id
        mock_result_update = MagicMock()
        mock_result_update.rowcount = 3

        mock_result_conversation = MagicMock()
        mock_result_conversation.scalar_one_or_none.return_value = sample_conversation

        mock_session.execute.side_effect = [
            mock_result_update,
            mock_result_conversation,
        ]

        count = await messaging_repository.mark_as_read(
            conversation_id=uuid.UUID(sample_conversation.id),
            user_id=user_2_id,
        )

        assert count == 3

    async def test_mark_as_read_resets_unread_count(
        self, messaging_repository, mock_session, sample_conversation, user_2_id
    ):
        """Test that unread count is reset for the user."""
        sample_conversation.participant_2_unread_count = 5

        mock_result_update = MagicMock()
        mock_result_update.rowcount = 5

        mock_result_conversation = MagicMock()
        mock_result_conversation.scalar_one_or_none.return_value = sample_conversation

        mock_session.execute.side_effect = [
            mock_result_update,
            mock_result_conversation,
        ]

        await messaging_repository.mark_as_read(
            conversation_id=uuid.UUID(sample_conversation.id),
            user_id=user_2_id,
        )

        assert sample_conversation.participant_2_unread_count == 0


class TestGetUnreadCount:
    """Tests for MessagingRepository.get_unread_count() method."""

    async def test_get_unread_count_returns_total(
        self, messaging_repository, mock_session, user_1_id
    ):
        """Test that total unread count is returned."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        count = await messaging_repository.get_unread_count(user_1_id)

        assert count == 5

    async def test_get_unread_count_returns_zero_when_none(
        self, messaging_repository, mock_session, user_1_id
    ):
        """Test that zero is returned when no unread messages."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        count = await messaging_repository.get_unread_count(user_1_id)

        assert count == 0


class TestGetUnreadCountForConversation:
    """Tests for MessagingRepository.get_unread_count_for_conversation() method."""

    async def test_get_unread_count_for_participant_1(
        self, messaging_repository, mock_session, sample_conversation, user_1_id
    ):
        """Test getting unread count for participant 1."""
        sample_conversation.participant_1_unread_count = 3

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        count = await messaging_repository.get_unread_count_for_conversation(
            uuid.UUID(sample_conversation.id), user_1_id
        )

        assert count == 3

    async def test_get_unread_count_for_participant_2(
        self, messaging_repository, mock_session, sample_conversation, user_2_id
    ):
        """Test getting unread count for participant 2."""
        sample_conversation.participant_2_unread_count = 7

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        count = await messaging_repository.get_unread_count_for_conversation(
            uuid.UUID(sample_conversation.id), user_2_id
        )

        assert count == 7

    async def test_get_unread_count_returns_zero_for_non_participant(
        self, messaging_repository, mock_session, sample_conversation, user_3_id
    ):
        """Test that zero is returned for non-participant."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        count = await messaging_repository.get_unread_count_for_conversation(
            uuid.UUID(sample_conversation.id), user_3_id
        )

        assert count == 0

    async def test_get_unread_count_returns_zero_when_conversation_not_found(
        self, messaging_repository, mock_session, user_1_id
    ):
        """Test that zero is returned when conversation not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        count = await messaging_repository.get_unread_count_for_conversation(
            uuid.uuid4(), user_1_id
        )

        assert count == 0


class TestGetConversationBetweenUsers:
    """Tests for MessagingRepository.get_conversation_between_users() method."""

    async def test_get_conversation_between_users_found(
        self,
        messaging_repository,
        mock_session,
        sample_conversation,
        user_1_id,
        user_2_id,
    ):
        """Test finding conversation between two users."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.get_conversation_between_users(
            user_1_id, user_2_id
        )

        assert result == sample_conversation

    async def test_get_conversation_between_users_not_found(
        self, messaging_repository, mock_session, user_1_id, user_2_id
    ):
        """Test returning None when no conversation exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.get_conversation_between_users(
            user_1_id, user_2_id
        )

        assert result is None

    async def test_get_conversation_between_users_orders_participants(
        self,
        messaging_repository,
        mock_session,
        sample_conversation,
        user_1_id,
        user_2_id,
    ):
        """Test that participant order is consistent regardless of argument order."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        # Should find same conversation regardless of order
        result1 = await messaging_repository.get_conversation_between_users(
            user_1_id, user_2_id
        )
        result2 = await messaging_repository.get_conversation_between_users(
            user_2_id, user_1_id
        )

        assert result1 == result2


class TestDeleteMessage:
    """Tests for MessagingRepository.delete_message() method."""

    async def test_delete_message_success(
        self, messaging_repository, mock_session, sample_message, user_1_id
    ):
        """Test successful message deletion by sender."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_message
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.delete_message(
            uuid.UUID(sample_message.id), user_1_id
        )

        assert result is True
        mock_session.delete.assert_called_once_with(sample_message)
        mock_session.flush.assert_called_once()

    async def test_delete_message_not_found(
        self, messaging_repository, mock_session, user_1_id
    ):
        """Test deletion returns False when message not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.delete_message(uuid.uuid4(), user_1_id)

        assert result is False
        mock_session.delete.assert_not_called()

    async def test_delete_message_wrong_user(
        self, messaging_repository, mock_session, sample_message, user_2_id
    ):
        """Test deletion returns False when user is not sender."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_message
        mock_session.execute.return_value = mock_result

        result = await messaging_repository.delete_message(
            uuid.UUID(sample_message.id), user_2_id
        )

        assert result is False
        mock_session.delete.assert_not_called()


class TestAsyncPatterns:
    """Tests to verify all methods use async patterns."""

    def test_get_or_create_conversation_is_async(self, messaging_repository):
        """Verify get_or_create_conversation is async."""
        import inspect

        assert inspect.iscoroutinefunction(
            messaging_repository.get_or_create_conversation
        )

    def test_get_conversation_by_id_is_async(self, messaging_repository):
        """Verify get_conversation_by_id is async."""
        import inspect

        assert inspect.iscoroutinefunction(messaging_repository.get_conversation_by_id)

    def test_get_conversations_for_user_is_async(self, messaging_repository):
        """Verify get_conversations_for_user is async."""
        import inspect

        assert inspect.iscoroutinefunction(
            messaging_repository.get_conversations_for_user
        )

    def test_get_messages_is_async(self, messaging_repository):
        """Verify get_messages is async."""
        import inspect

        assert inspect.iscoroutinefunction(messaging_repository.get_messages)

    def test_create_message_is_async(self, messaging_repository):
        """Verify create_message is async."""
        import inspect

        assert inspect.iscoroutinefunction(messaging_repository.create_message)

    def test_mark_as_read_is_async(self, messaging_repository):
        """Verify mark_as_read is async."""
        import inspect

        assert inspect.iscoroutinefunction(messaging_repository.mark_as_read)

    def test_get_unread_count_is_async(self, messaging_repository):
        """Verify get_unread_count is async."""
        import inspect

        assert inspect.iscoroutinefunction(messaging_repository.get_unread_count)

    def test_get_unread_count_for_conversation_is_async(self, messaging_repository):
        """Verify get_unread_count_for_conversation is async."""
        import inspect

        assert inspect.iscoroutinefunction(
            messaging_repository.get_unread_count_for_conversation
        )

    def test_get_conversation_between_users_is_async(self, messaging_repository):
        """Verify get_conversation_between_users is async."""
        import inspect

        assert inspect.iscoroutinefunction(
            messaging_repository.get_conversation_between_users
        )

    def test_delete_message_is_async(self, messaging_repository):
        """Verify delete_message is async."""
        import inspect

        assert inspect.iscoroutinefunction(messaging_repository.delete_message)
