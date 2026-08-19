from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from playwright.sync_api import BrowserContext, Page, sync_playwright

from .config import Settings


@dataclass
class ScrapedUser:
    douyin_user_id: str
    nickname: str
    douyin_id: str
    bio: str
    avatar_url: str


class ScraperError(RuntimeError):
    """Raised when Douyin data cannot be collected."""


FETCH_TEXT_JS = r"""
async (url) => {
  const response = await fetch(url, {
    credentials: 'include',
    headers: {'Accept': 'application/json, text/plain, */*'}
  });
  return await response.text();
}
"""


class DouyinScraper:
    def __init__(self, settings: Settings):
        self.settings = settings

    def check_login(self) -> bool:
        with sync_playwright() as playwright:
            context = self._launch_context(playwright, headless=True)
            try:
                page = context.new_page()
                page.goto(self.settings.douyin_url, wait_until="domcontentloaded", timeout=30_000)
                page.wait_for_timeout(1_500)
                return self._looks_logged_in(page)
            finally:
                context.close()

    def open_login_window(self, timeout_seconds: int = 180) -> bool:
        with sync_playwright() as playwright:
            context = self._launch_context(playwright, headless=False)
            try:
                page = context.new_page()
                page.goto(self.settings.following_url, wait_until="domcontentloaded", timeout=45_000)
                deadline = time.time() + timeout_seconds
                while time.time() < deadline:
                    if self._looks_logged_in(page):
                        page.wait_for_timeout(1_200)
                        return True
                    page.wait_for_timeout(2_000)
                return False
            finally:
                context.close()

    def scrape_following(self) -> list[ScrapedUser]:
        with sync_playwright() as playwright:
            context = self._launch_context(playwright, headless=self.settings.headless)
            try:
                page = context.new_page()
                page.goto(self.settings.following_url, wait_until="domcontentloaded", timeout=45_000)
                page.wait_for_timeout(2_500)
                if not self._looks_logged_in(page):
                    raise ScraperError("抖音未登录，请先扫码登录")

                sec_user_id = self._get_sec_user_id(page)
                users = self._fetch_following_api(page, sec_user_id)
                if not users:
                    raise ScraperError("未能读取到关注列表，可能账号没有关注用户或接口已变化")
                return users
            finally:
                context.close()

    def _launch_context(self, playwright: Any, headless: bool) -> BrowserContext:
        self.settings.ensure_dirs()
        return playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.settings.browser_profile_dir),
            channel=self.settings.browser_channel,
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

    def _looks_logged_in(self, page: Page) -> bool:
        try:
            cookies = page.context.cookies()
            cookie_names = {cookie.get("name", "") for cookie in cookies}
            return bool({"sessionid", "sessionid_ss"} & cookie_names)
        except Exception:
            return False

    def _get_sec_user_id(self, page: Page) -> str:
        try:
            raw = page.evaluate("() => localStorage.getItem('user_info')")
            if raw:
                user_info = json.loads(raw)
                sec_user_id = user_info.get("uid") or user_info.get("sec_uid")
                if sec_user_id:
                    return str(sec_user_id)
        except Exception:
            pass

        try:
            html = page.content()
            match = re.search(r"secUid[^0-9A-Za-z_-]*([A-Za-z0-9_-]{20,})", html)
            if match:
                return match.group(1)
            match = re.search(r"sec_uid=([A-Za-z0-9_-]{20,})", html)
            if match:
                return match.group(1)
        except Exception:
            pass

        raise ScraperError("无法获取当前抖音账号标识，请重新登录后再试")

    def _fetch_following_api(self, page: Page, sec_user_id: str) -> list[ScrapedUser]:
        users: dict[str, ScrapedUser] = {}
        max_time = 0
        previous_min_time: int | None = None

        while len(users) < self.settings.scrape_limit:
            url = self._build_following_url(sec_user_id, max_time)
            try:
                text = page.evaluate(FETCH_TEXT_JS, url)
                data = json.loads(text)
            except Exception as exc:
                raise ScraperError(f"关注列表接口请求失败: {exc}") from exc

            if data.get("status_code") not in (0, None):
                raise ScraperError(f"关注列表接口返回异常: {data.get('status_msg') or data.get('status_code')}")

            followings = data.get("followings") or []
            for item in followings:
                user = self._parse_following_item(item)
                if user and user.douyin_user_id not in users:
                    users[user.douyin_user_id] = user

            if not data.get("has_more"):
                break

            min_time = data.get("min_time")
            if not min_time or min_time == previous_min_time:
                break
            previous_min_time = min_time
            max_time = int(min_time)
            page.wait_for_timeout(self.settings.profile_delay_ms)

        return list(users.values())

    def _build_following_url(self, sec_user_id: str, max_time: int) -> str:
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "pc_client_type": "1",
            "pc_libra_divert": "Mac",
            "version_code": "170400",
            "version_name": "17.4.0",
            "cookie_enabled": "true",
            "screen_width": "1280",
            "screen_height": "900",
            "browser_language": "zh-CN",
            "browser_platform": "MacIntel",
            "browser_name": "Chrome",
            "browser_version": "151.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "151.0.0.0",
            "os_name": "Mac OS",
            "os_version": "10.15.7",
            "cpu_core_num": "10",
            "device_memory": "16",
            "platform": "PC",
            "downlink": "1.65",
            "effective_type": "4g",
            "round_trip_time": "200",
            "sec_user_id": sec_user_id,
            "count": "20",
            "max_time": str(max_time),
            "source_type": "1",
            "address_book_access": "1",
            "gps_access": "1",
        }
        return "https://www.douyin.com/aweme/v1/web/user/following/list/?" + urlencode(params)

    @staticmethod
    def _parse_following_item(item: dict[str, Any]) -> ScrapedUser | None:
        sec_uid = item.get("sec_uid") or item.get("uid") or item.get("reflow_page_uid")
        if not sec_uid:
            return None
        avatar_url = ""
        for key in ("avatar_thumb", "avatar_medium", "avatar_300x300", "avatar_larger"):
            avatar_obj = item.get(key) or {}
            url_list = avatar_obj.get("url_list") or []
            if url_list:
                avatar_url = url_list[0]
                break
        return ScrapedUser(
            douyin_user_id=str(sec_uid),
            nickname=str(item.get("nickname") or ""),
            douyin_id=str(item.get("short_id") or item.get("unique_id") or ""),
            bio=str(item.get("signature") or ""),
            avatar_url=avatar_url,
        )
