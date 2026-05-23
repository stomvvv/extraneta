import uuid
from sqlalchemy import String, Integer, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.user import UserRole


class Hotel(Base, TimestampMixin):
    __tablename__ = "hotels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    room_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Expected commission rates per OTA: {"yandex": 15.0, "ostrovok": 18.0, ...}
    expected_commission_rates: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Moscow", nullable=False)

    # Relationships
    members: Mapped[list["HotelMember"]] = relationship(
        "HotelMember", back_populates="hotel", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="hotel", cascade="all, delete-orphan"
    )
    uploads: Mapped[list["Upload"]] = relationship(
        "Upload", back_populates="hotel", cascade="all, delete-orphan"
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation", back_populates="hotel", cascade="all, delete-orphan"
    )


class HotelMember(Base, TimestampMixin):
    __tablename__ = "hotel_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.manager
    )

    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="hotel_memberships")


class Invitation(Base, TimestampMixin):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    from sqlalchemy import DateTime
    from datetime import datetime
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="invitations")
