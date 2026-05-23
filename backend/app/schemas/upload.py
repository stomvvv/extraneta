from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.booking import OTASource
from app.models.upload import UploadStatus, DocumentType


class UploadOut(BaseModel):
    id: UUID
    hotel_id: UUID
    original_filename: str
    file_size_bytes: int
    source_ota: OTASource
    document_type: DocumentType
    status: UploadStatus
    bookings_imported: int
    bookings_skipped: int
    error_message: Optional[str]
    report_period_start: Optional[datetime]
    report_period_end: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadPreview(BaseModel):
    filename: str
    detected_ota: Optional[str]
    row_count: int
    columns: list[str]
    sample_rows: list[dict]
    warnings: list[str]
