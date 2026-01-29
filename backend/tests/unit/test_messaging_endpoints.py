"""Unit tests for messaging router endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.conversation import MessageType
from app.models.user import User, UserType


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "user@test.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.user_type = UserType.CLIENT
    user.is_active = True
    user.email_verified = True
    return user


@pytest.fixture
def sample_other_user():
    """Create another sample user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "other@test.com"
    user.first_name = "Other"
    user.last_name = "Person"
    user.user_type = UserType.HOST
    user.is_active = True
    user.email_verified = True
    return user


def _create_mock_conversation(
    participant_1_id: str,
    participant_2_id: str,
    last_message_at: datetime | None = None,
    last_message_preview: str | None = None,
    p1_unread: int = 0,
    p2_unread: int = 0,
):
    """Create a mock conversation object."""
    conv = MagicMock()
    conv.id = str(uuid4())
    conv.participant_1_id = participant_1_id
    conv.participant_2_id = participant_2_id
    conv.last_message_at = last_message_at
    conv.last_message_preview = last_message_preview
    conv.participant_1_unread_count = p1_unread
    conv.participant_2_unread_count = p2_unread
    conv.created_at = datetime.now(UTC)
    conv.updated_at = datetime.now(UTC)

    def is_participant(user_id):
        return user_id in (participant_1_id, participant_2_id)

    def get_other_participant_id(user_id):
        if user_id == participant_1_id:
            return participant_2_id
        elif user_id == participant_2_id:
            return participant_1_id
        return None

    conv.is_participant = is_participant
    conv.get_other_participant_id = get_other_participant_id
    return conv


def _create_mock_message(
    conversation_id: str,
    sender_id: str,
    content: str = "Hello!",
    message_type: MessageType = MessageType.TEXT,
    sender=None,
):
    """Create a mock message object."""
    msg = MagicMock()
    msg.id = str(uuid4())
    msg.conversation_id = conversation_id
    msg.sender_id = sender_id
    msg.content = content
    msg.message_type = message_type
    msg.read_at = None
    msg.created_at = datetime.now(UTC)
    msg.updated_at = datetime.now(UTC)
    msg.sender = sender
    return msg


def get_auth_header(user_id: UUID):
    """Generate a mock authentication header."""
    return {"Authorization": f"Bearer test_token_{user_id}"}


class TestListConversationsEndpoint:
    """Tests for GET /api/v1/conversations endpoint."""

    @pytest.mark.asyncio
    async def test_list_conversations_endpoint_exists(self, mock_db, sample_user):
        """Test that the list conversations endpoint exists."""
        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
            patch("app.routers.messaging.UserRepository"),
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversations_for_user.return_value = []
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/conversations",
                    headers=get_auth_header(sample_user.id),
                )

        # Should not be 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_list_conversations_requires_auth(self, mock_db):
        """Test that list conversations requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/conversations")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_list_conversations_returns_empty_list(self, mock_db, sample_user):
        """Test that list conversations returns empty list when no conversations."""
        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
            patch("app.routers.messaging.UserRepository"),
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversations_for_user.return_value = []
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/conversations",
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_list_conversations_returns_conversations(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that list conversations returns user's conversations."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
            last_message_at=datetime.now(UTC),
            last_message_preview="Hello!",
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
            patch("app.routers.messaging.UserRepository") as mock_router_user_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_router_user_repo = AsyncMock()
            mock_router_user_repo.get_by_id.return_value = sample_other_user
            mock_router_user_repo_cls.return_value = mock_router_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversations_for_user.return_value = [conv]
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/conversations",
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["last_message_preview"] == "Hello!"


class TestStartConversationEndpoint:
    """Tests for POST /api/v1/conversations endpoint."""

    @pytest.mark.asyncio
    async def test_start_conversation_endpoint_exists(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that the start conversation endpoint exists."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
            patch("app.routers.messaging.UserRepository") as mock_router_user_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_router_user_repo = AsyncMock()
            mock_router_user_repo.get_by_id.side_effect = [
                sample_other_user,
                sample_user,
                sample_other_user,
            ]
            mock_router_user_repo_cls.return_value = mock_router_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_or_create_conversation.return_value = (conv, True)
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/conversations",
                    json={"participant_id": str(sample_other_user.id)},
                    headers=get_auth_header(sample_user.id),
                )

        # Should not be 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_start_conversation_requires_auth(self, mock_db):
        """Test that start conversation requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/conversations",
                json={"participant_id": str(uuid4())},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_start_conversation_creates_new_conversation(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that start conversation creates a new conversation."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
            patch("app.routers.messaging.UserRepository") as mock_router_user_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_router_user_repo = AsyncMock()
            mock_router_user_repo.get_by_id.side_effect = [
                sample_other_user,
                sample_user,
                sample_other_user,
            ]
            mock_router_user_repo_cls.return_value = mock_router_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_or_create_conversation.return_value = (conv, True)
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/conversations",
                    json={"participant_id": str(sample_other_user.id)},
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_start_conversation_with_self_returns_400(self, mock_db, sample_user):
        """Test that starting conversation with self returns 400."""
        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/conversations",
                    json={"participant_id": str(sample_user.id)},
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "yourself" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_start_conversation_user_not_found_returns_404(
        self, mock_db, sample_user
    ):
        """Test that starting conversation with nonexistent user returns 404."""
        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.UserRepository") as mock_router_user_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_router_user_repo = AsyncMock()
            mock_router_user_repo.get_by_id.return_value = None
            mock_router_user_repo_cls.return_value = mock_router_user_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/conversations",
                    json={"participant_id": str(uuid4())},
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetConversationEndpoint:
    """Tests for GET /api/v1/conversations/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_conversation_endpoint_exists(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that the get conversation endpoint exists."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
            patch("app.routers.messaging.UserRepository") as mock_router_user_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_router_user_repo = AsyncMock()
            mock_router_user_repo.get_by_id.side_effect = [
                sample_user,
                sample_other_user,
            ]
            mock_router_user_repo_cls.return_value = mock_router_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = conv
            mock_msg_repo.get_messages.return_value = []
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/conversations/{conv.id}",
                    headers=get_auth_header(sample_user.id),
                )

        # Should not be 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_conversation_requires_auth(self, mock_db):
        """Test that get conversation requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/conversations/{uuid4()}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_conversation_returns_conversation_with_messages(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that get conversation returns conversation with messages."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
        )

        message = _create_mock_message(
            conversation_id=conv.id,
            sender_id=str(sample_user.id),
            content="Hello!",
            sender=sample_user,
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
            patch("app.routers.messaging.UserRepository") as mock_router_user_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_router_user_repo = AsyncMock()
            mock_router_user_repo.get_by_id.side_effect = [
                sample_user,
                sample_other_user,
            ]
            mock_router_user_repo_cls.return_value = mock_router_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = conv
            mock_msg_repo.get_messages.return_value = [message]
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/conversations/{conv.id}",
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == conv.id
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Hello!"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found_returns_404(self, mock_db, sample_user):
        """Test that get conversation returns 404 when not found."""
        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = None
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/conversations/{uuid4()}",
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_conversation_not_participant_returns_403(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that get conversation returns 403 when user is not participant."""
        third_user = MagicMock(spec=User)
        third_user.id = uuid4()

        # Conversation between other two users
        conv = _create_mock_conversation(
            participant_1_id=str(sample_other_user.id),
            participant_2_id=str(third_user.id),
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = conv
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/conversations/{conv.id}",
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSendMessageEndpoint:
    """Tests for POST /api/v1/conversations/{id}/messages endpoint."""

    @pytest.mark.asyncio
    async def test_send_message_endpoint_exists(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that the send message endpoint exists."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = conv
            mock_msg_repo.create_message.return_value = _create_mock_message(
                conversation_id=conv.id,
                sender_id=str(sample_user.id),
            )
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/conversations/{conv.id}/messages",
                    json={"content": "Hello!"},
                    headers=get_auth_header(sample_user.id),
                )

        # Should not be 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_send_message_requires_auth(self, mock_db):
        """Test that send message requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/conversations/{uuid4()}/messages",
                json={"content": "Hello!"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_send_message_creates_message(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that send message creates a new message."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
        )

        created_message = _create_mock_message(
            conversation_id=conv.id,
            sender_id=str(sample_user.id),
            content="Hello there!",
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = conv
            mock_msg_repo.create_message.return_value = created_message
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/conversations/{conv.id}/messages",
                    json={"content": "Hello there!"},
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == "Hello there!"

    @pytest.mark.asyncio
    async def test_send_message_conversation_not_found_returns_404(
        self, mock_db, sample_user
    ):
        """Test that send message returns 404 when conversation not found."""
        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = None
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/conversations/{uuid4()}/messages",
                    json={"content": "Hello!"},
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_send_message_not_participant_returns_403(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that send message returns 403 when user is not participant."""
        third_user = MagicMock(spec=User)
        third_user.id = uuid4()

        # Conversation between other two users
        conv = _create_mock_conversation(
            participant_1_id=str(sample_other_user.id),
            participant_2_id=str(third_user.id),
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = conv
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/conversations/{conv.id}/messages",
                    json={"content": "Hello!"},
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMarkConversationReadEndpoint:
    """Tests for POST /api/v1/conversations/{id}/read endpoint."""

    @pytest.mark.asyncio
    async def test_mark_read_endpoint_exists(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that the mark read endpoint exists."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = conv
            mock_msg_repo.mark_as_read.return_value = 5
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/conversations/{conv.id}/read",
                    headers=get_auth_header(sample_user.id),
                )

        # Should not be 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_mark_read_requires_auth(self, mock_db):
        """Test that mark read requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(f"/api/v1/conversations/{uuid4()}/read")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_mark_read_returns_204(self, mock_db, sample_user, sample_other_user):
        """Test that mark read returns 204 No Content."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
            p1_unread=5,
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = conv
            mock_msg_repo.mark_as_read.return_value = 5
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/conversations/{conv.id}/read",
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_mark_read_conversation_not_found_returns_404(
        self, mock_db, sample_user
    ):
        """Test that mark read returns 404 when conversation not found."""
        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = None
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/conversations/{uuid4()}/read",
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetMessagesEndpoint:
    """Tests for GET /api/v1/conversations/{id}/messages endpoint."""

    @pytest.mark.asyncio
    async def test_get_messages_endpoint_exists(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that the get messages endpoint exists."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
        )

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = conv
            mock_msg_repo.get_messages.return_value = []
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/conversations/{conv.id}/messages",
                    headers=get_auth_header(sample_user.id),
                )

        # Should not be 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_messages_requires_auth(self, mock_db):
        """Test that get messages requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/conversations/{uuid4()}/messages")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_messages_returns_messages(
        self, mock_db, sample_user, sample_other_user
    ):
        """Test that get messages returns conversation messages."""
        conv = _create_mock_conversation(
            participant_1_id=str(sample_user.id),
            participant_2_id=str(sample_other_user.id),
        )

        messages = [
            _create_mock_message(
                conversation_id=conv.id,
                sender_id=str(sample_user.id),
                content="Message 1",
                sender=sample_user,
            ),
            _create_mock_message(
                conversation_id=conv.id,
                sender_id=str(sample_other_user.id),
                content="Message 2",
                sender=sample_other_user,
            ),
        ]

        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = conv
            mock_msg_repo.get_messages.return_value = messages
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/conversations/{conv.id}/messages",
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_messages_conversation_not_found_returns_404(
        self, mock_db, sample_user
    ):
        """Test that get messages returns 404 when conversation not found."""
        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_conversation_by_id.return_value = None
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/conversations/{uuid4()}/messages",
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetUnreadCountEndpoint:
    """Tests for GET /api/v1/conversations/unread endpoint."""

    @pytest.mark.asyncio
    async def test_get_unread_count_endpoint_exists(self, mock_db, sample_user):
        """Test that the unread count endpoint exists."""
        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_unread_count.return_value = 0
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/conversations/unread",
                    headers=get_auth_header(sample_user.id),
                )

        # Should not be 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_unread_count_requires_auth(self, mock_db):
        """Test that unread count requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/conversations/unread")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_unread_count_returns_count(self, mock_db, sample_user):
        """Test that unread count returns the total unread count."""
        with (
            patch("app.routers.messaging.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_cls,
            patch("app.routers.messaging.MessagingRepository") as mock_msg_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = sample_user
            mock_user_repo_cls.return_value = mock_user_repo

            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_unread_count.return_value = 15
            mock_msg_repo_cls.return_value = mock_msg_repo

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/conversations/unread",
                    headers=get_auth_header(sample_user.id),
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_unread"] == 15
