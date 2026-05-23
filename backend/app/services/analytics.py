from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, OTASource, PaymentStatus, BookingStatus
from app.models.hotel import Hotel
from app.schemas.analytics import SummaryMetrics, ChannelMetrics, TimeSeriesPoint, AnomalySummary


def _pct_change(new: Decimal, old: Decimal) -> Optional[Decimal]:
    if old == 0:
        return None
    return ((new - old) / abs(old)) * 100


class AnalyticsService:

    @staticmethod
    async def get_summary(
        db: AsyncSession,
        hotel_id: UUID,
        date_from: date,
        date_to: date,
        compare_from: Optional[date] = None,
        compare_to: Optional[date] = None,
    ) -> SummaryMetrics:
        def _base_query(d_from: date, d_to: date):
            return and_(
                Booking.hotel_id == hotel_id,
                Booking.check_in >= d_from,
                Booking.check_in <= d_to,
                Booking.payment_status != PaymentStatus.cancelled,
            )

        # Current period
        r = await db.execute(
            select(
                func.coalesce(func.sum(Booking.gross_amount), Decimal(0)).label("gross"),
                func.coalesce(func.sum(Booking.ota_commission_amount), Decimal(0)).label("commission"),
                func.coalesce(func.sum(Booking.net_amount), Decimal(0)).label("net"),
                func.count(Booking.id).label("total"),
                func.sum(case((Booking.booking_status == BookingStatus.confirmed, 1), else_=0)).label("confirmed"),
                func.sum(case((Booking.booking_status == BookingStatus.cancelled, 1), else_=0)).label("cancelled"),
                func.coalesce(func.avg(Booking.gross_amount), Decimal(0)).label("avg_booking"),
            ).where(_base_query(date_from, date_to))
        )
        row = r.one()

        gross = row.gross or Decimal(0)
        commission = row.commission or Decimal(0)
        net = row.net or Decimal(0)
        total = row.total or 0
        commission_rate = (commission / gross * 100) if gross else Decimal(0)

        # Hotel room count for occupancy
        hotel_result = await db.execute(select(Hotel).where(Hotel.id == hotel_id))
        hotel = hotel_result.scalar_one_or_none()
        occupancy = None
        if hotel and hotel.room_count and total > 0:
            days = (date_to - date_from).days or 1
            occupied_nights = await db.execute(
                select(func.coalesce(func.sum(Booking.nights), 0))
                .where(_base_query(date_from, date_to))
                .where(Booking.booking_status == BookingStatus.confirmed)
            )
            occ_nights = occupied_nights.scalar() or 0
            available_nights = hotel.room_count * days
            occupancy = Decimal(occ_nights) / Decimal(available_nights) * 100 if available_nights else None

        # Compare period
        gross_change = net_change = bookings_change = None
        if compare_from and compare_to:
            rc = await db.execute(
                select(
                    func.coalesce(func.sum(Booking.gross_amount), Decimal(0)).label("gross"),
                    func.coalesce(func.sum(Booking.net_amount), Decimal(0)).label("net"),
                    func.count(Booking.id).label("total"),
                ).where(_base_query(compare_from, compare_to))
            )
            prev = rc.one()
            gross_change = _pct_change(gross, prev.gross or Decimal(0))
            net_change = _pct_change(net, prev.net or Decimal(0))
            bookings_change = _pct_change(Decimal(total), Decimal(prev.total or 0))

        return SummaryMetrics(
            gross_revenue=gross,
            total_commission=commission,
            net_revenue=net,
            commission_rate_pct=commission_rate,
            total_bookings=total,
            confirmed_bookings=row.confirmed or 0,
            cancelled_bookings=row.cancelled or 0,
            avg_booking_value=row.avg_booking or Decimal(0),
            occupancy_pct=occupancy,
            period_start=date_from,
            period_end=date_to,
            gross_revenue_change_pct=gross_change,
            net_revenue_change_pct=net_change,
            bookings_change_pct=bookings_change,
        )

    @staticmethod
    async def get_channels(
        db: AsyncSession,
        hotel_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[ChannelMetrics]:
        r = await db.execute(
            select(
                Booking.source_ota,
                func.count(Booking.id).label("cnt"),
                func.coalesce(func.sum(Booking.gross_amount), Decimal(0)).label("gross"),
                func.coalesce(func.sum(Booking.ota_commission_amount), Decimal(0)).label("commission"),
                func.coalesce(func.sum(Booking.net_amount), Decimal(0)).label("net"),
                func.coalesce(func.avg(Booking.gross_amount), Decimal(0)).label("avg_val"),
            )
            .where(
                Booking.hotel_id == hotel_id,
                Booking.check_in >= date_from,
                Booking.check_in <= date_to,
                Booking.payment_status != PaymentStatus.cancelled,
            )
            .group_by(Booking.source_ota)
            .order_by(func.sum(Booking.gross_amount).desc())
        )
        rows = r.all()

        total_gross = sum(row.gross for row in rows) or Decimal(1)

        return [
            ChannelMetrics(
                source_ota=row.source_ota.value,
                bookings_count=row.cnt,
                gross_revenue=row.gross,
                commission_amount=row.commission,
                commission_rate_pct=(row.commission / row.gross * 100) if row.gross else Decimal(0),
                net_revenue=row.net,
                channel_share_pct=row.gross / total_gross * 100,
                avg_booking_value=row.avg_val,
            )
            for row in rows
        ]

    @staticmethod
    async def get_time_series(
        db: AsyncSession,
        hotel_id: UUID,
        date_from: date,
        date_to: date,
        granularity: str = "month",  # "month" | "week"
    ) -> list[TimeSeriesPoint]:
        if granularity == "week":
            period_expr = func.to_char(Booking.check_in, "IYYY-IW")
        else:
            period_expr = func.to_char(Booking.check_in, "YYYY-MM")

        r = await db.execute(
            select(
                period_expr.label("period"),
                func.coalesce(func.sum(Booking.gross_amount), Decimal(0)).label("gross"),
                func.coalesce(func.sum(Booking.ota_commission_amount), Decimal(0)).label("commission"),
                func.coalesce(func.sum(Booking.net_amount), Decimal(0)).label("net"),
                func.count(Booking.id).label("cnt"),
            )
            .where(
                Booking.hotel_id == hotel_id,
                Booking.check_in >= date_from,
                Booking.check_in <= date_to,
                Booking.payment_status != PaymentStatus.cancelled,
            )
            .group_by("period")
            .order_by("period")
        )

        return [
            TimeSeriesPoint(
                period=row.period,
                gross_revenue=row.gross,
                commission_amount=row.commission,
                net_revenue=row.net,
                bookings_count=row.cnt,
            )
            for row in r.all()
        ]

    @staticmethod
    async def get_anomaly_summary(db: AsyncSession, hotel_id: UUID, date_from: date, date_to: date) -> AnomalySummary:
        r = await db.execute(
            select(
                func.count(Booking.id).label("total"),
                func.coalesce(func.sum(Booking.gross_amount), Decimal(0)).label("affected"),
            )
            .where(
                Booking.hotel_id == hotel_id,
                Booking.check_in >= date_from,
                Booking.check_in <= date_to,
                Booking.is_anomaly == True,
            )
        )
        row = r.one()

        return AnomalySummary(
            total_anomalies=row.total or 0,
            commission_rate_deviations=0,  # TODO: parse anomaly_reasons for breakdown
            duplicate_bookings=0,
            invalid_commissions=0,
            cancelled_unreturned=0,
            affected_revenue=row.affected or Decimal(0),
        )
