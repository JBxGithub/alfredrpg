from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "defi_dashboard",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.sync"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "sync-chains-hourly": {
            "task": "app.tasks.sync.sync_chains",
            "schedule": 3600.0,
        },
        "sync-protocols-hourly": {
            "task": "app.tasks.sync.sync_protocols",
            "schedule": 3600.0,
        },
        "sync-yields-hourly": {
            "task": "app.tasks.sync.sync_yields",
            "schedule": 1800.0,
        },
        "sync-tvl-daily": {
            "task": "app.tasks.sync.sync_tvl_history",
            "schedule": 86400.0,
        },
    },
)
