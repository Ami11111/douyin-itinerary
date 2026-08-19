# Douyin Itinerary

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![Vue 3](https://img.shields.io/badge/Vue-3-42b883.svg)](https://vuejs.org/)

Turn the bios of the Douyin accounts you follow into a calendar.

Creators on Douyin publish their tour schedule in their profile bio — a dense,
punctuation-free line such as `行程：8.15沈阳/10.3上海/10.7厦门`. This project
reads those bios from a logged-in browser session, extracts `date + place/event`
entries plus undated clues, and shows them as a date table and per-creator cards.
It refreshes every 24 hours, supports manual refresh, and cleans up past entries
into a log.

**[中文文档](README.zh-CN.md)**

---

## Features

- **Bio-to-calendar parsing** for the shorthand Chinese creators actually use:
  ranges (`8.7-8.9`), same-month day lists (`8.16/21/26/28`), Chinese months
  (`8月22-23`), and compact forms (`925成都qy`).
- **Direction-aware naming** — decides per line whether the place comes before or
  after the date, so `沈阳星潮8.15` and `8.15沈阳星潮` both work.
- **Noise rejection** — booth ids, camera models, age ranges and opening hours
  (`E4-29`, `2460f2.8`, `18-28岁`, `晚9-11`) are not mistaken for dates.
- **Two views** — a date-sorted master table and per-creator cards. Keyword,
  date-range and status filters are available on the API.
- **Scheduled + manual refresh**, with the previous successful result preserved
  when a scrape fails.
- **Local first** — everything (database, browser session, logs) stays in `data/`.
  No official API, no reverse-engineered signatures, no third-party service.

## Requirements

- Python 3.10+
- Node.js 18+
- Google Chrome (driven through Playwright)

## Quick start

```bash
git clone https://github.com/Ami11111/douyin-itinerary.git
cd douyin-itinerary
chmod +x start.sh
./start.sh
```

`start.sh` creates the virtualenv, installs backend and frontend dependencies,
copies `backend/.env.example` to `backend/.env`, and starts both servers.

Then open <http://127.0.0.1:5173> and:

1. Click **扫码登录** — a separate Chrome window opens.
2. Scan the QR code / sign in to Douyin in that window.
3. Back in the app, click **手动刷新** and wait for the scrape to finish.
4. From then on the backend scrapes once every 24 hours.

Playwright needs a Chrome build. If the browser fails to launch:

```bash
backend/.venv/bin/python -m playwright install chrome
```

## Configuration

Copy `backend/.env.example` to `backend/.env`. Every setting is read with the
`DOUYIN_` prefix.

| Variable | Default | Description |
| --- | --- | --- |
| `DOUYIN_HEADLESS` | `false` | Run scheduled scrapes headless. `true` hides the browser window but is more likely to trigger a captcha. |
| `DOUYIN_SCRAPE_LIMIT` | `700` | Maximum number of followed accounts to collect. |
| `DOUYIN_SCROLL_DELAY_MS` | `800` | Delay between scrolls while loading the following list. |
| `DOUYIN_PROFILE_DELAY_MS` | `900` | Delay between opening creator profiles to fill in missing bios. |
| `DOUYIN_MAX_PROFILE_PAGES` | `100` | How many bio-less profiles to open per run. |
| `DOUYIN_BROWSER_CHANNEL` | `chrome` | Playwright browser channel. |
| `DOUYIN_DB_PATH` | `../data/app.db` | SQLite database location. |

`data/undated_keywords.txt` holds the trigger words for undated clues — one per
line, `#` for comments. Changes take effect on the next refresh.

## How parsing works

### Dates

Every convention, venue and IP name in the examples below is invented — the
rules were developed against real bios, but nothing quoted here names a real
event or account.

Supported spellings:

- Single dates — `8.9`, `8/9`, `8-9`, `8月9日`, `8月9号`, `2026.8.9`, `10. 3`
- Ranges — `8.7-8.9`, `10.24-25`, `8月22-23`, `7.31～8.2`, `8.22—8.23日`
- Same-month day lists — `9.5 6 12 13`, `8.16/21/26/28`, `4.17.18.19`,
  `9.18、19、20`, `10.24／25`, `8月7-8、10-12，14-16`
- Compact dates glued to the place — `925成都qy` (only enabled when the same
  bio uses the style at least twice)

**Year inference.** When no year is written, the parser picks the year (last,
current, or next) that puts the date closest to today, with a small penalty on
past distances so that ties resolve to the future. Bios routinely keep a log of
finished events — seeing `5.1 无锡云图车展` in August means *this* May, not next
May. Dates already in the past are not written to the database, so a refresh no
longer creates rows only to delete them again.

Ranges longer than 31 days keep only their start date, so a long residency does
not flood the calendar. Entries are treated as one-off events and never repeat.

### Names

- The bio is split on line breaks and `｜；。！？`, and each segment decides
  independently whether the date comes first: a segment that *ends* on a date and
  does not *start* with a `行程：`-style label is read as `place + date`,
  otherwise as `date + place`.
- Decorative emoji (`🎀✨🌟🩵` …) are separators only, never part of a name.
- Text is cut at contact markers such as `阵容`, `商务`, `私信`, `@someone` — but
  a segment that *is* just `@someone` keeps that handle as the name.
- Unbalanced brackets (`（延期`, `深圳砚山展】`) are repaired, and entries left
  with nothing but a status word (`延期`, `取消`) are dropped.

### Undated clues

A short line only becomes a pending clue when it contains an event word *and* a
place word *and* no contact-info noise — for example `线下行程：上海ac全勤`. This
keeps self-descriptions out of the itinerary list.

## API

The backend serves a small JSON API under `/api` (interactive docs at
<http://127.0.0.1:8000/docs>).

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness check. |
| `GET` | `/api/douyin/status` | Login state, last run status and error. |
| `POST` | `/api/douyin/login` | Open the Chrome window for QR sign-in. |
| `POST` | `/api/refresh` | Trigger a scrape (202; runs in the background). |
| `GET` | `/api/itineraries` | List entries; filters: `date_from`, `date_to`, `status`, `keyword`, `user_id`. |
| `GET` | `/api/following` | List followed creators with entry counts. |
| `DELETE` | `/api/itineraries/{id}` | Delete one entry (logged in `cleanup_log`). |

## Project layout

```text
backend/               FastAPI + SQLite + APScheduler + Playwright
  app/parser.py        bio → itinerary parsing rules
  app/scraper.py       Playwright scraping and DOM selectors
  app/service.py       persistence, refresh job, expiry cleanup
  tests/               pytest suite
frontend/              Vue 3 + Vite + Element Plus + Pinia
data/                  SQLite database, browser session, logs, parser config
start.sh               install dependencies and start both servers
```

## Development

```bash
# backend
cd backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
.venv/bin/python -m pytest

# frontend
cd frontend
npm run dev
```

The parser is pure and side-effect free — `ItineraryParser().parse(bio, today=...)`
takes a string and returns `ParsedTrip` objects, so new rules can be developed
against `backend/tests/test_parser.py` without running a scrape.

## Troubleshooting

A failed scrape never overwrites the last successful result; the frontend shows
the most recent error and **手动刷新** retries.

| Symptom | Fix |
| --- | --- |
| Login expired | Click **扫码登录** and sign in again. |
| Captcha appears | Complete it in the opened browser, then refresh. |
| Nothing is collected | Douyin changed its markup — update the DOM selectors in `backend/app/scraper.py`. |
| Browser fails to start | Run `python -m playwright install chrome` inside `backend/.venv`. |

## Contributing

Issues and pull requests are welcome. Parsing bugs are the most useful kind of
report: paste the bio text, the entry you got, and the entry you expected.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow.

## License

[MIT](LICENSE) © Ami

## Disclaimer

This project only reads content that is already visible in a browser you are
signed into yourself. It uses no official API, no reverse-engineered request
signing and no paid third-party service. It is meant for personal use — keeping
track of creators you already follow — and its behaviour depends on Douyin's web
markup, which changes without notice and may trigger rate limiting. Please
respect Douyin's terms of service, do not use it for commercial purposes or
high-frequency scraping, and do not redistribute the personal data it collects.
