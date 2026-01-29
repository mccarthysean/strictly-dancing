"""Create dance_styles table with seed data.

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2026-01-29 02:00:00.000000+00:00

"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000003"
down_revision: str | None = "000000000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Seed data for dance styles (20+ styles across 5 categories)
DANCE_STYLES = [
    # Latin
    (
        "Salsa",
        "salsa",
        "latin",
        "A sensual, energetic partner dance originating from Cuba.",
    ),
    (
        "Bachata",
        "bachata",
        "latin",
        "A romantic Dominican dance characterized by hip movements.",
    ),
    (
        "Merengue",
        "merengue",
        "latin",
        "A lively Dominican dance with simple side-to-side steps.",
    ),
    (
        "Cha-Cha",
        "cha-cha",
        "latin",
        "A rhythmic Cuban dance with a distinctive triple step.",
    ),
    ("Rumba", "rumba", "latin", "A slow, sensual Cuban dance emphasizing hip motion."),
    (
        "Samba",
        "samba",
        "latin",
        "An energetic Brazilian dance with bouncing movements.",
    ),
    (
        "Mambo",
        "mambo",
        "latin",
        "A Cuban dance featuring quick footwork and hip movements.",
    ),
    # Ballroom
    ("Waltz", "waltz", "ballroom", "An elegant, flowing dance in 3/4 time."),
    (
        "Foxtrot",
        "foxtrot",
        "ballroom",
        "A smooth, progressive dance with long, flowing movements.",
    ),
    (
        "Tango",
        "tango",
        "ballroom",
        "A dramatic Argentine dance with sharp, staccato movements.",
    ),
    (
        "Viennese Waltz",
        "viennese-waltz",
        "ballroom",
        "A fast, rotating waltz with elegant spins.",
    ),
    (
        "Quickstep",
        "quickstep",
        "ballroom",
        "A fast-paced, lively ballroom dance with hops and runs.",
    ),
    # Swing
    (
        "East Coast Swing",
        "east-coast-swing",
        "swing",
        "An American swing dance with a bouncy, circular motion.",
    ),
    (
        "West Coast Swing",
        "west-coast-swing",
        "swing",
        "A smooth, slotted swing dance from California.",
    ),
    (
        "Lindy Hop",
        "lindy-hop",
        "swing",
        "The original swing dance from Harlem with aerial moves.",
    ),
    ("Jive", "jive", "swing", "A fast, energetic swing dance with kicks and flicks."),
    (
        "Boogie Woogie",
        "boogie-woogie",
        "swing",
        "A high-energy swing dance to boogie woogie music.",
    ),
    # Social
    (
        "Two-Step",
        "two-step",
        "social",
        "A simple country dance with quick-quick-slow steps.",
    ),
    (
        "Hustle",
        "hustle",
        "social",
        "A disco-era partner dance with spins and turns.",
    ),
    (
        "Night Club Two-Step",
        "night-club-two-step",
        "social",
        "A romantic, slow dance for contemporary music.",
    ),
    (
        "Cumbia",
        "cumbia",
        "social",
        "A Colombian dance with circular footwork patterns.",
    ),
    ("Zouk", "zouk", "social", "A Brazilian dance with flowing head movements."),
    (
        "Kizomba",
        "kizomba",
        "social",
        "A sensual Angolan dance with close embrace.",
    ),
    # Other
    (
        "Argentine Tango",
        "argentine-tango",
        "other",
        "The original improvisational tango from Buenos Aires.",
    ),
    (
        "Bolero",
        "bolero",
        "other",
        "A slow, romantic dance with dramatic arm movements.",
    ),
    (
        "Paso Doble",
        "paso-doble",
        "other",
        "A dramatic Spanish dance portraying a bullfight.",
    ),
]


def upgrade() -> None:
    """Create dance_styles table and seed data."""
    # Create dance_style_category enum
    category_enum = sa.Enum(
        "latin",
        "ballroom",
        "swing",
        "social",
        "other",
        name="dance_style_category_enum",
    )
    category_enum.create(op.get_bind(), checkfirst=True)

    # Create dance_styles table
    op.create_table(
        "dance_styles",
        sa.Column(
            "id",
            UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("category", category_enum, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create indexes
    op.create_index("ix_dance_styles_name", "dance_styles", ["name"], unique=True)
    op.create_index("ix_dance_styles_slug", "dance_styles", ["slug"], unique=True)
    op.create_index("ix_dance_styles_category", "dance_styles", ["category"])

    # Seed dance styles data
    dance_styles_table = sa.table(
        "dance_styles",
        sa.column("id", UUID(as_uuid=False)),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("category", sa.String),
        sa.column("description", sa.Text),
    )

    op.bulk_insert(
        dance_styles_table,
        [
            {
                "id": str(uuid4()),
                "name": name,
                "slug": slug,
                "category": category,
                "description": description,
            }
            for name, slug, category, description in DANCE_STYLES
        ],
    )


def downgrade() -> None:
    """Drop dance_styles table and enum."""
    op.drop_index("ix_dance_styles_category", table_name="dance_styles")
    op.drop_index("ix_dance_styles_slug", table_name="dance_styles")
    op.drop_index("ix_dance_styles_name", table_name="dance_styles")
    op.drop_table("dance_styles")

    # Drop enum type
    sa.Enum(name="dance_style_category_enum").drop(op.get_bind(), checkfirst=True)
