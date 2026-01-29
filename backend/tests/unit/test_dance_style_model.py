"""Unit tests for the DanceStyle database model."""

from app.models.dance_style import DanceStyle, DanceStyleCategory


class TestDanceStyleModel:
    """Tests for DanceStyle model definition."""

    def test_dance_style_model_instantiation(self) -> None:
        """Test that DanceStyle model can be instantiated with required fields."""
        dance_style = DanceStyle(
            name="Salsa",
            slug="salsa",
            category=DanceStyleCategory.LATIN,
            description="A sensual, energetic partner dance.",
        )

        assert dance_style.name == "Salsa"
        assert dance_style.slug == "salsa"
        assert dance_style.category == DanceStyleCategory.LATIN
        assert dance_style.description == "A sensual, energetic partner dance."

    def test_dance_style_model_instantiation_without_description(self) -> None:
        """Test that DanceStyle can be created without description."""
        dance_style = DanceStyle(
            name="Waltz",
            slug="waltz",
            category=DanceStyleCategory.BALLROOM,
        )

        assert dance_style.name == "Waltz"
        assert dance_style.slug == "waltz"
        assert dance_style.category == DanceStyleCategory.BALLROOM
        assert dance_style.description is None

    def test_dance_style_model_has_required_fields(self) -> None:
        """Test that DanceStyle model has all required fields."""
        columns = DanceStyle.__table__.columns.keys()

        required_fields = [
            "id",
            "name",
            "slug",
            "category",
            "description",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"

    def test_dance_style_model_tablename(self) -> None:
        """Test that DanceStyle model has correct table name."""
        assert DanceStyle.__tablename__ == "dance_styles"


class TestDanceStyleCategory:
    """Tests for DanceStyleCategory enumeration."""

    def test_dance_style_category_latin(self) -> None:
        """Test that LATIN category value is correct."""
        assert DanceStyleCategory.LATIN.value == "latin"

    def test_dance_style_category_ballroom(self) -> None:
        """Test that BALLROOM category value is correct."""
        assert DanceStyleCategory.BALLROOM.value == "ballroom"

    def test_dance_style_category_swing(self) -> None:
        """Test that SWING category value is correct."""
        assert DanceStyleCategory.SWING.value == "swing"

    def test_dance_style_category_social(self) -> None:
        """Test that SOCIAL category value is correct."""
        assert DanceStyleCategory.SOCIAL.value == "social"

    def test_dance_style_category_other(self) -> None:
        """Test that OTHER category value is correct."""
        assert DanceStyleCategory.OTHER.value == "other"

    def test_dance_style_category_is_string_enum(self) -> None:
        """Test that DanceStyleCategory is a string enum."""
        assert isinstance(DanceStyleCategory.LATIN, str)
        assert DanceStyleCategory.LATIN == "latin"

    def test_dance_style_category_count(self) -> None:
        """Test that DanceStyleCategory has exactly 5 values."""
        assert len(DanceStyleCategory) == 5

    def test_dance_style_category_all_values(self) -> None:
        """Test that all expected categories exist."""
        expected_categories = {"latin", "ballroom", "swing", "social", "other"}
        actual_categories = {cat.value for cat in DanceStyleCategory}
        assert actual_categories == expected_categories


class TestDanceStyleModelConstraints:
    """Tests for DanceStyle model constraints."""

    def test_name_column_is_unique(self) -> None:
        """Test that name column has unique constraint."""
        name_column = DanceStyle.__table__.columns["name"]
        assert name_column.unique is True

    def test_slug_column_is_unique(self) -> None:
        """Test that slug column has unique constraint."""
        slug_column = DanceStyle.__table__.columns["slug"]
        assert slug_column.unique is True

    def test_slug_column_is_indexed(self) -> None:
        """Test that slug column is indexed."""
        slug_column = DanceStyle.__table__.columns["slug"]
        assert slug_column.index is True

    def test_name_column_is_not_nullable(self) -> None:
        """Test that name column is not nullable."""
        name_column = DanceStyle.__table__.columns["name"]
        assert name_column.nullable is False

    def test_slug_column_is_not_nullable(self) -> None:
        """Test that slug column is not nullable."""
        slug_column = DanceStyle.__table__.columns["slug"]
        assert slug_column.nullable is False

    def test_category_column_is_not_nullable(self) -> None:
        """Test that category column is not nullable."""
        category_column = DanceStyle.__table__.columns["category"]
        assert category_column.nullable is False

    def test_description_column_is_nullable(self) -> None:
        """Test that description column is nullable."""
        description_column = DanceStyle.__table__.columns["description"]
        assert description_column.nullable is True

    def test_id_is_primary_key(self) -> None:
        """Test that id column is primary key."""
        id_column = DanceStyle.__table__.columns["id"]
        assert id_column.primary_key is True


class TestDanceStyleModelRepr:
    """Tests for DanceStyle model representation."""

    def test_dance_style_repr(self) -> None:
        """Test that DanceStyle __repr__ returns expected format."""
        dance_style = DanceStyle(
            id="12345678-1234-1234-1234-123456789012",
            name="Salsa",
            slug="salsa",
            category=DanceStyleCategory.LATIN,
        )

        repr_str = repr(dance_style)
        assert "12345678-1234-1234-1234-123456789012" in repr_str
        assert "Salsa" in repr_str
        assert "LATIN" in repr_str
