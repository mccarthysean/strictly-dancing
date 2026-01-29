"""Unit tests for the HostDanceStyle junction model."""

from app.models.host_dance_style import HostDanceStyle


class TestHostDanceStyleModel:
    """Tests for HostDanceStyle model definition."""

    def test_host_dance_style_model_instantiation(self) -> None:
        """Test that HostDanceStyle model can be instantiated with required fields."""
        host_dance_style = HostDanceStyle(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            dance_style_id="22222222-2222-2222-2222-222222222222",
            skill_level=4,
        )

        assert (
            host_dance_style.host_profile_id == "11111111-1111-1111-1111-111111111111"
        )
        assert host_dance_style.dance_style_id == "22222222-2222-2222-2222-222222222222"
        assert host_dance_style.skill_level == 4

    def test_host_dance_style_model_skill_level_has_default(self) -> None:
        """Test that skill_level column has a default value of 3 configured."""
        skill_level_column = HostDanceStyle.__table__.columns["skill_level"]
        assert skill_level_column.default is not None
        assert skill_level_column.default.arg == 3

    def test_host_dance_style_model_has_required_fields(self) -> None:
        """Test that HostDanceStyle model has all required fields."""
        columns = HostDanceStyle.__table__.columns.keys()

        required_fields = [
            "id",
            "host_profile_id",
            "dance_style_id",
            "skill_level",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"

    def test_host_dance_style_model_tablename(self) -> None:
        """Test that HostDanceStyle model has correct table name."""
        assert HostDanceStyle.__tablename__ == "host_dance_styles"


class TestHostDanceStyleModelConstraints:
    """Tests for HostDanceStyle model constraints."""

    def test_host_profile_id_column_is_not_nullable(self) -> None:
        """Test that host_profile_id column is not nullable."""
        host_profile_id_column = HostDanceStyle.__table__.columns["host_profile_id"]
        assert host_profile_id_column.nullable is False

    def test_dance_style_id_column_is_not_nullable(self) -> None:
        """Test that dance_style_id column is not nullable."""
        dance_style_id_column = HostDanceStyle.__table__.columns["dance_style_id"]
        assert dance_style_id_column.nullable is False

    def test_skill_level_column_is_not_nullable(self) -> None:
        """Test that skill_level column is not nullable."""
        skill_level_column = HostDanceStyle.__table__.columns["skill_level"]
        assert skill_level_column.nullable is False

    def test_host_profile_id_is_indexed(self) -> None:
        """Test that host_profile_id column is indexed."""
        host_profile_id_column = HostDanceStyle.__table__.columns["host_profile_id"]
        assert host_profile_id_column.index is True

    def test_dance_style_id_is_indexed(self) -> None:
        """Test that dance_style_id column is indexed."""
        dance_style_id_column = HostDanceStyle.__table__.columns["dance_style_id"]
        assert dance_style_id_column.index is True

    def test_id_is_primary_key(self) -> None:
        """Test that id column is primary key."""
        id_column = HostDanceStyle.__table__.columns["id"]
        assert id_column.primary_key is True

    def test_unique_constraint_on_host_profile_dance_style_pair(self) -> None:
        """Test that unique constraint exists on (host_profile_id, dance_style_id)."""
        constraints = HostDanceStyle.__table__.constraints
        unique_constraint_names = [
            c.name for c in constraints if c.name and "uq_" in c.name
        ]
        assert "uq_host_dance_style_host_profile_dance_style" in unique_constraint_names

    def test_check_constraint_on_skill_level_range(self) -> None:
        """Test that check constraint exists for skill_level range (1-5)."""
        constraints = HostDanceStyle.__table__.constraints
        check_constraint_names = [
            c.name for c in constraints if c.name and "ck_" in c.name
        ]
        assert "ck_host_dance_style_skill_level_range" in check_constraint_names


class TestHostDanceStyleForeignKeys:
    """Tests for HostDanceStyle foreign key relationships."""

    def test_host_profile_id_foreign_key(self) -> None:
        """Test that host_profile_id has correct foreign key."""
        host_profile_id_column = HostDanceStyle.__table__.columns["host_profile_id"]
        foreign_keys = list(host_profile_id_column.foreign_keys)

        assert len(foreign_keys) == 1
        fk = foreign_keys[0]
        assert fk.column.table.name == "host_profiles"
        assert fk.column.name == "id"

    def test_host_profile_id_foreign_key_cascade_delete(self) -> None:
        """Test that host_profile_id foreign key has CASCADE delete."""
        host_profile_id_column = HostDanceStyle.__table__.columns["host_profile_id"]
        foreign_keys = list(host_profile_id_column.foreign_keys)
        fk = foreign_keys[0]
        assert fk.ondelete == "CASCADE"

    def test_dance_style_id_foreign_key(self) -> None:
        """Test that dance_style_id has correct foreign key."""
        dance_style_id_column = HostDanceStyle.__table__.columns["dance_style_id"]
        foreign_keys = list(dance_style_id_column.foreign_keys)

        assert len(foreign_keys) == 1
        fk = foreign_keys[0]
        assert fk.column.table.name == "dance_styles"
        assert fk.column.name == "id"

    def test_dance_style_id_foreign_key_cascade_delete(self) -> None:
        """Test that dance_style_id foreign key has CASCADE delete."""
        dance_style_id_column = HostDanceStyle.__table__.columns["dance_style_id"]
        foreign_keys = list(dance_style_id_column.foreign_keys)
        fk = foreign_keys[0]
        assert fk.ondelete == "CASCADE"


class TestHostDanceStyleSkillLevel:
    """Tests for HostDanceStyle skill_level field."""

    def test_skill_level_minimum_valid(self) -> None:
        """Test that skill_level can be set to minimum valid value (1)."""
        host_dance_style = HostDanceStyle(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            dance_style_id="22222222-2222-2222-2222-222222222222",
            skill_level=1,
        )
        assert host_dance_style.skill_level == 1

    def test_skill_level_maximum_valid(self) -> None:
        """Test that skill_level can be set to maximum valid value (5)."""
        host_dance_style = HostDanceStyle(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            dance_style_id="22222222-2222-2222-2222-222222222222",
            skill_level=5,
        )
        assert host_dance_style.skill_level == 5

    def test_skill_level_middle_values(self) -> None:
        """Test that skill_level accepts middle range values (2, 3, 4)."""
        for skill in [2, 3, 4]:
            host_dance_style = HostDanceStyle(
                host_profile_id="11111111-1111-1111-1111-111111111111",
                dance_style_id="22222222-2222-2222-2222-222222222222",
                skill_level=skill,
            )
            assert host_dance_style.skill_level == skill


class TestHostDanceStyleRelationships:
    """Tests for HostDanceStyle relationship definitions."""

    def test_host_profile_relationship_exists(self) -> None:
        """Test that host_profile relationship is defined."""
        assert hasattr(HostDanceStyle, "host_profile")

    def test_dance_style_relationship_exists(self) -> None:
        """Test that dance_style relationship is defined."""
        assert hasattr(HostDanceStyle, "dance_style")


class TestHostDanceStyleModelRepr:
    """Tests for HostDanceStyle model representation."""

    def test_host_dance_style_repr(self) -> None:
        """Test that HostDanceStyle __repr__ returns expected format."""
        host_dance_style = HostDanceStyle(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            dance_style_id="22222222-2222-2222-2222-222222222222",
            skill_level=4,
        )

        repr_str = repr(host_dance_style)
        assert "11111111-1111-1111-1111-111111111111" in repr_str
        assert "22222222-2222-2222-2222-222222222222" in repr_str
        assert "4" in repr_str
