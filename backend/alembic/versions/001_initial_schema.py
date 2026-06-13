"""Initial schema v3

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hotels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(500), nullable=True, server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "uploads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hotel_id", sa.Integer(), sa.ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("ota", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="processing"),
        sa.Column("records_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True, server_default=""),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_uploads_hotel_id", "uploads", ["hotel_id"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hotel_id", sa.Integer(), sa.ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("upload_id", sa.Integer(), sa.ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_ota", sa.String(50), nullable=False),
        sa.Column("booking_id_ota", sa.String(100), nullable=False),
        sa.Column("guest_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("room_type", sa.String(255), nullable=True, server_default=""),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("nights", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("gross_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("ota_commission_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("ota_commission_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("net_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("payment_status", sa.String(20), nullable=False, server_default="paid"),
        sa.Column("booking_status", sa.String(20), nullable=False, server_default="confirmed"),
        sa.Column("has_anomaly", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("anomaly_reason", sa.Text(), nullable=True, server_default=""),
        sa.Column("raw_row", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bookings_hotel_id", "bookings", ["hotel_id"])
    op.create_index("ix_bookings_source_ota", "bookings", ["source_ota"])
    op.create_index("ix_bookings_check_in", "bookings", ["check_in"])

    op.create_table(
        "commission_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hotel_id", sa.Integer(), sa.ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ota", sa.String(50), nullable=False),
        sa.Column("expected_rate", sa.Numeric(5, 2), nullable=False, server_default="15.0"),
    )
    op.create_index("ix_commission_settings_hotel_id", "commission_settings", ["hotel_id"])


def downgrade() -> None:
    op.drop_table("commission_settings")
    op.drop_table("bookings")
    op.drop_table("uploads")
    op.drop_table("hotels")
