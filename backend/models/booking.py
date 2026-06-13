from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Numeric, JSON, ForeignKey
from database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=True)
    source_ota = Column(String, nullable=False, index=True)
    booking_id_ota = Column(String, nullable=False, index=True)
    guest_name = Column(String, default="")
    room_type = Column(String, default="")
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    nights = Column(Integer, default=1)
    gross_amount = Column(Numeric(10, 2), default=0)
    ota_commission_rate = Column(Numeric(5, 2), default=0)
    ota_commission_amount = Column(Numeric(10, 2), default=0)
    net_amount = Column(Numeric(10, 2), default=0)
    currency = Column(String, default="RUB")
    payment_status = Column(String, default="paid")
    booking_status = Column(String, default="confirmed")  # confirmed | cancelled | no_show
    has_anomaly = Column(Boolean, default=False)
    anomaly_reason = Column(String, default="")
    raw_row = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
