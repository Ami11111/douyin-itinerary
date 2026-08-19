from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


MONTH = r"(?:1[0-2]|0?[1-9])"
DAY = r"(?:3[01]|[12]\d|0?[1-9])"
# Separators that may sit between a month and a day. Padding spaces are only
# tolerated around a dot ("10. 3"); "AB04 / 10.5" is a booth id, not a date.
MD_SEP = r"(?:\s*[.．]\s*|[-/－／])"
# Separators that may sit between the two ends of a range.
RANGE_SEP = r"[-–—－~～至到]"
DAY_SUFFIX = r"(?:[日号](?!本))?"

FULL_DATE_RE = re.compile(
    r"(?P<year>20\d{2})\s*(?:年|[-/.])\s*"
    rf"(?P<month>{MONTH})\s*(?:月|[-/.])\s*"
    rf"(?P<day>{DAY}){DAY_SUFFIX}"
)
CN_DATE_RE = re.compile(rf"(?P<month>{MONTH})\s*月\s*(?P<day>{DAY}){DAY_SUFFIX}")
NUM_DATE_RE = re.compile(
    rf"(?P<month>{MONTH}){MD_SEP}(?P<day>{DAY})(?![0-9]){DAY_SUFFIX}"
)
RANGE_MD_MD_RE = re.compile(
    rf"(?P<m1>{MONTH}){MD_SEP}(?P<d1>{DAY}){DAY_SUFFIX}\s*{RANGE_SEP}\s*"
    rf"(?P<m2>{MONTH}){MD_SEP}(?P<d2>{DAY}){DAY_SUFFIX}(?![0-9])"
)
RANGE_MD_D_RE = re.compile(
    rf"(?P<m>{MONTH}){MD_SEP}(?P<d1>{DAY}){DAY_SUFFIX}\s*{RANGE_SEP}\s*"
    rf"(?P<d2>{DAY}){DAY_SUFFIX}(?![0-9])"
)
RANGE_CN_RE = re.compile(
    rf"(?P<m1>{MONTH})\s*月\s*(?P<d1>{DAY}){DAY_SUFFIX}\s*{RANGE_SEP}\s*"
    rf"(?:(?P<m2>{MONTH})\s*月\s*)?(?P<d2>{DAY}){DAY_SUFFIX}(?![0-9])"
)
# "925成都qy" / "1003上海星潮": a compact date glued to the location.
COMPACT_DATE_RE = re.compile(r"(?P<digits>\d{3,4})(?![\d.．:：])")

# Separators allowed between the items of a day enumeration ("8.16/21/26").
ENUM_SEP_RE = re.compile(r"[\s.．、,，/／&＆和]+")
ENUM_ITEM_RE = re.compile(
    rf"(?P<d1>{DAY})[日]?(?:\s*{RANGE_SEP}\s*(?P<d2>{DAY})[日]?)?"
)
ENUM_UNIT_RE = re.compile(r"[点时分楼层号馆厅室区排座人个位元岁月年周天级届w万k]")

# Two dates separated by nothing but whitespace belong to the same entry only
# when they are near each other in time.
MAX_GROUP_GAP_DAYS = 45

# Ranges longer than this are almost always a long running gig (or a typo);
# expanding them would flood the calendar, so only the start day is kept.
MAX_RANGE_DAYS = 31

SEGMENT_SPLIT_RE = re.compile(r"[\n\r｜|;；。！!？?║⏎]")
LINE_SPLIT_RE = re.compile(r"[\n\r，。！？；、｜|]+")
IGNORABLE_GAP_RE = re.compile(r"[\s，,；;、:：&＆和/／]*")

# Decorative characters bloggers sprinkle between entries. They are never part
# of a place name, so they are trimmed rather than treated as content.
DECOR_RE = re.compile(
    "[\U0001F000-\U0001FAFF"
    "←-⇿⌀-⏿①-⓿─-◿☀-➿"
    "⬀-⯿〰〽㊗㊙‼⁉©®™"
    "︀-️‍⃣]+"
)
DECOR_TAIL_RE = re.compile(DECOR_RE.pattern + "$")

# Textual markers that mean "the itinerary ended, contact info follows".
LOCATION_STOP_RE = re.compile(
    r"@|"
    r"阵容|粉丝群|无外网|没有外网|不授权|盗图|举报|商务|企鹅|群号|微bo|备注来意|"
    r"恋人|老婆|老公|谢谢|感谢|私信|搬运|全平台|主推|禁止|二创|勿扰|"
    r"玩耍|高p|妆造|记忆力|珍惜|有需要|希望大家|支持一下|欢迎|请不要|喜欢的"
)
_STRIP_CHARS = " \t\r\n,，.。!！?？;；:：、|｜/\\·-—_~*\"'“”‘’＋+=＝"

SCHEDULE_LABEL_RE = re.compile(
    r"^(?:近日|近期|后续|最近|以下|如下|接下来|预计|大概|部分|全部|"
    r"线下|线上|活动|漫展|签售|嘉宾|展会|拍摄|商演|休息日|工作|"
    r"行程|安排|时间|地点|档期|排期|公告|计划|日程|行踪|通知|更新)+$"
)
SCHEDULE_HINT_MARKERS = (
    "近日行程",
    "近期行程",
    "线下行程",
    "活动行程",
    "漫展行程",
    "签售行程",
    "拍摄行程",
    "嘉宾行程",
    "展会行程",
    "行程安排",
    "行程",
    "排期",
    "档期",
    "日程",
    "安排",
)
TRAILING_LABEL_RE = re.compile(r"(?:定档|开票|开始|时间|日期|如下|安排)$")
# "（延期8.19）" leaves the status word behind; it is not a place.
STATUS_ONLY_RE = re.compile(r"^(?:延期|取消|改期|待定|暂定|未定|已满|结束|新增|补充|部分)+$")
LEADING_LABEL_RE = re.compile(
    r"^(?:近日|近期|后续|最近|线下|线上|活动|漫展|行程|安排|时间|地点|档期|"
    r"排期|公告|计划|日程|行踪|嘉宾|签售|拍摄|展会|部分|以下|如下)+\s*[:：]?\s*"
)

# Numbers that look like a date but are something else entirely.
TIME_PREFIX_RE = re.compile(r"(?:晚上|早上|上午|下午|中午|凌晨|半夜|晚|早|点|时)$")
UNIT_SUFFIX_RE = re.compile(
    r"^\s*(?:小时|分钟|周年|个月|岁|kg|KG|cm|CM|km|w粉|万粉|w赞|元钱|块钱|"
    r"人民币|平米|℃|%|点|时)"
)

BRACKET_PAIRS = {
    "(": ")",
    "（": "）",
    "[": "]",
    "【": "】",
    "《": "》",
    "〔": "〕",
    "「": "」",
    "『": "』",
    "〈": "〉",
}
CLOSERS = {value: key for key, value in BRACKET_PAIRS.items()}
WORD_RE = re.compile(r"[0-9A-Za-z一-鿿぀-ヿ]")

# Undated clues only survive when they read like an event, not like a bio line.
UNDATED_EVENT_RE = re.compile(
    r"漫展|展会|车展|签售|摄影会|演出|巡演|音乐节|嘉年华|快闪|见面会|见面|"
    r"live|only|路演|一日店长|见面签|活动|线下|巡回|见粉|团建"
)
UNDATED_NOISE_RE = re.compile(
    r"[🈴🈺📮🐧🛰️@？?吗呢吧]|\d{4,}|/.*/|私|备注|联系|合作|商务|星图|微信|"
    r"主页|关注|直播|评论|拉踩|举报|搬运|外网|粉丝群|勿扰|转载|"
    r"接|谢谢|感谢|禁止|希望|我|你|各种|一些|可以|均可|限号|查无"
)
# A clue is only worth keeping when it says *where*: a bare "偶尔接接商演活动"
# is a self-description, "上海ac全勤" is an itinerary without a date.
UNDATED_PLACE_RE = re.compile(
    r"上海|北京|广州|深圳|成都|杭州|南京|武汉|天津|重庆|西安|苏州|无锡|长沙|"
    r"合肥|沈阳|青岛|厦门|郑州|济南|福州|南昌|昆明|贵阳|南宁|石家庄|太原|"
    r"长春|哈尔滨|大连|宁波|温州|常州|徐州|东莞|佛山|珠海|汕头|保定|洛阳|"
    r"芜湖|镇江|嘉兴|金华|泉州|海口|三亚|兰州|银川|呼和浩特|乌鲁木齐|绍兴|"
    r"扬州|南通|盐城|柳州|桂林|唐山|潍坊|烟台|临沂|株洲|衡阳|赣州|九江|"
    r"香港|澳门|台北|东京|大阪|首尔|新加坡|日本|韩国|美国|加拿大|"
    r"(?:1[0-2]|[1-9])月(?![0-9])"
)


@dataclass
class DateToken:
    dates: list[date]
    start: int
    end: int
    year_given: bool = False
    confidence: float | None = None
    sep_class: str = ""


@dataclass
class ParsedTrip:
    trip_date: date | None
    is_dated: bool
    location_activity: str
    raw_source_text: str
    confidence: float = 1.0


@dataclass
class _Segment:
    start: int
    end: int
    tokens: list[DateToken]


class ItineraryParser:
    def __init__(self, keywords_path: Path | None = None):
        self.keywords_path = keywords_path
        self.keywords = self._load_keywords(keywords_path)

    def _load_keywords(self, path: Path | None) -> list[str]:
        defaults = [
            "在",
            "去",
            "打卡",
            "见面",
            "见面会",
            "签售",
            "巡演",
            "演出",
            "live",
            "音乐节",
            "展览",
            "活动",
            "线下",
        ]
        if not path or not path.exists():
            return defaults
        lines = []
        for line in path.read_text(encoding="utf-8").splitlines():
            keyword = line.strip()
            if keyword and not keyword.startswith("#"):
                lines.append(keyword)
        return lines or defaults

    # ------------------------------------------------------------------ parse

    def parse(self, bio: str, today: date | None = None) -> list[ParsedTrip]:
        if not bio or not bio.strip():
            return []
        today = today or date.today()
        tokens = self._tokenize_dates(bio, today=today)
        raw_source = self._clean_text(bio)

        trips: list[ParsedTrip] = []
        for segment in self._split_segments(bio, tokens):
            trips.extend(self._parse_segment(bio, segment, raw_source))
        trips.extend(self._parse_undated(bio, tokens, raw_source))
        return self._dedupe(trips)

    # ------------------------------------------------------------- segmenting

    def _split_segments(self, text: str, tokens: list[DateToken]) -> list[_Segment]:
        """Cut the bio on hard separators, never inside a recognised date."""
        boundaries = [0]
        for index, char in enumerate(text):
            if not SEGMENT_SPLIT_RE.match(char):
                continue
            if any(token.start <= index < token.end for token in tokens):
                continue
            # "8.21。  NX海南嘉年华" — the mark is filler after the date, and
            # cutting there would strand the date without its location. A line
            # break in that position is still a real break.
            if char not in "\n\r" and any(token.end == index for token in tokens):
                continue
            boundaries.append(index + 1)
        boundaries.append(len(text))

        segments: list[_Segment] = []
        for start, end in zip(boundaries, boundaries[1:]):
            if start >= end:
                continue
            inside = [
                token for token in tokens if start <= token.start and token.end <= end
            ]
            if inside:
                segments.append(_Segment(start=start, end=end, tokens=inside))
        return segments

    def _parse_segment(
        self, text: str, segment: _Segment, raw_source: str
    ) -> list[ParsedTrip]:
        groups = self._group_tokens(text, segment.tokens)
        head = self._clean_location(text[segment.start : segment.tokens[0].start])
        tail = self._clean_location(text[segment.tokens[-1].end : segment.end])
        # "地点 + 日期" ordering is only assumed when the segment ends on a date
        # and opens with something that is not just a "行程：" style label.
        postfixed = bool(head) and not tail and not self._is_schedule_label(head)

        trips: list[ParsedTrip] = []
        for index, group in enumerate(groups):
            left = groups[index - 1][-1].end if index > 0 else segment.start
            right = (
                groups[index + 1][0].start
                if index + 1 < len(groups)
                else segment.end
            )
            before = self._clean_location(text[left : group[0].start])
            after = self._clean_location(text[group[-1].end : right])
            if postfixed:
                location = before or (tail if index == len(groups) - 1 else "")
                if not location:
                    location = self._adjacent(
                        text, group[-1].end, right, after, before=False
                    )
            else:
                location = after or (
                    head if index == 0 and not self._is_schedule_label(head) else ""
                )
                if not location:
                    location = self._adjacent(
                        text, left, group[0].start, before, before=True
                    )
            if not location:
                continue
            for token in group:
                for trip_date in token.dates:
                    trips.append(
                        ParsedTrip(
                            trip_date=trip_date,
                            is_dated=True,
                            location_activity=location,
                            raw_source_text=raw_source,
                            confidence=self._confidence(token),
                        )
                    )
        return trips

    @staticmethod
    def _confidence(token: DateToken) -> float:
        if token.confidence is not None:
            return token.confidence
        return 0.95 if token.year_given else 0.82

    def _group_tokens(self, text: str, tokens: list[DateToken]) -> list[list[DateToken]]:
        if not tokens:
            return []
        groups: list[list[DateToken]] = []
        current = [tokens[0]]
        for token in tokens[1:]:
            gap = text[current[-1].end : token.start]
            if IGNORABLE_GAP_RE.fullmatch(gap) and self._dates_are_close(
                current[-1], token
            ):
                current.append(token)
            else:
                groups.append(current)
                current = [token]
        groups.append(current)
        return groups

    @staticmethod
    def _dates_are_close(left: DateToken, right: DateToken) -> bool:
        """Only whitespace between "8.15" and "10.2" still means two events."""
        if not left.dates or not right.dates:
            return True
        return abs((right.dates[0] - left.dates[-1]).days) <= MAX_GROUP_GAP_DAYS

    def _adjacent(
        self, text: str, left: int, right: int, whole: str, before: bool
    ) -> str:
        """Last resort: the words glued to the date, as in "南宁8.15 10.2沈阳".

        Only reached when the whole side was already claimed by a neighbouring
        date, so the glued part has to be a shorter string than that one.
        """
        parts = [part for part in re.split(r"\s+", text[left:right]) if part]
        if not parts:
            return ""
        candidate = self._clean_location(parts[-1] if before else parts[0])
        if not candidate or candidate == whole:
            return ""
        return candidate

    # ------------------------------------------------------------- tokenizing

    def _tokenize_dates(self, text: str, today: date) -> list[DateToken]:
        candidates = self._collect_candidates(text, today=today)
        # Longest match wins when two patterns start at the same offset, so a
        # range beats the plain date hiding inside it.
        candidates.sort(key=lambda token: (token.start, -(token.end - token.start)))

        accepted: list[DateToken] = []
        for candidate in candidates:
            if accepted and candidate.start < accepted[-1].end:
                continue
            if not self._context_ok(text, candidate, accepted):
                continue
            self._extend_with_enumeration(text, candidate)
            accepted.append(candidate)
        return accepted

    def _collect_candidates(self, text: str, today: date) -> list[DateToken]:
        candidates: list[DateToken] = []
        candidates.extend(self._iter_range_tokens(text, today=today))
        for pattern, year_given in (
            (FULL_DATE_RE, True),
            (CN_DATE_RE, False),
            (NUM_DATE_RE, False),
        ):
            for match in pattern.finditer(text):
                if not year_given and self._has_year_prefix(text, match.start()):
                    continue
                if not year_given and not self._looks_like_date(
                    text, match.start(), match.group(0),
                    match.group("month"), match.group("day"),
                ):
                    continue
                month = int(match.group("month"))
                day = int(match.group("day"))
                year = (
                    int(match.group("year"))
                    if year_given
                    else self._infer_year(month, day, today=today)
                )
                value = self._safe_date(year, month, day)
                if value is None:
                    continue
                candidates.append(
                    DateToken(
                        dates=[value],
                        start=match.start(),
                        end=match.end(),
                        year_given=year_given,
                        sep_class=self._match_sep_class(match.group(0)),
                    )
                )
        candidates.extend(self._iter_compact_tokens(text, today=today))
        return candidates

    def _iter_range_tokens(self, text: str, today: date) -> list[DateToken]:
        tokens: list[DateToken] = []
        for pattern, kind in (
            (RANGE_MD_MD_RE, "md_md"),
            (RANGE_MD_D_RE, "md_d"),
            (RANGE_CN_RE, "cn"),
        ):
            for match in pattern.finditer(text):
                if kind == "md_md":
                    month1, day1 = int(match.group("m1")), int(match.group("d1"))
                    month2, day2 = int(match.group("m2")), int(match.group("d2"))
                elif kind == "md_d":
                    month1 = month2 = int(match.group("m"))
                    day1, day2 = int(match.group("d1")), int(match.group("d2"))
                else:
                    month1, day1 = int(match.group("m1")), int(match.group("d1"))
                    month2 = int(match.group("m2") or match.group("m1"))
                    day2 = int(match.group("d2"))
                    if self._has_year_prefix(text, match.start()):
                        continue
                if not self._looks_like_date(
                    text, match.start(), match.group(0),
                    match.group("m1") if kind != "md_d" else match.group("m"),
                    match.group("d1"),
                ):
                    continue
                year = self._infer_year(month1, day1, today=today)
                start = self._safe_date(year, month1, day1)
                if start is None:
                    continue
                end_year = year if (month2, day2) >= (month1, day1) else year + 1
                end = self._safe_date(end_year, month2, day2)
                tokens.append(
                    DateToken(
                        dates=self._expand_range(start, end),
                        start=match.start(),
                        end=match.end(),
                        year_given=False,
                        sep_class=self._match_sep_class(match.group(0)),
                    )
                )
        return tokens

    @staticmethod
    def _expand_range(start: date, end: date | None) -> list[date]:
        if end is None or end < start:
            return [start]
        if (end - start).days > MAX_RANGE_DAYS:
            return [start]
        dates: list[date] = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    def _iter_compact_tokens(self, text: str, today: date) -> list[DateToken]:
        """Handle "925成都qy": a separator-less date glued to a place name.

        Only accepted at the very start of a segment and followed by a short
        Chinese place/event name, otherwise every QQ group id would match.
        """
        tokens: list[DateToken] = []
        for match in COMPACT_DATE_RE.finditer(text):
            start = match.start()
            if start > 0 and not SEGMENT_SPLIT_RE.match(text[start - 1]):
                continue
            digits = match.group("digits")
            if digits.startswith("0"):
                continue
            parsed = self._split_compact_digits(digits)
            if parsed is None:
                continue
            month, day = parsed
            rest = text[match.end() :]
            rest = rest[: SEGMENT_SPLIT_RE.search(rest).start()] if SEGMENT_SPLIT_RE.search(rest) else rest
            cleaned = self._clean_location(rest)
            if not 2 <= len(cleaned) <= 20:
                continue
            if not re.search(r"[一-鿿]", cleaned):
                continue
            if ENUM_UNIT_RE.match(cleaned):
                continue
            value = self._safe_date(self._infer_year(month, day, today=today), month, day)
            if value is None:
                continue
            tokens.append(
                DateToken(
                    dates=[value],
                    start=start,
                    end=match.end(),
                    year_given=False,
                    confidence=0.7,
                )
            )
        return tokens if len(tokens) > 1 else []

    @staticmethod
    def _split_compact_digits(digits: str) -> tuple[int, int] | None:
        """"925" is 9/25, "103" is 10/3 — never 1/03, nobody pads the day."""
        options: list[tuple[int, int]] = []
        if len(digits) == 3:
            if digits[1] != "0":
                options.append((int(digits[0]), int(digits[1:])))
            options.append((int(digits[:2]), int(digits[2])))
        else:
            options.append((int(digits[:2]), int(digits[2:])))
        for month, day in options:
            if 1 <= month <= 12 and 1 <= day <= 31:
                return month, day
        return None

    @staticmethod
    def _match_sep_class(matched: str) -> str:
        for char in matched:
            if char in ".．":
                return "."
            if char in "/／":
                return "/"
            if char in "-－":
                return "-"
            if char == "月":
                return "月"
        return ""

    def _looks_like_date(
        self, text: str, start: int, matched: str, month: str, day: str
    ) -> bool:
        """Filter the two shapes that only ever turn out to be booth ids."""
        if day.startswith("0") and not month.startswith("0"):
            # "n3-03", "N5-01" — nobody pads only the day.
            return False
        if self._match_sep_class(matched) == "-" and start > 0:
            previous = text[start - 1]
            if previous.isascii() and previous.isalnum():
                # "E4-29", "f2-2" — a dash date never sticks to a letter.
                return False
        return True

    def _context_ok(
        self, text: str, token: DateToken, accepted: list[DateToken]
    ) -> bool:
        start = token.start
        if start > 0:
            previous = text[start - 1]
            if previous.isdigit():
                # Only legitimate when the digits belong to the date before it,
                # e.g. "10月31" immediately followed by "11.1".
                if not (accepted and accepted[-1].end == start):
                    return False
            elif self._inside_alnum_token(text, start):
                return False
            if TIME_PREFIX_RE.search(text[max(0, start - 2) : start]):
                return False
        if UNIT_SUFFIX_RE.match(text[token.end : token.end + 4]):
            return False
        return True

    @staticmethod
    def _inside_alnum_token(text: str, start: int) -> bool:
        """True for "2460f2.8" or "35150f2-2.8" — a model number, not a date."""
        index = start
        while index > 0 and (
            (text[index - 1].isascii() and text[index - 1].isalpha())
            or text[index - 1] in "+-."
        ):
            index -= 1
        if index == start:
            return False
        return index > 0 and (text[index - 1].isdigit() or text[index - 1] == ".")

    def _extend_with_enumeration(self, text: str, token: DateToken) -> None:
        """Absorb "8.16/21/26/28" or "9.5 6 12 13" into a single token."""
        base = token.dates[0]
        dates = list(token.dates)
        position = token.end
        separator: str | None = None
        while position < len(text):
            sep_match = ENUM_SEP_RE.match(text, position)
            if not sep_match:
                break
            sep_key = self._separator_class(sep_match.group(0))
            if separator is None:
                separator = sep_key
            elif sep_key != separator:
                break
            item = ENUM_ITEM_RE.match(text, sep_match.end())
            if not item:
                break
            following = text[item.end() : item.end() + 2]
            # "8.15 8.16" is two dates: the item is a month, not a day.
            if re.match(rf"{MD_SEP}\d", following) and (
                self._separator_class(following[0]) != separator
            ):
                break
            if following.startswith("月") or ENUM_UNIT_RE.match(following):
                break
            # "7-10 7-11" is two dates while "9.5-6 12-13" is one: a dash item
            # only continues a list whose base date did not use a dash itself.
            if item.group("d2") and separator == " " and token.sep_class == "-":
                if re.search(r"[-－]", text[sep_match.end() : item.end()]):
                    break
            first = self._safe_date(base.year, base.month, int(item.group("d1")))
            if first is None:
                break
            last = first
            if item.group("d2"):
                last = self._safe_date(base.year, base.month, int(item.group("d2")))
                if last is None:
                    break
            dates.extend(self._expand_range(first, last))
            position = item.end()
        if position > token.end:
            token.end = position
            token.dates = self._unique_dates(dates)

    @staticmethod
    def _separator_class(text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return " "
        char = stripped[-1]
        for group in (".．", "/／", "、,，", "&＆和"):
            if char in group:
                return group
        return char

    @staticmethod
    def _unique_dates(values: list[date]) -> list[date]:
        seen: set[date] = set()
        result: list[date] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

    @staticmethod
    def _has_year_prefix(text: str, start: int) -> bool:
        prefix = text[max(0, start - 6) : start]
        return re.search(r"\d{4}\s*年\s*$", prefix) is not None

    def _infer_year(self, month: int, day: int, today: date) -> int:
        """Pick the year that puts the date closest to today.

        Bios mix announcements ("10.24 广州") with a log of past events
        ("5.1 无锡云图车展"); always rolling forward turned last spring into next
        spring. A small penalty on past distances keeps the tie-break on the
        upcoming side.
        """
        best: tuple[float, int] | None = None
        for year in (today.year - 1, today.year, today.year + 1):
            value = self._safe_date(year, month, day)
            if value is None:
                continue
            delta = (value - today).days
            score = float(delta) if delta >= 0 else -delta * 1.15
            if best is None or score < best[0]:
                best = (score, year)
        return best[1] if best else today.year

    @staticmethod
    def _safe_date(year: int, month: int, day: int) -> date | None:
        try:
            return date(year, month, day)
        except ValueError:
            return None

    # --------------------------------------------------------------- cleaning

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip(_STRIP_CHARS).strip()

    def _clean_location(self, text: str) -> str:
        text = self._trim(text)
        if not text:
            return ""
        for marker in SCHEDULE_HINT_MARKERS:
            index = text.rfind(marker)
            if index == -1:
                continue
            rest = self._trim(text[index + len(marker) :])
            if rest:
                text = rest
            break
        text = self._trim(LEADING_LABEL_RE.sub("", text))
        if text.startswith("@"):
            mention = re.match(r"@[^\s@,，。；;、|｜]+", text)
            return mention.group(0) if mention else ""
        stop = LOCATION_STOP_RE.search(text)
        if stop:
            text = self._trim(text[: stop.start()])
        text = self._trim(TRAILING_LABEL_RE.sub("", text))
        text = self._trim(self._drop_unmatched_brackets(text))
        if not text or not WORD_RE.search(text):
            return ""
        if STATUS_ONLY_RE.match(text):
            return ""
        return text

    @staticmethod
    def _trim(text: str) -> str:
        """Peel punctuation and decoration off both ends, until nothing moves."""
        text = re.sub(r"\s+", " ", text)
        previous = None
        while previous != text:
            previous = text
            text = text.strip(_STRIP_CHARS)
            leading = DECOR_RE.match(text)
            if leading:
                text = text[leading.end() :]
            text = DECOR_TAIL_RE.sub("", text)
        return text.strip()

    @staticmethod
    def _drop_unmatched_brackets(text: str) -> str:
        stack: list[tuple[str, int]] = []
        remove: set[int] = set()
        for index, char in enumerate(text):
            if char in BRACKET_PAIRS:
                stack.append((char, index))
            elif char in CLOSERS:
                if stack and stack[-1][0] == CLOSERS[char]:
                    stack.pop()
                else:
                    remove.add(index)
        remove.update(index for _, index in stack)
        if not remove:
            return text
        return "".join(char for index, char in enumerate(text) if index not in remove)

    @staticmethod
    def _is_schedule_label(text: str) -> bool:
        stripped = re.sub(r"[\s:：]+", "", text)
        return bool(stripped) and SCHEDULE_LABEL_RE.match(stripped) is not None

    # ---------------------------------------------------------------- undated

    def _parse_undated(
        self, bio: str, tokens: list[DateToken], raw_source: str
    ) -> list[ParsedTrip]:
        trips: list[ParsedTrip] = []
        for start, end in self._line_spans(bio):
            if any(token.start < end and token.end > start for token in tokens):
                continue
            clean_line = self._clean_text(bio[start:end])
            if not 3 <= len(clean_line) <= 24:
                continue
            if not self._has_undated_keyword(clean_line):
                continue
            if UNDATED_NOISE_RE.search(clean_line):
                continue
            if not UNDATED_EVENT_RE.search(clean_line):
                continue
            if not UNDATED_PLACE_RE.search(clean_line):
                continue
            location = self._clean_location(clean_line)
            if not 3 <= len(location) <= 24:
                continue
            trips.append(
                ParsedTrip(
                    trip_date=None,
                    is_dated=False,
                    location_activity=location,
                    raw_source_text=raw_source,
                    confidence=0.55,
                )
            )
        return trips

    @staticmethod
    def _line_spans(text: str) -> list[tuple[int, int]]:
        spans: list[tuple[int, int]] = []
        position = 0
        for match in LINE_SPLIT_RE.finditer(text):
            if match.start() > position:
                spans.append((position, match.start()))
            position = match.end()
        if position < len(text):
            spans.append((position, len(text)))
        return spans

    def _has_undated_keyword(self, text: str) -> bool:
        lowered = text.lower()
        return any(keyword.lower() in lowered for keyword in self.keywords)

    # ----------------------------------------------------------------- output

    @staticmethod
    def _dedupe(trips: list[ParsedTrip]) -> list[ParsedTrip]:
        seen: set[tuple[date | None, bool, str]] = set()
        result: list[ParsedTrip] = []
        for trip in trips:
            key = (trip.trip_date, trip.is_dated, trip.location_activity)
            if key in seen:
                continue
            seen.add(key)
            result.append(trip)
        return result
