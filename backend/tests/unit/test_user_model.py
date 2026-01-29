"""Unit tests for the User database model."""

from app.models.user import User, UserType


class TestUserModel:
    """Tests for User model definition."""

    def test_user_model_instantiation(self) -> None:
        """Test that User model can be instantiated with required fields."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe",
        )

        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.first_name == "John"
        assert user.last_name == "Doe"

    def test_user_model_has_required_fields(self) -> None:
        """Test that User model has all required fields."""
        # Check that all required columns exist
        columns = User.__table__.columns.keys()

        required_fields = [
            "id",
            "email",
            "password_hash",
            "first_name",
            "last_name",
            "user_type",
            "email_verified",
            "is_active",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"

    def test_user_model_default_values_defined(self) -> None:
        """Test that User model has default values defined on columns."""
        # SQLAlchemy defaults are applied during insert, not instantiation
        # So we check that the defaults are defined on the columns
        user_type_col = User.__table__.columns["user_type"]
        email_verified_col = User.__table__.columns["email_verified"]
        is_active_col = User.__table__.columns["is_active"]

        # Defaults are defined on the column
        assert user_type_col.default is not None
        assert email_verified_col.default is not None
        assert is_active_col.default is not None

        # Check the actual default values
        assert user_type_col.default.arg == UserType.CLIENT
        assert email_verified_col.default.arg is False
        assert is_active_col.default.arg is True

    def test_user_model_tablename(self) -> None:
        """Test that User model has correct table name."""
        assert User.__tablename__ == "users"


class TestUserType:
    """Tests for UserType enumeration."""

    def test_user_type_enum_values(self) -> None:
        """Test that UserType enum has all required values."""
        assert UserType.CLIENT.value == "client"
        assert UserType.HOST.value == "host"
        assert UserType.BOTH.value == "both"

    def test_user_type_enum_is_string_enum(self) -> None:
        """Test that UserType is a string enum."""
        assert isinstance(UserType.CLIENT, str)
        assert UserType.CLIENT == "client"

    def test_user_type_enum_count(self) -> None:
        """Test that UserType has exactly 3 values."""
        assert len(UserType) == 3


class TestUserModelConstraints:
    """Tests for User model constraints."""

    def test_email_column_is_unique(self) -> None:
        """Test that email column has unique constraint."""
        email_column = User.__table__.columns["email"]
        assert email_column.unique is True

    def test_email_column_is_indexed(self) -> None:
        """Test that email column is indexed."""
        email_column = User.__table__.columns["email"]
        assert email_column.index is True

    def test_email_column_is_not_nullable(self) -> None:
        """Test that email column is not nullable."""
        email_column = User.__table__.columns["email"]
        assert email_column.nullable is False

    def test_password_hash_column_is_nullable(self) -> None:
        """Test that password_hash column is nullable (passwordless auth)."""
        password_hash_column = User.__table__.columns["password_hash"]
        # Password hash is nullable for passwordless authentication
        assert password_hash_column.nullable is True

    def test_id_is_primary_key(self) -> None:
        """Test that id column is primary key."""
        id_column = User.__table__.columns["id"]
        assert id_column.primary_key is True


class TestUserModelRepr:
    """Tests for User model representation."""

    def test_user_repr(self) -> None:
        """Test that User __repr__ returns expected format."""
        user = User(
            id="12345678-1234-1234-1234-123456789012",
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe",
            user_type=UserType.HOST,
        )

        repr_str = repr(user)
        assert "12345678-1234-1234-1234-123456789012" in repr_str
        assert "test@example.com" in repr_str
        # The enum is shown as UserType.HOST in the repr
        assert "HOST" in repr_str
