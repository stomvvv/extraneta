import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.api.deps import CurrentUser, DB, get_hotel_membership
from app.services.export import export_excel, export_pdf

router = APIRouter(prefix="/hotels/{hotel_id}/reports", tags=["reports"])


def _default_dates():
    from datetime import date
    today = date.today()
    return date(today.year, today.month, 1), today


@router.get("/excel")
async def download_excel(
    hotel_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    await get_hotel_membership(hotel_id, current_user, db)
    if not date_from or not date_to:
        date_from, date_to = _default_dates()

    xlsx_bytes = await export_excel(db, hotel_id, date_from, date_to)
    filename = f"extraneta_{date_from}_{date_to}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/pdf")
async def download_pdf(
    hotel_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    await get_hotel_membership(hotel_id, current_user, db)
    if not date_from or not date_to:
        date_from, date_to = _default_dates()

    pdf_bytes = await export_pdf(db, hotel_id, date_from, date_to)
    filename = f"extraneta_{date_from}_{date_to}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
