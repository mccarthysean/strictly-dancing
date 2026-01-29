"""create reviews table.

Revision ID: 000000000009
Revises: 000000000008
Create Date: 2026-01-29 08:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000009"
down_revision: str | None = "000000000008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create reviews table
    op.create_table(
        "reviews",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()::text"),
            nullable=False,
        ),
        sa.Column("booking_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("reviewee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("host_response", sa.Text(), nullable=True),
        sa.Column("host_responded_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewee_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("booking_id"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range_1_to_5"),
    )

    # Create indexes
    op.create_index("ix_reviews_booking_id", "reviews", ["booking_id"], unique=True)
    op.create_index("ix_reviews_reviewer_id", "reviews", ["reviewer_id"])
    op.create_index("ix_reviews_reviewee_id", "reviews", ["reviewee_id"])

    # Create function to update host_profile rating_average and total_reviews
    op.execute("""
        CREATE OR REPLACE FUNCTION update_host_rating_stats()
        RETURNS TRIGGER AS $$
        DECLARE
            host_profile_uuid UUID;
            new_avg NUMERIC(3, 2);
            new_total INTEGER;
        BEGIN
            -- Get the host_profile_id for this reviewee
            -- We find it via booking -> host_profile_id
            SELECT b.host_profile_id INTO host_profile_uuid
            FROM bookings b
            WHERE b.id = NEW.booking_id::uuid;

            -- Calculate new average rating and total reviews for this host profile
            SELECT
                ROUND(AVG(r.rating)::numeric, 2),
                COUNT(*)
            INTO new_avg, new_total
            FROM reviews r
            JOIN bookings b ON r.booking_id = b.id::text
            WHERE b.host_profile_id = host_profile_uuid;

            -- Update the host_profile
            UPDATE host_profiles
            SET
                rating_average = new_avg,
                total_reviews = new_total,
                updated_at = NOW()
            WHERE id = host_profile_uuid::text;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger to update stats on review insert
    op.execute("""
        CREATE TRIGGER trigger_update_host_rating_on_review_insert
        AFTER INSERT ON reviews
        FOR EACH ROW
        EXECUTE FUNCTION update_host_rating_stats();
    """)

    # Create trigger to update stats on review update (rating change)
    op.execute("""
        CREATE TRIGGER trigger_update_host_rating_on_review_update
        AFTER UPDATE OF rating ON reviews
        FOR EACH ROW
        WHEN (OLD.rating IS DISTINCT FROM NEW.rating)
        EXECUTE FUNCTION update_host_rating_stats();
    """)

    # Create function to update stats on review delete
    op.execute("""
        CREATE OR REPLACE FUNCTION update_host_rating_stats_on_delete()
        RETURNS TRIGGER AS $$
        DECLARE
            host_profile_uuid UUID;
            new_avg NUMERIC(3, 2);
            new_total INTEGER;
        BEGIN
            -- Get the host_profile_id for this reviewee
            SELECT b.host_profile_id INTO host_profile_uuid
            FROM bookings b
            WHERE b.id = OLD.booking_id::uuid;

            -- Calculate new average rating and total reviews
            SELECT
                ROUND(AVG(r.rating)::numeric, 2),
                COUNT(*)
            INTO new_avg, new_total
            FROM reviews r
            JOIN bookings b ON r.booking_id = b.id::text
            WHERE b.host_profile_id = host_profile_uuid;

            -- Update the host_profile (new_avg will be NULL if no reviews remain)
            UPDATE host_profiles
            SET
                rating_average = new_avg,
                total_reviews = COALESCE(new_total, 0),
                updated_at = NOW()
            WHERE id = host_profile_uuid::text;

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger for review delete
    op.execute("""
        CREATE TRIGGER trigger_update_host_rating_on_review_delete
        AFTER DELETE ON reviews
        FOR EACH ROW
        EXECUTE FUNCTION update_host_rating_stats_on_delete();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute(
        "DROP TRIGGER IF EXISTS trigger_update_host_rating_on_review_delete ON reviews"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trigger_update_host_rating_on_review_update ON reviews"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trigger_update_host_rating_on_review_insert ON reviews"
    )

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_host_rating_stats_on_delete()")
    op.execute("DROP FUNCTION IF EXISTS update_host_rating_stats()")

    # Drop indexes
    op.drop_index("ix_reviews_reviewee_id", table_name="reviews")
    op.drop_index("ix_reviews_reviewer_id", table_name="reviews")
    op.drop_index("ix_reviews_booking_id", table_name="reviews")

    # Drop table
    op.drop_table("reviews")
