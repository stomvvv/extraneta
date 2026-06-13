from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from database import get_db
from models.booking import Booking
from models.hotel import Hotel

router = APIRouter()


def _parse_period(period: str) -> tuple[date, date]:
    today = date.today()
    mapping = {
        "7d": today - timedelta(days=7),
        "30d": today - timedelta(days=30),
        "90d": today - timedelta(days=90),
        "180d": today - timedelta(days=180),
        "365d": today - timedelta(days=365),
    }
    if period in mapping:
        return mapping[period], today
    # Try to parse as date range "YYYY-MM-DD,YYYY-MM-DD"
    if "," in period:
        parts = period.split(",")
        try:
            return date.fromisoformat(parts[0]), date.fromisoformat(parts[1])
        except Exception:
            pass
    return today - timedelta(days=30), today


@router.get("/dashboard")
def dashboard(
    hotel_id: Optional[int] = None,
    period: str = "30d",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if date_from and date_to:
        try:
            d_from = date.fromisoformat(date_from)
            d_to = date.fromisoformat(date_to)
        except Exception:
            d_from, d_to = _parse_period(period)
    else:
        d_from, d_to = _parse_period(period)

    # If no hotel_id — pick first hotel
    if not hotel_id:
        first = db.query(Hotel).order_by(Hotel.id).first()
        hotel_id = first.id if first else None

    filters = [Booking.check_in >= d_from, Booking.check_in <= d_to]
    if hotel_id:
        filters.append(Booking.hotel_id == hotel_id)

    bookings = db.query(Booking).filter(and_(*filters)).all()

    total_bookings = len(bookings)
    confirmed = [b for b in bookings if b.booking_status == "confirmed"]
    cancelled = [b for b in bookings if b.booking_status == "cancelled"]

    gross_revenue = sum(float(b.gross_amount) for b in confirmed)
    total_commission = sum(float(b.ota_commission_amount) for b in confirmed)
    net_revenue = gross_revenue - total_commission
    avg_booking_value = gross_revenue / len(confirmed) if confirmed else 0
    commission_rate_pct = (total_commission / gross_revenue * 100) if gross_revenue else 0

    # Time series (monthly)
    monthly: dict[str, dict] = {}
    for b in confirmed:
        key = b.check_in.strftime("%Y-%m")
        if key not in monthly:
            monthly[key] = {"gross": 0.0, "commission": 0.0, "bookings": 0}
        monthly[key]["gross"] += float(b.gross_amount)
        monthly[key]["commission"] += float(b.ota_commission_amount)
        monthly[key]["bookings"] += 1

    time_series = [
        {
            "period": k,
            "gross_revenue": round(v["gross"], 2),
            "commission_amount": round(v["commission"], 2),
            "net_revenue": round(v["gross"] - v["commission"], 2),
            "bookings": v["bookings"],
        }
        for k, v in sorted(monthly.items())
    ]

    # Channel breakdown
    channels: dict[str, dict] = {}
    for b in confirmed:
        ota = b.source_ota
        if ota not in channels:
            channels[ota] = {"gross": 0.0, "commission": 0.0, "bookings": 0}
        channels[ota]["gross"] += float(b.gross_amount)
        channels[ota]["commission"] += float(b.ota_commission_amount)
        channels[ota]["bookings"] += 1

    channel_list = [
        {
            "source_ota": ota,
            "gross_revenue": round(v["gross"], 2),
            "commission_amount": round(v["commission"], 2),
            "net_revenue": round(v["gross"] - v["commission"], 2),
            "bookings": v["bookings"],
            "commission_rate_pct": round(v["commission"] / v["gross"] * 100, 2) if v["gross"] else 0,
            "share_pct": round(v["gross"] / gross_revenue * 100, 2) if gross_revenue else 0,
        }
        for ota, v in sorted(channels.items(), key=lambda x: -x[1]["gross"])
    ]

    anomaly_count = sum(1 for b in bookings if b.has_anomaly)

    return {
        "kpi": {
            "gross_revenue": round(gross_revenue, 2),
            "total_commission": round(total_commission, 2),
            "net_revenue": round(net_revenue, 2),
            "commission_rate_pct": round(commission_rate_pct, 2),
            "total_bookings": total_bookings,
            "confirmed_bookings": len(confirmed),
            "cancelled_bookings": len(cancelled),
            "avg_booking_value": round(avg_booking_value, 2),
            "anomaly_count": anomaly_count,
        },
        "time_series": time_series,
        "channels": channel_list,
        "period": {"date_from": str(d_from), "date_to": str(d_to)},
    }
