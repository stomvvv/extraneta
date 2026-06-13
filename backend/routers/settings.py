from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models.booking import Booking
from models.hotel import Hotel
from models.commission_setting import CommissionSetting
from models.upload import Upload

router = APIRouter()


class CommissionUpdate(BaseModel):
    ota: str
    expected_rate: float


@router.get("/settings/commissions")
def get_commissions(hotel_id: Optional[int] = None, db: Session = Depends(get_db)):
    if not hotel_id:
        first = db.query(Hotel).order_by(Hotel.id).first()
        hotel_id = first.id if first else None

    if not hotel_id:
        return []

    settings = db.query(CommissionSetting).filter(
        CommissionSetting.hotel_id == hotel_id
    ).all()
    return [{"id": s.id, "ota": s.ota, "expected_rate": float(s.expected_rate)} for s in settings]


@router.put("/settings/commissions")
def update_commissions(
    updates: list[CommissionUpdate],
    hotel_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    if not hotel_id:
        first = db.query(Hotel).order_by(Hotel.id).first()
        hotel_id = first.id if first else None

    if not hotel_id:
        raise HTTPException(status_code=400, detail="No hotel found")

    for update in updates:
        cs = db.query(CommissionSetting).filter(
            CommissionSetting.hotel_id == hotel_id,
            CommissionSetting.ota == update.ota,
        ).first()
        if cs:
            cs.expected_rate = update.expected_rate
        else:
            db.add(CommissionSetting(
                hotel_id=hotel_id,
                ota=update.ota,
                expected_rate=update.expected_rate,
            ))
    db.commit()
    return {"ok": True}


@router.delete("/settings/data", status_code=204)
def clear_all_data(hotel_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Clear all bookings and uploads for a hotel."""
    if not hotel_id:
        first = db.query(Hotel).order_by(Hotel.id).first()
        hotel_id = first.id if first else None

    if hotel_id:
        db.query(Booking).filter(Booking.hotel_id == hotel_id).delete()
        db.query(Upload).filter(Upload.hotel_id == hotel_id).delete()
        db.commit()
