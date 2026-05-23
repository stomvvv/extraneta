"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Pre-declare enums with create_type=False so create_table doesn't try to recreate them
userrole = postgresql.ENUM("owner", "manager", "accountant", name="userrole", create_type=False)
otasource = postgresql.ENUM(
    "yandex", "ostrovok", "bronevoy", "tinkoff", "2gis", "hotel101", "academservis",
    name="otasource", create_type=False,
)
documenttype = postgresql.ENUM(
    "booking_report", "financial_report", "reconciliation_act",
    name="documenttype", create_type=False,
)
uploadstatus = postgresql.ENUM("pending", "processing", "completed", "failed", name="uploadstatus", create_type=False)
paymentstatus = postgresql.ENUM("paid", "pending", "cancelled", "refunded", name="paymentstatus", create_type=False)
bookingstatus = postgresql.ENUM("confirmed", "cancelled", "no_show", name="bookingstatus", create_type=False)


def upgrade() -> None:
    # Create all enum types first via raw SQL
    op.execute("CREATE TYPE userrole AS ENUM ('owner', 'manager', 'accountant')")
    op.execute("CREATE TYPE otasource AS ENUM ('yandex', 'ostrovok', 'bronevoy', 'tinkoff', '2gis', 'hotel101', 'academservis')")
    op.execute("CREATE TYPE documenttype AS ENUM ('booking_report', 'financial_report', 'reconciliation_act')")
    op.execute("CREATE TYPE uploadstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('paid', 'pending', 'cancelled', 'refunded')")
    op.execute("CREATE TYPE bookingstatus AS ENUM ('confirmed', 'cancelled', 'no_show')")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(512), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"])

    op.create_table(
        "hotels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("room_count", sa.Integer(), nullable=True),
        sa.Column("expected_commission_rates", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Europe/Moscow"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "hotel_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hotel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", userrole, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["hotel_id"], ["hotels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hotel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", userrole, nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["hotel_id"], ["hotels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_invitations_token", "invitations", ["token"])

    op.create_table(
        "uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hotel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("source_ota", otasource, nullable=False),
        sa.Column("document_type", documenttype, nullable=False),
        sa.Column("report_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("report_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", uploadstatus, nullable=False, server_default="pending"),
        sa.Column("bookings_imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bookings_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["hotel_id"], ["hotels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_uploads_hotel_id", "uploads", ["hotel_id"])

    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hotel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_ota", otasource, nullable=False),
        sa.Column("booking_id_ota", sa.String(100), nullable=False),
        sa.Column("guest_name", sa.String(255), nullable=False),
        sa.Column("room_type", sa.String(255), nullable=True),
        sa.Column("booking_date", sa.Date(), nullable=True),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("nights", sa.Integer(), nullable=False),
        sa.Column("gross_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("ota_commission_rate", sa.Numeric(6, 4), nullable=False),
        sa.Column("ota_commission_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("net_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("payment_status", paymentstatus, nullable=False),
        sa.Column("booking_status", bookingstatus, nullable=False),
        sa.Column("has_vat", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_anomaly", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("anomaly_reasons", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["hotel_id"], ["hotels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upload_id"], ["uploads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bookings_hotel_id", "bookings", ["hotel_id"])
    op.create_index("ix_bookings_source_ota", "bookings", ["source_ota"])
    op.create_index("ix_bookings_check_in", "bookings", ["check_in"])
    op.create_index("ix_bookings_booking_id_ota", "bookings", ["booking_id_ota"])
    op.create_index("ix_bookings_hotel_ota_id", "bookings", ["hotel_id", "source_ota", "booking_id_ota"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("hotel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("details", postgresql.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["hotel_id"], ["hotels.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_hotel_id", "audit_logs", ["hotel_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("bookings")
    op.drop_table("uploads")
    op.drop_table("invitations")
    op.drop_table("hotel_members")
    op.drop_table("hotels")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    for enum_name in ["userrole", "otasource", "documenttype", "uploadstatus", "paymentstatus", "bookingstatus"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
