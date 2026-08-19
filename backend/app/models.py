from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now()


class FollowedUser(Base):
    __tablename__ = "followed_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    douyin_user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(255), default="")
    douyin_id: Mapped[str] = mapped_column(String(128), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    avatar_url: Mapped[str] = mapped_column(Text, default="")
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    followed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    itineraries: Mapped[list["Itinerary"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Itinerary(Base):
    __tablename__ = "itinerary"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("followed_user.id"), index=True)
    trip_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    is_dated: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    location_activity: Mapped[str] = mapped_column(Text, default="")
    raw_source_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="upcoming", index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user: Mapped[FollowedUser] = relationship(back_populates="itineraries")


class JobRun(Base):
    __tablename__ = "job_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str] = mapped_column(String(64), default="refresh", index=True)
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class CleanupLog(Base):
    __tablename__ = "cleanup_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    itinerary_snapshot_json: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    reason: Mapped[str] = mapped_column(String(64), default="expired")
