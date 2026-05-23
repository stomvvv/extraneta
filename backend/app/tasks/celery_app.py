import os
from celery import Celery

# Railway provides Redis URL as REDIS_URL. Fall back to local Docker service name.
_redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
if not _redis_url.startswith("redis"):
    raise RuntimeError(
        f"REDIS_URL must be a Redis URL (got: {_redis_url!r}). "
        "Set REDIS_URL to your Redis connection string on Railway."
    )

celery_app = Celery(
    "extraneta",
    broker=_redis_url,
    backend=_redis_url,
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
