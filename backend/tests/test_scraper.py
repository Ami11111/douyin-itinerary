import json
from unittest.mock import Mock

from app.config import Settings
from app.scraper import DouyinScraper


def test_parse_following_item_extracts_signature():
    scraper = DouyinScraper(Settings())
    item = {
        "sec_uid": "MS4wLjABAAAAabc123",
        "nickname": "云汐酱",
        "short_id": "1234567890",
        "signature": "7.17-7.20 广州青羽签售区",
        "avatar_thumb": {"url_list": ["https://example.com/a.jpg"]},
    }
    user = scraper._parse_following_item(item)
    assert user is not None
    assert user.douyin_user_id == "MS4wLjABAAAAabc123"
    assert user.bio == "7.17-7.20 广州青羽签售区"
    assert user.avatar_url == "https://example.com/a.jpg"


def test_build_following_url():
    scraper = DouyinScraper(Settings())
    url = scraper._build_following_url("MS4wLjABAAAAabc123", 1784639943)
    assert "sec_user_id=MS4wLjABAAAAabc123" in url
    assert "max_time=1784639943" in url


def test_get_sec_user_id_from_local_storage():
    scraper = DouyinScraper(Settings())
    page = Mock()
    page.evaluate.return_value = json.dumps({"uid": "MS4wLjABAAAAabc123"})
    assert scraper._get_sec_user_id(page) == "MS4wLjABAAAAabc123"


def test_looks_logged_in_uses_cookie():
    scraper = DouyinScraper(Settings())
    page = Mock()
    page.url = "https://www.douyin.com/passport/login/"
    page.context.cookies.return_value = [{"name": "sessionid", "value": "abc123"}]
    assert scraper._looks_logged_in(page) is True
