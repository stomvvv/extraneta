import uuid
from typing import Optional
from datetime import date
from fastapi import APIRouter, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DB, get_hotel_membership
from app.models.booking import Booking, OTASource, PaymentStatus, BookingStatus
from app.schemas.booking import BookingOut, BookingListResponse

router = APIRouter(prefix="/hotels/{hotel_id}/bookings", tags=["bookings"])


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    hotel_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    source_ota: Optional[list[OTASource]] = Query(None),
    payment_status: Optional[list[PaymentStatus]] = Query(None),
    booking_status: Optional[list[BookingStatus]] = Query(None),
    check_in_from: Optional[date] = Query(None),
    check_in_to: Optional[date] = Query(None),
    guest_name: Optional[str] = Query(None),
    booking_id_ota: Optional[str] = Query(None),
    is_anomaly: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: str = Query("check_in"),
    sort_desc: bool = Query(True),
):
    await get_hotel_membership(hotel_id, current_user, db)

    filters = [Booking.hotel_id == hotel_id]
    if source_ota:
        filters.append(Booking.source_ota.in_(source_ota))
    if payment_status:
        filters.append(Booking.payment_status.in_(payment_status))
    if booking_status:
        filters.append(Booking.booking_status.in_(booking_status))
    if check_in_from:
        filters.append(Booking.check_in >= check_in_from)
    if check_in_to:
        filters.append(Booking.check_in <= check_in_to)
    if guest_name:
        filters.append(Booking.guest_name.ilike(f"%{guest_name}%"))
    if booking_id_ota:
        filters.append(Booking.booking_id_ota.ilike(f"%{booking_id_ota}%"))
    if is_anomaly is not None:
        filters.append(Booking.is_anomaly == is_anomaly)

    # Count
    count_result = await db.execute(
        select(func.count(Booking.id)).where(and_(*filters))
    )
    total = count_result.scalar()

    # Sort
    sort_col = getattr(Booking, sort_by, Booking.check_in)
    order = sort_col.desc() if sort_desc else sort_col.asc()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Booking)
        .where(and_(*filters))
        .order_by(order)
        .offset(offset)
        .limit(page_size)
    )
    bookings = result.scalars().all()

    return BookingListResponse(
        items=bookings,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )
