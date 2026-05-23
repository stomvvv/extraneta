import asyncio
import uuid
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app
from app.core.config import settings


@celery_app.task(bind=True, name="parse_upload", max_retries=3)
def parse_upload_task(self, upload_id: str, hotel_id: str):
    """
    Celery task: download file from storage, parse it, persist bookings.
    Runs synchronously via asyncio.run() since Celery workers are sync.
    """
    try:
        asyncio.run(_parse_upload_async(upload_id, hotel_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


async def _parse_upload_async(upload_id: str, hotel_id: str):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select
    from app.models.upload import Upload, UploadStatus
    from app.models.booking import Booking
    from app.models.hotel import Hotel
    from app.services.parsers import get_parser
    from app.services.anomaly import AnomalyDetector
    from app.core.storage import get_s3_client
    import io

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        # Fetch upload record
        result = await db.execute(select(Upload).where(Upload.id == uuid.UUID(upload_id)))
        upload = result.scalar_one_or_none()
        if not upload:
            return

        # Fetch hotel for expected commission rates
        hotel_result = await db.execute(select(Hotel).where(Hotel.id == uuid.UUID(hotel_id)))
        hotel = hotel_result.scalar_one_or_none()

        # Mark as processing
        upload.status = UploadStatus.processing
        await db.commit()

        try:
            # Download file from storage
            s3 = get_s3_client()
            response = s3.get_object(Bucket=settings.MINIO_BUCKET, Key=upload.storage_key)
            file_bytes = response["Body"].read()

            # Parse
            parser = get_parser(upload.source_ota)
            parse_result = parser.parse(file_bytes, upload.original_filename)

            if parse_result.errors:
                upload.status = UploadStatus.failed
                upload.error_message = "; ".join(parse_result.errors)
                await db.commit()
                return

            # Check expected commission rates from hotel settings
            expected_rates = hotel.expected_commission_rates if hotel else {}

            imported = 0
            skipped = parse_result.skipped

            for pb in parse_result.bookings:
                # Dedup by hotel + source_ota + booking_id_ota
                existing = await db.execute(
                    select(Booking).where(
                        Booking.hotel_id == uuid.UUID(hotel_id),
                        Booking.source_ota == pb.source_ota,
                        Booking.booking_id_ota == pb.booking_id_ota,
                    )
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                booking = Booking(
                    hotel_id=uuid.UUID(hotel_id),
                    upload_id=upload.id,
                    source_ota=pb.source_ota,
                    booking_id_ota=pb.booking_id_ota,
                    guest_name=pb.guest_name,
                    room_type=pb.room_type,
                    booking_date=pb.booking_date,
                    check_in=pb.check_in,
                    check_out=pb.check_out,
                    nights=pb.nights,
                    gross_amount=pb.gross_amount,
                    ota_commission_rate=pb.ota_commission_rate,
                    ota_commission_amount=pb.ota_commission_amount,
                    net_amount=pb.net_amount,
                    currency=pb.currency,
                    payment_status=pb.payment_status,
                    booking_status=pb.booking_status,
                    has_vat=pb.has_vat,
                )
                db.add(booking)
                await db.flush()

                # Run anomaly detection inline
                anomaly_reasons = AnomalyDetector.check(booking, expected_rates)
                if anomaly_reasons:
                    booking.is_anomaly = True
                    booking.anomaly_reasons = "; ".join(anomaly_reasons)

                imported += 1

            upload.status = UploadStatus.completed
            upload.bookings_imported = imported
            upload.bookings_skipped = skipped
            await db.commit()

        except Exception as e:
            await db.rollback()
            upload.status = UploadStatus.failed
            upload.error_message = str(e)
            await db.commit()
            raise

    await engine.dispose()
