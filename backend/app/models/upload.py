import uuid
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import String, ForeignKey, Enum, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.booking import OTASource


class UploadStatus(str, PyEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class DocumentType(str, PyEnum):
    booking_report = "booking_report"
    financial_report = "financial_report"
    reconciliation_act = "reconciliation_act"


class Upload(Base, TimestampMixin):
    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # File info
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # OTA metadata
    source_ota: Mapped[OTASource] = mapped_column(Enum(OTASource), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType), nullable=False, default=DocumentType.booking_report
    )
    report_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    report_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Processing
    status: Mapped[UploadStatus] = mapped_column(
        Enum(UploadStatus), nullable=False, default=UploadStatus.pending
    )
    bookings_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bookings_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="uploads")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="upload")
