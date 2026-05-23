import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy import select

from app.api.deps import CurrentUser, DB, get_hotel_membership
from app.models.upload import Upload, UploadStatus, DocumentType
from app.models.booking import OTASource
from app.schemas.upload import UploadOut, UploadPreview
from app.core.storage import upload_file, get_presigned_url, delete_file
from app.tasks.parse_upload import parse_upload_task

router = APIRouter(prefix="/hotels/{hotel_id}/uploads", tags=["uploads"])

ALLOWED_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
    "application/csv",
    "application/pdf",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("", response_model=UploadOut, status_code=201)
async def create_upload(
    hotel_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    file: UploadFile = File(...),
    source_ota: OTASource = Form(...),
    document_type: DocumentType = Form(DocumentType.booking_report),
    report_period_start: Optional[datetime] = Form(None),
    report_period_end: Optional[datetime] = Form(None),
):
    await get_hotel_membership(hotel_id, current_user, db)

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    content_type = file.content_type or "application/octet-stream"
    storage_key = f"{hotel_id}/{source_ota.value}/{uuid.uuid4()}/{file.filename}"
    upload_file(file_bytes, storage_key, content_type)

    upload = Upload(
        hotel_id=hotel_id,
        uploaded_by_id=current_user.id,
        original_filename=file.filename,
        storage_key=storage_key,
        file_size_bytes=len(file_bytes),
        content_type=content_type,
        source_ota=source_ota,
        document_type=document_type,
        report_period_start=report_period_start,
        report_period_end=report_period_end,
        status=UploadStatus.pending,
    )
    db.add(upload)
    await db.commit()
    await db.refresh(upload)

    # Enqueue parsing task
    task = parse_upload_task.delay(str(upload.id), str(hotel_id))
    upload.celery_task_id = task.id
    await db.commit()

    return upload


@router.get("", response_model=list[UploadOut])
async def list_uploads(hotel_id: uuid.UUID, current_user: CurrentUser, db: DB):
    await get_hotel_membership(hotel_id, current_user, db)
    result = await db.execute(
        select(Upload)
        .where(Upload.hotel_id == hotel_id)
        .order_by(Upload.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{upload_id}", response_model=UploadOut)
async def get_upload(hotel_id: uuid.UUID, upload_id: uuid.UUID, current_user: CurrentUser, db: DB):
    await get_hotel_membership(hotel_id, current_user, db)
    result = await db.execute(
        select(Upload).where(Upload.id == upload_id, Upload.hotel_id == hotel_id)
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


@router.delete("/{upload_id}", status_code=204)
async def delete_upload(hotel_id: uuid.UUID, upload_id: uuid.UUID, current_user: CurrentUser, db: DB):
    await get_hotel_membership(hotel_id, current_user, db)
    result = await db.execute(
        select(Upload).where(Upload.id == upload_id, Upload.hotel_id == hotel_id)
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    try:
        delete_file(upload.storage_key)
    except Exception:
        pass  # File may already be gone

    await db.delete(upload)
    await db.commit()


@router.post("/{upload_id}/reimport", response_model=UploadOut)
async def reimport_upload(hotel_id: uuid.UUID, upload_id: uuid.UUID, current_user: CurrentUser, db: DB):
    await get_hotel_membership(hotel_id, current_user, db)
    result = await db.execute(
        select(Upload).where(Upload.id == upload_id, Upload.hotel_id == hotel_id)
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    upload.status = UploadStatus.pending
    upload.bookings_imported = 0
    upload.bookings_skipped = 0
    upload.error_message = None
    await db.commit()

    task = parse_upload_task.delay(str(upload.id), str(hotel_id))
    upload.celery_task_id = task.id
    await db.commit()

    return upload
