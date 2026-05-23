import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DB, get_hotel_membership
from app.services.analytics import AnalyticsService
from app.schemas.analytics import SummaryMetrics, ChannelMetrics, TimeSeriesPoint, AnomalySummary

router = APIRouter(prefix="/hotels/{hotel_id}/analytics", tags=["analytics"])


def _default_dates():
    from datetime import date
    today = date.today()
    return date(today.year, today.month, 1), today


@router.get("/summary", response_model=SummaryMetrics)
async def get_summary(
    hotel_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    compare_from: Optional[date] = Query(None),
    compare_to: Optional[date] = Query(None),
):
    await get_hotel_membership(hotel_id, current_user, db)
    if not date_from or not date_to:
        date_from, date_to = _default_dates()
    return await AnalyticsService.get_summary(db, hotel_id, date_from, date_to, compare_from, compare_to)


@router.get("/channels", response_model=list[ChannelMetrics])
async def get_channels(
    hotel_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    await get_hotel_membership(hotel_id, current_user, db)
    if not date_from or not date_to:
        date_from, date_to = _default_dates()
    return await AnalyticsService.get_channels(db, hotel_id, date_from, date_to)


@router.get("/time-series", response_model=list[TimeSeriesPoint])
async def get_time_series(
    hotel_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    granularity: str = Query("month", pattern="^(month|week)$"),
):
    await get_hotel_membership(hotel_id, current_user, db)
    if not date_from or not date_to:
        date_from, date_to = _default_dates()
    return await AnalyticsService.get_time_series(db, hotel_id, date_from, date_to, granularity)


@router.get("/anomalies", response_model=AnomalySummary)
async def get_anomaly_summary(
    hotel_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    await get_hotel_membership(hotel_id, current_user, db)
    if not date_from or not date_to:
        date_from, date_to = _default_dates()
    return await AnalyticsService.get_anomaly_summary(db, hotel_id, date_from, date_to)
