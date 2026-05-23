from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.models.booking import OTASource, PaymentStatus, BookingStatus


class BookingOut(BaseModel):
    id: UUID
    hotel_id: UUID
    upload_id: Optional[UUID]
    source_ota: OTASource
    booking_id_ota: str
    guest_name: str
    room_type: Optional[str]
    booking_date: Optional[date]
    check_in: date
    check_out: date
    nights: int
    gross_amount: Decimal
    ota_commission_rate: Decimal
    ota_commission_amount: Decimal
    net_amount: Decimal
    currency: str
    payment_status: PaymentStatus
    booking_status: BookingStatus
    has_vat: bool
    is_anomaly: bool
    anomaly_reasons: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class BookingFilter(BaseModel):
    source_ota: Optional[list[OTASource]] = None
    payment_status: Optional[list[PaymentStatus]] = None
    booking_status: Optional[list[BookingStatus]] = None
    check_in_from: Optional[date] = None
    check_in_to: Optional[date] = None
    guest_name: Optional[str] = None
    booking_id_ota: Optional[str] = None
    is_anomaly: Optional[bool] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)
    sort_by: str = "check_in"
    sort_desc: bool = True


class BookingListResponse(BaseModel):
    items: list[BookingOut]
    total: int
    page: int
    page_size: int
    total_pages: int
