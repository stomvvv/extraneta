from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, timedelta
from typing import Optional
from database import get_db
from models.booking import Booking
from models.hotel import Hotel
from models.commission_setting import CommissionSetting
from parsers import OTA_NAMES

router = APIRouter()


@router.get("/channels")
def channels(
    hotel_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    period: str = "30d",
    db: Session = Depends(get_db),
):
    if not hotel_id:
        first = db.query(Hotel).order_by(Hotel.id).first()
        hotel_id = first.id if first else None

    if date_from and date_to:
        try:
            d_from = date.fromisoformat(date_from)
            d_to = date.fromisoformat(date_to)
        except Exception:
            d_from, d_to = _default_range(period)
    else:
        d_from, d_to = _default_range(period)

    filters = [Booking.check_in >= d_from, Booking.check_in <= d_to]
    if hotel_id:
        filters.append(Booking.hotel_id == hotel_id)

    bookings = db.query(Booking).filter(and_(*filters)).all()
    confirmed = [b for b in bookings if b.booking_status == "confirmed"]

    # Expected rates
    expected_rates: dict[str, float] = {}
    if hotel_id:
        settings = db.query(CommissionSetting).filter(
            CommissionSetting.hotel_id == hotel_id
        ).all()
        expected_rates = {s.ota: float(s.expected_rate) for s in settings}

    # Aggregate per OTA
    agg: dict[str, dict] = {}
    for b in confirmed:
        ota = b.source_ota
        if ota not in agg:
            agg[ota] = {"gross": 0.0, "commission": 0.0, "bookings": 0}
        agg[ota]["gross"] += float(b.gross_amount)
        agg[ota]["commission"] += float(b.ota_commission_amount)
        agg[ota]["bookings"] += 1

    total_gross = sum(v["gross"] for v in agg.values())

    result = []
    for ota, v in sorted(agg.items(), key=lambda x: -x[1]["gross"]):
        real_rate = (v["commission"] / v["gross"] * 100) if v["gross"] else 0
        expected_rate = expected_rates.get(ota, 15.0)
        deviation = real_rate - expected_rate
        status = "ok" if abs(deviation) <= 1.0 else "warning"
        result.append({
            "source_ota": ota,
            "ota_name": OTA_NAMES.get(ota, ota),
            "bookings": v["bookings"],
            "gross_revenue": round(v["gross"], 2),
            "commission_amount": round(v["commission"], 2),
            "net_revenue": round(v["gross"] - v["commission"], 2),
            "real_commission_rate": round(real_rate, 2),
            "expected_commission_rate": expected_rate,
            "deviation": round(deviation, 2),
            "status": status,
            "share_pct": round(v["gross"] / total_gross * 100, 2) if total_gross else 0,
        })

    return result


def _default_range(period: str) -> tuple[date, date]:
    today = date.today()
    days = {"7d": 7, "30d": 30, "90d": 90, "180d": 180, "365d": 365}
    return today - timedelta(days=days.get(period, 30)), today
