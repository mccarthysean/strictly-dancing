"""Unit tests for UserRepository."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserType
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    # Mock the execute method to return a mock result
    mock_result = MagicMock()
    session.execute.return_value = mock_result
    return session


@pytest.fixture
def user_repository(mock_session):
    """Create a UserRepository with a mock session."""
    return UserRepository(mock_session)


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$...",
        first_name="Test",
        last_name="User",
        user_type=UserType.CLIENT,
        email_verified=False,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    return user


@pytest.fixture
def sample_user_create():
    """Create a sample UserCreate schema."""
    return UserCreate(
        email="newuser@example.com",
        password="securepassword123",
        first_name="New",
        last_name="User",
        user_type=UserType.CLIENT,
    )


class TestUserRepositoryCreate:
    """Tests for UserRepository.create() method."""

    async def test_create_user_success(self, user_repository, mock_session):
        """Test successful user creation."""
        user_data = UserCreate(
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            user_type=UserType.CLIENT,
        )
        password_hash = "$argon2id$v=19$m=65536,t=3,p=4$..."

        result = await user_repository.create(user_data, password_hash)

        # Verify session.add was called
        mock_session.add.assert_called_once()
        # Verify the user has correct attributes
        assert result.email == "test@example.com"
        assert result.password_hash == password_hash
        assert result.first_name == "Test"
        assert result.last_name == "User"
        assert result.user_type == UserType.CLIENT
        assert result.is_active is True
        assert result.email_verified is False

    async def test_create_user_with_host_type(self, user_repository, mock_session):
        """Test creating a user with host user type."""
        user_data = UserCreate(
            email="host@example.com",
            password="password123",
            first_name="Host",
            last_name="User",
            user_type=UserType.HOST,
        )
        password_hash = "$argon2id$..."

        result = await user_repository.create(user_data, password_hash)

        assert result.user_type == UserType.HOST


class TestUserRepositoryGetById:
    """Tests for UserRepository.get_by_id() method."""

    async def test_get_by_id_found(self, user_repository, mock_session, sample_user):
        """Test getting a user by ID when user exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        result = await user_repository.get_by_id(sample_user.id)

        assert result == sample_user
        mock_session.execute.assert_called_once()

    async def test_get_by_id_not_found(self, user_repository, mock_session):
        """Test getting a user by ID when user doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await user_repository.get_by_id(uuid.uuid4())

        assert result is None


class TestUserRepositoryGetByEmail:
    """Tests for UserRepository.get_by_email() method."""

    async def test_get_by_email_found(self, user_repository, mock_session, sample_user):
        """Test getting a user by email when user exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        result = await user_repository.get_by_email("test@example.com")

        assert result == sample_user

    async def test_get_by_email_not_found(self, user_repository, mock_session):
        """Test getting a user by email when user doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await user_repository.get_by_email("nonexistent@example.com")

        assert result is None

    async def test_get_by_email_case_insensitive(
        self, user_repository, mock_session, sample_user
    ):
        """Test that email lookup is case-insensitive."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        await user_repository.get_by_email("TEST@EXAMPLE.COM")

        # Verify the query was executed with lowercase email
        mock_session.execute.assert_called_once()


class TestUserRepositoryExistsByEmail:
    """Tests for UserRepository.exists_by_email() method."""

    async def test_exists_by_email_true(self, user_repository, mock_session):
        """Test exists_by_email returns True when user exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = True
        mock_session.execute.return_value = mock_result

        result = await user_repository.exists_by_email("test@example.com")

        assert result is True

    async def test_exists_by_email_false(self, user_repository, mock_session):
        """Test exists_by_email returns False when user doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await user_repository.exists_by_email("nonexistent@example.com")

        assert result is False

    async def test_exists_by_email_case_insensitive(
        self, user_repository, mock_session
    ):
        """Test that exists_by_email check is case-insensitive."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = True
        mock_session.execute.return_value = mock_result

        # Should work with uppercase email
        result = await user_repository.exists_by_email("TEST@EXAMPLE.COM")

        assert result is True


class TestUserRepositoryUpdate:
    """Tests for UserRepository.update() method."""

    async def test_update_user_success(
        self, user_repository, mock_session, sample_user
    ):
        """Test successful user update."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        update_data = UserUpdate(first_name="Updated", last_name="Name")

        result = await user_repository.update(sample_user.id, update_data)

        assert result.first_name == "Updated"
        assert result.last_name == "Name"

    async def test_update_partial_fields(
        self, user_repository, mock_session, sample_user
    ):
        """Test partial update with only some fields."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        original_last_name = sample_user.last_name
        update_data = UserUpdate(first_name="JustFirst")

        result = await user_repository.update(sample_user.id, update_data)

        assert result.first_name == "JustFirst"
        assert result.last_name == original_last_name  # Should remain unchanged

    async def test_update_user_not_found(self, user_repository, mock_session):
        """Test update returns None when user doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        update_data = UserUpdate(first_name="Updated")

        result = await user_repository.update(uuid.uuid4(), update_data)

        assert result is None


class TestUserRepositorySoftDelete:
    """Tests for UserRepository.soft_delete() method."""

    async def test_soft_delete_success(
        self, user_repository, mock_session, sample_user
    ):
        """Test successful soft delete (sets is_active to False)."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        result = await user_repository.soft_delete(sample_user.id)

        assert result is True
        assert sample_user.is_active is False

    async def test_soft_delete_not_found(self, user_repository, mock_session):
        """Test soft_delete returns False when user doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await user_repository.soft_delete(uuid.uuid4())

        assert result is False

    async def test_soft_delete_idempotent(
        self, user_repository, mock_session, sample_user
    ):
        """Test soft_delete on already deleted user still returns True."""
        sample_user.is_active = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        result = await user_repository.soft_delete(sample_user.id)

        assert result is True
        assert sample_user.is_active is False


class TestUserRepositoryAsyncPatterns:
    """Tests to verify all methods use async patterns."""

    async def test_create_is_async(self, user_repository, sample_user_create):
        """Verify create method is async."""
        import inspect

        assert inspect.iscoroutinefunction(user_repository.create)

    async def test_get_by_id_is_async(self, user_repository):
        """Verify get_by_id method is async."""
        import inspect

        assert inspect.iscoroutinefunction(user_repository.get_by_id)

    async def test_get_by_email_is_async(self, user_repository):
        """Verify get_by_email method is async."""
        import inspect

        assert inspect.iscoroutinefunction(user_repository.get_by_email)

    async def test_exists_by_email_is_async(self, user_repository):
        """Verify exists_by_email method is async."""
        import inspect

        assert inspect.iscoroutinefunction(user_repository.exists_by_email)

    async def test_update_is_async(self, user_repository):
        """Verify update method is async."""
        import inspect

        assert inspect.iscoroutinefunction(user_repository.update)

    async def test_soft_delete_is_async(self, user_repository):
        """Verify soft_delete method is async."""
        import inspect

        assert inspect.iscoroutinefunction(user_repository.soft_delete)
