from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "extraneta",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.parse_upload"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
