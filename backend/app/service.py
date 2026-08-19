from __future__ import annotations

import json
import threading
import time
from datetime import date, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal
from .models import CleanupLog, FollowedUser, Itinerary, JobRun
from .parser import ItineraryParser
from .scraper import DouyinScraper, ScrapedUser


REFRESH_LOCK = threading.Lock()
_login_cache: dict[str, Any] = {"value": False, "at": 0.0}


def is_refresh_running() -> bool:
    return REFRESH_LOCK.locked()


def get_douyin_status() -> dict[str, Any]:
    db = SessionLocal()
    try:
        last_success = db.scalars(
            select(JobRun)
            .where(JobRun.job_type == "refresh", JobRun.status == "success")
            .order_by(JobRun.started_at.desc())
            .limit(1)
        ).first()
        last_run = db.scalars(
            select(JobRun)
            .where(JobRun.job_type == "refresh")
            .order_by(JobRun.started_at.desc())
            .limit(1)
        ).first()
        if REFRESH_LOCK.locked():
            logged_in = True
        elif last_run is None:
            logged_in = False
        elif last_run.status == "success":
            logged_in = True
        else:
            logged_in = bool(last_success)
        return {
            "logged_in": logged_in,
            "last_success_at": last_success.finished_at if last_success else None,
            "last_run_status": last_run.status if last_run else None,
            "last_error": last_run.error_message if last_run else None,
            "running": REFRESH_LOCK.locked(),
        }
    finally:
        db.close()


def open_login_window(timeout_seconds: int = 180) -> bool:
    return DouyinScraper(settings).open_login_window(timeout_seconds)


def refresh_job() -> dict[str, Any]:
    if not REFRESH_LOCK.acquire(blocking=False):
        return {"status": "already_running", "job_id": None}

    db = SessionLocal()
    job = JobRun(job_type="refresh", status="running")
    db.add(job)
    db.commit()
    job_id = job.id
    try:
        scraper = DouyinScraper(settings)
        users = scraper.scrape_following()
        parser = ItineraryParser(settings.undated_keywords_path)
        today = date.today()
        stats = _upsert_users_and_trips(db, users, parser, today)
        _cleanup_expired(db, today)

        job.status = "success"
        job.finished_at = datetime.now()
        job.stats_json = json.dumps(stats, ensure_ascii=False)
        db.commit()
        _login_cache["value"] = True
        _login_cache["at"] = time.time()
        return {"status": "success", "job_id": job_id, "stats": stats}
    except Exception as exc:
        db.rollback()
        job = db.get(JobRun, job_id)
        if job:
            job.status = "failed"
            job.finished_at = datetime.now()
            job.error_message = str(exc)
            db.commit()
        raise
    finally:
        db.close()
        REFRESH_LOCK.release()


def _upsert_users_and_trips(
    db: Session,
    users: list[ScrapedUser],
    parser: ItineraryParser,
    today: date,
) -> dict[str, int]:
    seen_ids = {user.douyin_user_id for user in users}
    existing_users = db.scalars(select(FollowedUser)).all()
    existing_by_douyin_id = {user.douyin_user_id: user for user in existing_users}

    total_users = 0
    total_dated = 0
    total_pending = 0

    for scraped in users:
        user = existing_by_douyin_id.get(scraped.douyin_user_id)
        if user is None:
            user = FollowedUser(douyin_user_id=scraped.douyin_user_id)
            db.add(user)
        user.nickname = scraped.nickname
        user.douyin_id = scraped.douyin_id
        user.bio = scraped.bio
        user.avatar_url = scraped.avatar_url
        user.last_seen_at = datetime.now()
        if user.followed_at is None:
            user.followed_at = datetime.now()
        db.flush()

        db.execute(delete(Itinerary).where(Itinerary.user_id == user.id))
        parsed_trips = parser.parse(scraped.bio, today=today)
        for trip in parsed_trips:
            # Bios keep a log of past events. Storing them would only feed the
            # expiry cleanup a fresh copy to delete on every single refresh.
            if trip.is_dated and trip.trip_date and trip.trip_date < today:
                continue
            itinerary = Itinerary(
                user_id=user.id,
                trip_date=trip.trip_date,
                is_dated=trip.is_dated,
                location_activity=trip.location_activity,
                raw_source_text=trip.raw_source_text,
                status="upcoming" if trip.is_dated else "pending",
                confidence=trip.confidence,
            )
            db.add(itinerary)
            if trip.is_dated:
                total_dated += 1
            else:
                total_pending += 1
        total_users += 1

    # Only prune unfollowed accounts when the scrape appears complete.
    if len(users) < settings.scrape_limit:
        for user in existing_users:
            if user.douyin_user_id not in seen_ids:
                db.delete(user)

    db.commit()
    return {
        "followed_users": total_users,
        "dated_itineraries": total_dated,
        "pending_clues": total_pending,
    }


def _cleanup_expired(db: Session, today: date) -> int:
    expired = db.scalars(
        select(Itinerary).where(Itinerary.is_dated.is_(True), Itinerary.trip_date < today)
    ).all()
    deleted = 0
    for itinerary in expired:
        user = db.get(FollowedUser, itinerary.user_id)
        snapshot = {
            "id": itinerary.id,
            "user_id": itinerary.user_id,
            "user_nickname": user.nickname if user else "",
            "trip_date": itinerary.trip_date.isoformat() if itinerary.trip_date else None,
            "location_activity": itinerary.location_activity,
            "raw_source_text": itinerary.raw_source_text,
            "status": itinerary.status,
        }
        db.add(
            CleanupLog(
                itinerary_snapshot_json=json.dumps(snapshot, ensure_ascii=False),
                reason="expired",
            )
        )
        db.delete(itinerary)
        deleted += 1
    db.commit()
    return deleted


def list_itineraries(
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    keyword: str | None = None,
    user_id: int | None = None,
) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        stmt = select(Itinerary, FollowedUser).join(FollowedUser)
        if date_from:
            stmt = stmt.where(Itinerary.trip_date >= date_from)
        if date_to:
            stmt = stmt.where(Itinerary.trip_date <= date_to)
        if status:
            stmt = stmt.where(Itinerary.status == status)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                Itinerary.location_activity.like(like)
                | FollowedUser.nickname.like(like)
                | FollowedUser.douyin_id.like(like)
            )
        if user_id:
            stmt = stmt.where(Itinerary.user_id == user_id)
        stmt = stmt.order_by(Itinerary.trip_date.asc().nullslast(), Itinerary.created_at.desc())
        rows = db.execute(stmt).all()
        result = []
        for itinerary, user in rows:
            item = {
                "id": itinerary.id,
                "user_id": itinerary.user_id,
                "trip_date": itinerary.trip_date,
                "is_dated": itinerary.is_dated,
                "location_activity": itinerary.location_activity,
                "raw_source_text": itinerary.raw_source_text,
                "status": itinerary.status,
                "confidence": itinerary.confidence,
                "created_at": itinerary.created_at,
                "updated_at": itinerary.updated_at,
                "user_nickname": user.nickname,
                "user_douyin_id": user.douyin_id,
                "user_sec_uid": user.douyin_user_id,
                "user_avatar_url": user.avatar_url,
            }
            result.append(item)
        return result
    finally:
        db.close()


def list_following() -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        users = db.scalars(select(FollowedUser).order_by(FollowedUser.last_seen_at.desc())).all()
        counts = dict(
            db.execute(
                select(Itinerary.user_id, func.count(Itinerary.id))
                .group_by(Itinerary.user_id)
            ).all()
        )
        result = []
        for user in users:
            result.append(
                {
                    "id": user.id,
                    "douyin_user_id": user.douyin_user_id,
                    "nickname": user.nickname,
                    "douyin_id": user.douyin_id,
                    "bio": user.bio,
                    "avatar_url": user.avatar_url,
                    "last_seen_at": user.last_seen_at,
                    "followed_at": user.followed_at,
                    "itinerary_count": counts.get(user.id, 0),
                }
            )
        return result
    finally:
        db.close()


def delete_itinerary(itinerary_id: int) -> bool:
    db = SessionLocal()
    try:
        itinerary = db.get(Itinerary, itinerary_id)
        if not itinerary:
            return False
        user = db.get(FollowedUser, itinerary.user_id)
        snapshot = {
            "id": itinerary.id,
            "user_id": itinerary.user_id,
            "user_nickname": user.nickname if user else "",
            "trip_date": itinerary.trip_date.isoformat() if itinerary.trip_date else None,
            "location_activity": itinerary.location_activity,
            "raw_source_text": itinerary.raw_source_text,
            "status": itinerary.status,
        }
        db.add(
            CleanupLog(
                itinerary_snapshot_json=json.dumps(snapshot, ensure_ascii=False),
                reason="manual",
            )
        )
        db.delete(itinerary)
        db.commit()
        return True
    finally:
        db.close()
