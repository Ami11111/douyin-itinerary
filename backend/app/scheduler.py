from __future__ import annotations

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from .service import refresh_job


logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def _scheduled_refresh() -> None:
    try:
        refresh_job()
    except Exception:
        logger.exception("Scheduled Douyin refresh failed")


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        _scheduled_refresh,
        trigger="interval",
        hours=24,
        id="douyin_refresh",
        next_run_time=datetime.now() + timedelta(hours=24),
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
