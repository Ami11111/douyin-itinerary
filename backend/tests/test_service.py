from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import service
from app.database import Base
from app.models import CleanupLog, FollowedUser, Itinerary
from app.parser import ItineraryParser
from app.scraper import ScrapedUser


@pytest.fixture()
def test_session(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(service, "SessionLocal", session_factory)
    return session_factory


def test_upsert_users_and_trips(test_session):
    parser = ItineraryParser()
    user = ScrapedUser(
        douyin_user_id="abc123",
        nickname="旅行博主",
        douyin_id="travel",
        bio="8.29 长沙星屿海洋乐园，去武汉签售",
        avatar_url="https://example.com/a.png",
    )
    stats = service._upsert_users_and_trips(
        test_session(),
        [user],
        parser,
        date(2026, 8, 18),
    )
    assert stats["followed_users"] == 1
    assert stats["dated_itineraries"] == 1
    assert stats["pending_clues"] >= 1

    session = test_session()
    saved_user = session.scalars(select(FollowedUser)).one()
    assert saved_user.nickname == "旅行博主"
    assert len(session.scalars(select(Itinerary)).all()) == 2


def test_upsert_skips_already_expired_trips(test_session):
    user = ScrapedUser(
        douyin_user_id="abc123",
        nickname="旅行博主",
        douyin_id="travel",
        bio="8.1 上海回顾场 8.29 长沙星屿海洋乐园",
        avatar_url="",
    )
    stats = service._upsert_users_and_trips(
        test_session(),
        [user],
        ItineraryParser(),
        date(2026, 8, 18),
    )
    assert stats["dated_itineraries"] == 1
    saved = test_session().scalars(select(Itinerary)).all()
    assert [item.trip_date for item in saved] == [date(2026, 8, 29)]


def test_cleanup_expired(test_session):
    session = test_session()
    user = FollowedUser(douyin_user_id="abc123", nickname="旅行博主")
    session.add(user)
    session.flush()
    session.add(
        Itinerary(
            user_id=user.id,
            trip_date=date(2026, 8, 1),
            is_dated=True,
            location_activity="已过期活动",
            raw_source_text="8.1 已过期活动",
            status="upcoming",
        )
    )
    session.commit()

    deleted = service._cleanup_expired(test_session(), date(2026, 8, 18))
    assert deleted == 1
    assert len(test_session().scalars(select(Itinerary)).all()) == 0
    assert len(test_session().scalars(select(CleanupLog)).all()) == 1
