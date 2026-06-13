from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models.upload import Upload
from models.booking import Booking
from models.hotel import Hotel
from models.commission_setting import CommissionSetting
from parsers import PARSERS
from services.anomaly_detector import detect_anomalies

router = APIRouter()


@router.get("/uploads")
def list_uploads(hotel_id: Optional[int] = None, db: Session = Depends(get_db)):
    if not hotel_id:
        first = db.query(Hotel).order_by(Hotel.id).first()
        hotel_id = first.id if first else None

    q = db.query(Upload)
    if hotel_id:
        q = q.filter(Upload.hotel_id == hotel_id)
    uploads = q.order_by(Upload.uploaded_at.desc()).all()
    return [_upload_dict(u) for u in uploads]


@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    ota: str = Form(...),
    hotel_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    # Resolve hotel
    if not hotel_id:
        first = db.query(Hotel).order_by(Hotel.id).first()
        if not first:
            raise HTTPException(status_code=400, detail="Сначала создайте отель в настройках")
        hotel_id = first.id

    hotel = db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    file_bytes = file.file.read()
    filename = file.filename or "upload"

    # Create upload record
    upload = Upload(
        hotel_id=hotel_id,
        filename=filename,
        ota=ota,
        status="processing",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    # Get expected commission rate for anomaly detection
    cs = db.query(CommissionSetting).filter(
        CommissionSetting.hotel_id == hotel_id,
        CommissionSetting.ota == ota,
    ).first()
    expected_rate = float(cs.expected_rate) if cs else 15.0

    try:
        parser_cls = PARSERS.get(ota)
        if not parser_cls:
            raise ValueError(f"Неизвестный OTA: {ota}. Доступные: {', '.join(PARSERS.keys())}")

        parser = parser_cls()
        parsed = parser.parse(file_bytes, filename)

        added = 0
        skipped = 0
        for pb in parsed:
            # Deduplication
            exists = db.query(Booking).filter(
                Booking.source_ota == ota,
                Booking.booking_id_ota == pb.booking_id_ota,
                Booking.hotel_id == hotel_id,
            ).first()
            if exists:
                skipped += 1
                continue

            has_anomaly, anomaly_reason = detect_anomalies(pb, expected_rate)
            from datetime import datetime
            nights = (pb.check_out - pb.check_in).days or 1
            booking = Booking(
                hotel_id=hotel_id,
                upload_id=upload.id,
                source_ota=ota,
                booking_id_ota=pb.booking_id_ota,
                guest_name=pb.guest_name,
                room_type=pb.room_type,
                check_in=pb.check_in,
                check_out=pb.check_out,
                nights=nights,
                gross_amount=pb.gross_amount,
                ota_commission_rate=pb.ota_commission_rate,
                ota_commission_amount=pb.ota_commission_amount,
                net_amount=pb.net_amount,
                booking_status=pb.booking_status,
                payment_status=pb.payment_status,
                has_anomaly=has_anomaly,
                anomaly_reason=anomaly_reason,
                raw_row={str(k): str(v) for k, v in pb.raw_row.items()},
            )
            db.add(booking)
            added += 1

        upload.status = "done"
        upload.records_total = len(parsed)
        upload.records_added = added
        upload.records_skipped = skipped
        db.commit()

    except Exception as e:
        upload.status = "error"
        upload.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=422, detail=str(e))

    return _upload_dict(upload)


@router.delete("/uploads/{upload_id}", status_code=204)
def delete_upload(upload_id: int, db: Session = Depends(get_db)):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    # Delete associated bookings
    db.query(Booking).filter(Booking.upload_id == upload_id).delete()
    db.delete(upload)
    db.commit()


def _upload_dict(u: Upload) -> dict:
    return {
        "id": u.id,
        "hotel_id": u.hotel_id,
        "filename": u.filename,
        "ota": u.ota,
        "status": u.status,
        "records_total": u.records_total,
        "records_added": u.records_added,
        "records_skipped": u.records_skipped,
        "error_message": u.error_message,
        "uploaded_at": str(u.uploaded_at),
    }
