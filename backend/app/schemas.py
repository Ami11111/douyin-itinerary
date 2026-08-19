from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ItineraryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    trip_date: date | None
    is_dated: bool
    location_activity: str
    raw_source_text: str
    status: str
    confidence: float
    created_at: datetime
    updated_at: datetime
    user_nickname: str = ""
    user_douyin_id: str = ""
    user_sec_uid: str = ""
    user_avatar_url: str = ""


class FollowingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    douyin_user_id: str
    nickname: str
    douyin_id: str
    bio: str
    avatar_url: str
    last_seen_at: datetime
    followed_at: datetime
    itinerary_count: int = 0


class JobStatusOut(BaseModel):
    logged_in: bool
    last_success_at: datetime | None = None
    last_run_status: str | None = None
    last_error: str | None = None
    running: bool = False


class MessageOut(BaseModel):
    message: str
