"""Initial migration: Enable uuid-ossp and postgis extensions.

Revision ID: 000000000001
Revises:
Create Date: 2026-01-29 00:00:00.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable PostgreSQL extensions for UUID and PostGIS support."""
    # Enable uuid-ossp extension for UUID generation functions
    # This provides uuid_generate_v4() for generating UUIDs
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Enable PostGIS extension for geospatial data types and functions
    # This provides GEOGRAPHY type and spatial functions like ST_DWithin
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    """Remove PostgreSQL extensions.

    Note: Dropping extensions may fail if there are dependent objects.
    In production, carefully consider the implications before downgrading.
    """
    op.execute("DROP EXTENSION IF EXISTS postgis CASCADE")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp" CASCADE')
