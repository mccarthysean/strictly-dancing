"""Add pg_trgm extension and GIN indexes for fuzzy search.

Revision ID: 000000000015
Revises: 000000000014
Create Date: 2026-01-29 14:00:00.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000015"
down_revision: str | None = "000000000014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable pg_trgm extension and create GIN indexes for fuzzy text search.

    The pg_trgm extension provides trigram-based similarity search which enables:
    - Fuzzy matching (typo tolerance)
    - Similarity scoring for result ranking
    - Efficient GIN-indexed pattern matching
    """
    # Enable pg_trgm extension for trigram-based text search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create GIN index on host_profiles for bio and headline search
    # gin_trgm_ops enables trigram-based similarity search
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_host_profiles_headline_trgm
        ON host_profiles USING gin (headline gin_trgm_ops)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_host_profiles_bio_trgm
        ON host_profiles USING gin (bio gin_trgm_ops)
    """)

    # Create GIN index on users table for name search
    # This allows fuzzy matching on host names
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_first_name_trgm
        ON users USING gin (first_name gin_trgm_ops)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_last_name_trgm
        ON users USING gin (last_name gin_trgm_ops)
    """)


def downgrade() -> None:
    """Remove GIN indexes and pg_trgm extension."""
    op.execute("DROP INDEX IF EXISTS ix_users_last_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_users_first_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_host_profiles_bio_trgm")
    op.execute("DROP INDEX IF EXISTS ix_host_profiles_headline_trgm")
    # Note: Not dropping pg_trgm extension as it may be used by other apps
