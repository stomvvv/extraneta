from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models.hotel import Hotel
from models.commission_setting import CommissionSetting
from parsers import DEFAULT_COMMISSION_RATES

router = APIRouter()


class HotelCreate(BaseModel):
    name: str
    address: Optional[str] = ""


class HotelUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None


class HotelOut(BaseModel):
    id: int
    name: str
    address: str

    class Config:
        from_attributes = True


@router.get("/hotels", response_model=list[HotelOut])
def list_hotels(db: Session = Depends(get_db)):
    return db.query(Hotel).order_by(Hotel.id).all()


@router.post("/hotels", response_model=HotelOut, status_code=201)
def create_hotel(data: HotelCreate, db: Session = Depends(get_db)):
    hotel = Hotel(name=data.name.strip(), address=data.address or "")
    db.add(hotel)
    db.flush()
    # Seed default commission settings
    for ota, rate in DEFAULT_COMMISSION_RATES.items():
        cs = CommissionSetting(hotel_id=hotel.id, ota=ota, expected_rate=rate)
        db.add(cs)
    db.commit()
    db.refresh(hotel)
    return hotel


@router.patch("/hotels/{hotel_id}", response_model=HotelOut)
def update_hotel(hotel_id: int, data: HotelUpdate, db: Session = Depends(get_db)):
    hotel = db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    if data.name is not None:
        hotel.name = data.name.strip()
    if data.address is not None:
        hotel.address = data.address
    db.commit()
    db.refresh(hotel)
    return hotel


@router.delete("/hotels/{hotel_id}", status_code=204)
def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    db.delete(hotel)
    db.commit()
