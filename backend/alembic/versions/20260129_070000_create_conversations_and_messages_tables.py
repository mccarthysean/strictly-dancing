"""Create conversations and messages tables.

Revision ID: 000000000008
Revises: 000000000007
Create Date: 2026-01-29 07:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000008"
down_revision: str | None = "000000000007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create conversations and messages tables."""
    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "participant_1_id",
            UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_2_id",
            UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "last_message_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_message_preview",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "participant_1_unread_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "participant_2_unread_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        # Timestamps
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
        # Constraints
        sa.UniqueConstraint(
            "participant_1_id",
            "participant_2_id",
            name="uq_conversations_participants",
        ),
        sa.CheckConstraint(
            "participant_1_id < participant_2_id",
            name="ck_conversations_participant_order",
        ),
    )

    # Create indexes for conversations
    op.create_index(
        "ix_conversations_participant_1",
        "conversations",
        ["participant_1_id"],
    )
    op.create_index(
        "ix_conversations_participant_2",
        "conversations",
        ["participant_2_id"],
    )
    op.create_index(
        "ix_conversations_last_message_at",
        "conversations",
        ["last_message_at"],
    )

    # Create message_type_enum using raw SQL
    op.execute(
        "CREATE TYPE message_type_enum AS ENUM "
        "('text', 'system', 'booking_request', 'booking_confirmed', 'booking_cancelled')"
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column(
            "id",
            UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            UUID(as_uuid=False),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_id",
            UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "message_type",
            ENUM(
                "text",
                "system",
                "booking_request",
                "booking_confirmed",
                "booking_cancelled",
                name="message_type_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="text",
        ),
        sa.Column(
            "read_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        # Timestamps
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

    # Create indexes for messages
    op.create_index(
        "ix_messages_conversation_id",
        "messages",
        ["conversation_id"],
    )
    op.create_index(
        "ix_messages_sender_id",
        "messages",
        ["sender_id"],
    )
    op.create_index(
        "ix_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at"],
    )
    op.create_index(
        "ix_messages_conversation_read_at",
        "messages",
        ["conversation_id", "read_at"],
    )


def downgrade() -> None:
    """Drop conversations and messages tables."""
    # Drop indexes for messages
    op.drop_index("ix_messages_conversation_read_at", table_name="messages")
    op.drop_index("ix_messages_conversation_created", table_name="messages")
    op.drop_index("ix_messages_sender_id", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")

    # Drop messages table
    op.drop_table("messages")

    # Drop the enum type
    sa.Enum(name="message_type_enum").drop(op.get_bind(), checkfirst=True)

    # Drop indexes for conversations
    op.drop_index("ix_conversations_last_message_at", table_name="conversations")
    op.drop_index("ix_conversations_participant_2", table_name="conversations")
    op.drop_index("ix_conversations_participant_1", table_name="conversations")

    # Drop conversations table
    op.drop_table("conversations")
