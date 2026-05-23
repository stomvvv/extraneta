import uuid
from enum import Enum as PyEnum
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Date, Numeric, ForeignKey, Enum, Boolean, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class OTASource(str, PyEnum):
    yandex = "yandex"
    ostrovok = "ostrovok"
    bronevoy = "bronevoy"
    tinkoff = "tinkoff"
    gis2 = "2gis"
    hotel101 = "hotel101"
    academservis = "academservis"


class PaymentStatus(str, PyEnum):
    paid = "paid"
    pending = "pending"
    cancelled = "cancelled"
    refunded = "refunded"


class BookingStatus(str, PyEnum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    no_show = "no_show"


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    upload_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True
    )

    # OTA info
    source_ota: Mapped[OTASource] = mapped_column(Enum(OTASource), nullable=False, index=True)
    booking_id_ota: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Guest info
    guest_name: Mapped[str] = mapped_column(String(255), nullable=False)
    room_type: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Dates
    booking_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    check_in: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    nights: Mapped[int] = mapped_column(Integer, nullable=False)

    # Financials
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    ota_commission_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    ota_commission_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)

    # Status
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), nullable=False, default=PaymentStatus.paid
    )
    booking_status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), nullable=False, default=BookingStatus.confirmed
    )

    # Flags
    has_vat: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_reasons: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="bookings")
    upload: Mapped["Upload | None"] = relationship("Upload", back_populates="bookings")
