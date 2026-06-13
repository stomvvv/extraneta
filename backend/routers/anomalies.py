from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, timedelta
from typing import Optional
from database import get_db
from models.booking import Booking
from models.hotel import Hotel

router = APIRouter()


@router.get("/anomalies")
def list_anomalies(
    hotel_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if not hotel_id:
        first = db.query(Hotel).order_by(Hotel.id).first()
        hotel_id = first.id if first else None

    filters = [Booking.has_anomaly == True]
    if hotel_id:
        filters.append(Booking.hotel_id == hotel_id)
    if date_from:
        try:
            filters.append(Booking.check_in >= date.fromisoformat(date_from))
        except Exception:
            pass
    if date_to:
        try:
            filters.append(Booking.check_in <= date.fromisoformat(date_to))
        except Exception:
            pass

    bookings = db.query(Booking).filter(and_(*filters)).order_by(Booking.check_in.desc()).all()

    return {
        "total": len(bookings),
        "items": [
            {
                "id": b.id,
                "source_ota": b.source_ota,
                "booking_id_ota": b.booking_id_ota,
                "guest_name": b.guest_name,
                "check_in": str(b.check_in),
                "gross_amount": float(b.gross_amount),
                "ota_commission_rate": float(b.ota_commission_rate),
                "booking_status": b.booking_status,
                "anomaly_reason": b.anomaly_reason,
            }
            for b in bookings
        ],
    }
