from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import Settings
from app.db import SessionLocal
from app.services.sync_service import SyncService


scheduler = BackgroundScheduler()


def start_scheduler(settings: Settings) -> None:
    if not settings.sync_enabled or scheduler.running:
        return

    scheduler.add_job(
        sync_job,
        trigger=CronTrigger(
            hour=settings.sync_hour,
            minute=settings.sync_minute,
            timezone=settings.sync_timezone,
        ),
        args=[settings],
        id="daily-club-sync",
        replace_existing=True,
    )
    scheduler.start()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


def sync_job(settings: Settings) -> None:
    db = SessionLocal()
    try:
        service = SyncService(db, settings)
        import asyncio

        asyncio.run(
            service.run_sync(
                requested_by=settings.default_requested_by,
                trigger_type="scheduled",
                source_type="uma_moe",
            )
        )
    finally:
        db.close()
