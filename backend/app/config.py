from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / "backend" / ".env",
        env_prefix="DOUYIN_",
        extra="ignore",
    )

    db_path: Path = BASE_DIR / "data" / "app.db"
    browser_profile_dir: Path = BASE_DIR / "data" / "browser_profile"
    logs_dir: Path = BASE_DIR / "data" / "logs"
    undated_keywords_path: Path = BASE_DIR / "data" / "undated_keywords.txt"

    browser_channel: str = "chrome"
    headless: bool = False
    douyin_url: str = "https://www.douyin.com/"
    following_url: str = "https://www.douyin.com/user/self"
    scrape_limit: int = 700
    scroll_delay_ms: int = 800
    profile_delay_ms: int = 900
    max_profile_pages: int = 100

    def ensure_dirs(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.browser_profile_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
