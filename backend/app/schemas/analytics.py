from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import date


class SummaryMetrics(BaseModel):
    gross_revenue: Decimal
    total_commission: Decimal
    net_revenue: Decimal
    commission_rate_pct: Decimal
    total_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    avg_booking_value: Decimal
    occupancy_pct: Optional[Decimal]
    period_start: date
    period_end: date

    # vs previous period
    gross_revenue_change_pct: Optional[Decimal] = None
    net_revenue_change_pct: Optional[Decimal] = None
    bookings_change_pct: Optional[Decimal] = None


class ChannelMetrics(BaseModel):
    source_ota: str
    bookings_count: int
    gross_revenue: Decimal
    commission_amount: Decimal
    commission_rate_pct: Decimal
    net_revenue: Decimal
    channel_share_pct: Decimal
    avg_booking_value: Decimal


class TimeSeriesPoint(BaseModel):
    period: str  # "2025-01" or "2025-W03"
    gross_revenue: Decimal
    commission_amount: Decimal
    net_revenue: Decimal
    bookings_count: int


class AnomalySummary(BaseModel):
    total_anomalies: int
    commission_rate_deviations: int
    duplicate_bookings: int
    invalid_commissions: int
    cancelled_unreturned: int
    affected_revenue: Decimal
