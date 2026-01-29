"""Create verification_documents table.

Revision ID: 20260129_110000
Revises: 20260129_100000
Create Date: 2026-01-29 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260129_110000"
down_revision: str | None = "20260129_100000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create document_type enum
    document_type_enum = postgresql.ENUM(
        "government_id",
        "passport",
        "drivers_license",
        "other",
        name="document_type_enum",
        create_type=True,
    )
    document_type_enum.create(op.get_bind(), checkfirst=True)

    # Create verification_documents table
    op.create_table(
        "verification_documents",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("host_profile_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "document_type",
            document_type_enum,
            nullable=False,
        ),
        sa.Column("document_url", sa.String(length=1024), nullable=True),
        sa.Column("document_number", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.String(), nullable=True),
        sa.Column("reviewed_by", sa.UUID(as_uuid=False), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["host_profile_id"],
            ["host_profiles.id"],
            name="fk_verification_documents_host_profile",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        "ix_verification_documents_host_profile_id",
        "verification_documents",
        ["host_profile_id"],
        unique=False,
    )
    op.create_index(
        "ix_verification_documents_created_at",
        "verification_documents",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        "ix_verification_documents_created_at",
        table_name="verification_documents",
    )
    op.drop_index(
        "ix_verification_documents_host_profile_id",
        table_name="verification_documents",
    )

    # Drop table
    op.drop_table("verification_documents")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS document_type_enum")
