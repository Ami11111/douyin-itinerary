"""Parser fixtures.

The bio shapes here are taken from real profiles, but every convention, venue
and IP name is invented — only the punctuation, spacing and ordering matter to
the rules under test.
"""

from datetime import date

from app.parser import ItineraryParser


TODAY = date(2026, 8, 18)


def test_parse_simple_numeric_date():
    trips = ItineraryParser().parse("8.9 长沙星屿海洋乐园", today=TODAY)
    assert len(trips) == 1
    assert trips[0].is_dated is True
    assert trips[0].trip_date == date(2026, 8, 9)
    assert trips[0].location_activity == "长沙星屿海洋乐园"


def test_parse_chinese_date():
    trips = ItineraryParser().parse("8月9日 长沙星屿海洋乐园", today=TODAY)
    assert len(trips) == 1
    assert trips[0].trip_date == date(2026, 8, 9)


def test_parse_explicit_year():
    trips = ItineraryParser().parse("2026.8.9 长沙星屿海洋乐园", today=TODAY)
    assert len(trips) == 1
    assert trips[0].trip_date == date(2026, 8, 9)


def test_parse_multiple_dates_in_one_bio():
    trips = ItineraryParser().parse(
        "8.9 长沙星屿海洋乐园 8.10 武汉巡演",
        today=TODAY,
    )
    assert [trip.trip_date for trip in trips] == [date(2026, 8, 9), date(2026, 8, 10)]
    assert [trip.location_activity for trip in trips] == ["长沙星屿海洋乐园", "武汉巡演"]


def test_parse_date_range():
    trips = ItineraryParser().parse("8.7-8.9 重庆栖鹤", today=TODAY)
    assert [trip.trip_date for trip in trips] == [
        date(2026, 8, 7),
        date(2026, 8, 8),
        date(2026, 8, 9),
    ]
    assert {trip.location_activity for trip in trips} == {"重庆栖鹤"}


def test_parse_same_month_date_range():
    trips = ItineraryParser().parse("10.24-25 广州锦棠社", today=TODAY)
    assert [trip.trip_date for trip in trips] == [
        date(2026, 10, 24),
        date(2026, 10, 25),
    ]
    assert {trip.location_activity for trip in trips} == {"广州锦棠社"}


def test_parse_chinese_date_range():
    trips = ItineraryParser().parse("8月22-23 无锡站", today=TODAY)
    assert [trip.trip_date for trip in trips] == [
        date(2026, 8, 22),
        date(2026, 8, 23),
    ]
    assert {trip.location_activity for trip in trips} == {"无锡站"}


def test_parse_cross_month_range():
    trips = ItineraryParser().parse("7.31～8.2 日本深空列车快闪", today=TODAY)
    assert [trip.trip_date for trip in trips] == [
        date(2026, 7, 31),
        date(2026, 8, 1),
        date(2026, 8, 2),
    ]
    assert {trip.location_activity for trip in trips} == {"日本深空列车快闪"}


def test_parse_range_ignores_leading_label():
    trips = ItineraryParser().parse("行程：7.10-7.11ac弦月", today=TODAY)
    assert [trip.trip_date for trip in trips] == [
        date(2026, 7, 10),
        date(2026, 7, 11),
    ]
    assert {trip.location_activity for trip in trips} == {"ac弦月"}


def test_parse_postfixed_date_entries():
    bio = "近日行程： 🎀 青岛·NX次元派对 8.6🎀沈阳·星潮漫展 8.15"
    trips = ItineraryParser().parse(bio, today=TODAY)
    assert [t.trip_date for t in trips] == [date(2026, 8, 6), date(2026, 8, 15)]
    assert [t.location_activity for t in trips] == ["青岛·NX次元派对", "沈阳·星潮漫展"]


def test_parse_day_enumeration():
    trips = ItineraryParser().parse("9.5 6 12 13 上海", today=TODAY)
    assert [t.trip_date for t in trips] == [
        date(2026, 9, 5),
        date(2026, 9, 6),
        date(2026, 9, 12),
        date(2026, 9, 13),
    ]
    assert {t.location_activity for t in trips} == {"上海"}


def test_parse_slash_separated_day_enumeration():
    trips = ItineraryParser().parse("8.16/21/26/28云顶zx我推快闪织星", today=TODAY)
    assert [trip.trip_date for trip in trips] == [
        date(2026, 8, 16),
        date(2026, 8, 21),
        date(2026, 8, 26),
        date(2026, 8, 28),
    ]
    assert {trip.location_activity for trip in trips} == {"云顶zx我推快闪织星"}


def test_parse_two_ranges_with_different_locations():
    trips = ItineraryParser().parse(
        "8.7-10，8.14-15:上海云海 8.22-23成都棱镜",
        today=TODAY,
    )
    expected = {
        date(2026, 8, 7): "上海云海",
        date(2026, 8, 8): "上海云海",
        date(2026, 8, 9): "上海云海",
        date(2026, 8, 10): "上海云海",
        date(2026, 8, 14): "上海云海",
        date(2026, 8, 15): "上海云海",
        date(2026, 8, 22): "成都棱镜",
        date(2026, 8, 23): "成都棱镜",
    }
    assert {trip.trip_date: trip.location_activity for trip in trips} == expected


def test_parse_adjacent_dates_without_spaces():
    trips = ItineraryParser().parse("10.5河北夜航10月3111.1成都", today=TODAY)
    assert [t.trip_date for t in trips] == [
        date(2026, 10, 5),
        date(2026, 10, 31),
        date(2026, 11, 1),
    ]
    assert [t.location_activity for t in trips] == ["河北夜航", "成都", "成都"]


def test_ignore_historical_year_date():
    trips = ItineraryParser().parse("1945年9月2号 胜利日", today=TODAY)
    assert trips == []


def test_parse_location_with_square_bracket_suffix():
    trips = ItineraryParser().parse(
        "8月21 -上海市徐汇区星环广场·LIVE 东区B1中庭【山海绘卷】",
        today=TODAY,
    )
    assert len(trips) == 1
    assert trips[0].trip_date == date(2026, 8, 21)
    assert trips[0].location_activity == "上海市徐汇区星环广场·LIVE 东区B1中庭【山海绘卷】"


def test_parse_bullet_prefixed_date_lines():
    bio = (
        "近期线下活动如下:\n"
        "⭐️8月21 -上海市徐汇区星环广场·LIVE 东区B1中庭【山海绘卷】\n"
        "⭐️8月23 - 长沙锦时广场晨风&深空列车【澪】"
    )
    trips = ItineraryParser().parse(bio, today=TODAY)
    assert trips[0].trip_date == date(2026, 8, 21)
    assert trips[0].location_activity == "上海市徐汇区星环广场·LIVE 东区B1中庭【山海绘卷】"
    assert trips[1].trip_date == date(2026, 8, 23)
    assert trips[1].location_activity == "长沙锦时广场晨风&深空列车【澪】"


def test_parse_undated_clue():
    trips = ItineraryParser().parse("去长沙参加签售", today=TODAY)
    assert len(trips) == 1
    assert trips[0].is_dated is False
    assert trips[0].trip_date is None


def test_ignore_phone_like_numbers():
    trips = ItineraryParser().parse("联系 138.9.9 或 2026.8.9 长沙", today=TODAY)
    assert len(trips) == 1
    assert trips[0].trip_date == date(2026, 8, 9)


def test_infer_recent_past_year_instead_of_next_year():
    trips = ItineraryParser().parse("行程：6.12 长沙机车嘉年华｜5.1 无锡云图车展", today=TODAY)
    assert [trip.trip_date for trip in trips] == [date(2026, 6, 12), date(2026, 5, 1)]


def test_postfixed_dates_are_detected_per_line():
    bio = (
        "身高178/42kg 合作私信\n"
        "🚀泡泡 沈阳星潮8.15 天津云海only9.12 合肥云海only9.26 厦门星潮10/6"
    )
    trips = ItineraryParser().parse(bio, today=TODAY)
    assert [trip.location_activity for trip in trips] == [
        "泡泡 沈阳星潮",
        "天津云海only",
        "合肥云海only",
        "厦门星潮",
    ]


def test_prefixed_line_is_not_shifted_by_a_decorated_label():
    bio = "谢谢喜欢 🌟程：7.25广州漫游乐园  8.2广州鹿岛动漫节"
    trips = ItineraryParser().parse(bio, today=TODAY)
    assert [(t.trip_date, t.location_activity) for t in trips] == [
        (date(2026, 7, 25), "广州漫游乐园"),
        (date(2026, 8, 2), "广州鹿岛动漫节"),
    ]


def test_two_dates_separated_by_a_space_are_not_a_day_list():
    trips = ItineraryParser().parse("8.15 8.16云海清凉节（去玩）", today=TODAY)
    assert [trip.trip_date for trip in trips] == [date(2026, 8, 15), date(2026, 8, 16)]
    assert {trip.location_activity for trip in trips} == {"云海清凉节（去玩）"}


def test_decorative_emoji_are_not_locations():
    bio = "🌱线下行程🩵6.25-6.28 武汉云雀嘉年华🩵7.4-7.5 成都星野谷🩵"
    trips = ItineraryParser().parse(bio, today=TODAY)
    assert {trip.location_activity for trip in trips} == {
        "武汉云雀嘉年华",
        "成都星野谷",
    }


def test_ignore_age_time_and_model_numbers():
    bio = (
        "18-28岁｜每天4-6小时\n"
        "直播:晚9-11\n"
        "相机s5m2x 加镜头2460f2.8\n"
        "mx 星芯N5-01 展台在E4-29"
    )
    assert [trip for trip in ItineraryParser().parse(bio, today=TODAY) if trip.is_dated] == []


def test_range_after_letters_and_with_day_suffix():
    trips = ItineraryParser().parse("ac7.10-11全勤，8.22—8.23日 东莞青羽", today=TODAY)
    assert [trip.trip_date for trip in trips] == [
        date(2026, 7, 10),
        date(2026, 7, 11),
        date(2026, 8, 22),
        date(2026, 8, 23),
    ]
    assert trips[-1].location_activity == "东莞青羽"


def test_day_list_with_chinese_enumeration_separator():
    trips = ItineraryParser().parse("9.18、19、20广州lm摄影会", today=TODAY)
    assert [trip.trip_date for trip in trips] == [
        date(2026, 9, 18),
        date(2026, 9, 19),
        date(2026, 9, 20),
    ]


def test_day_ranges_listed_after_a_chinese_month():
    trips = ItineraryParser().parse("8月7-8、10-12，14-16上海云海清凉节", today=TODAY)
    assert [trip.trip_date.day for trip in trips] == [7, 8, 10, 11, 12, 14, 15, 16]
    assert {trip.location_activity for trip in trips} == {"上海云海清凉节"}


def test_dash_dates_separated_by_space_stay_separate():
    trips = ItineraryParser().parse("7-10 7-11上海AC", today=TODAY)
    assert [trip.trip_date for trip in trips] == [date(2026, 7, 10), date(2026, 7, 11)]


def test_day_range_continues_a_dotted_date():
    trips = ItineraryParser().parse("9.5-6 12-13上海星海赛", today=TODAY)
    assert [trip.trip_date.day for trip in trips] == [5, 6, 12, 13]
    assert {trip.location_activity for trip in trips} == {"上海星海赛"}


def test_long_range_is_not_expanded_day_by_day():
    trips = ItineraryParser().parse("南京星野谷npc 6.27-8.30", today=TODAY)
    assert [trip.trip_date for trip in trips] == [date(2026, 6, 27)]


def test_distant_dates_separated_by_space_are_separate_entries():
    trips = ItineraryParser().parse("行程:7.19浙江宁波 南宁8.15 10.2沈阳", today=TODAY)
    assert [(t.trip_date, t.location_activity) for t in trips] == [
        (date(2026, 7, 19), "浙江宁波 南宁"),
        (date(2026, 8, 15), "南宁"),
        (date(2026, 10, 2), "沈阳"),
    ]


def test_location_before_date_when_the_text_after_is_a_greeting():
    trips = ItineraryParser().parse("云海纪元摄影会定档9月6日，欢迎来玩", today=TODAY)
    assert len(trips) == 1
    assert trips[0].location_activity == "云海纪元摄影会"


def test_mention_only_location_is_kept():
    trips = ItineraryParser().parse("行程：8.22-23@云汐摄影会", today=TODAY)
    assert {trip.location_activity for trip in trips} == {"@云汐摄影会"}


def test_unmatched_bracket_and_status_only_locations():
    trips = ItineraryParser().parse("8.18广州晴野周年庆 （延期8.19）8.22广州云港", today=TODAY)
    assert [(t.trip_date, t.location_activity) for t in trips] == [
        (date(2026, 8, 18), "广州晴野周年庆 延期"),
        (date(2026, 8, 22), "广州云港"),
    ]


def test_compact_dates_need_more_than_one_occurrence():
    trips = ItineraryParser().parse("925成都qy （签售）\n103上海星潮（签售）", today=TODAY)
    assert [trip.trip_date for trip in trips] == [date(2026, 9, 25), date(2026, 10, 3)]
    assert ItineraryParser().parse("211本硕 谢谢喜欢", today=TODAY) == []


def test_full_width_slash_day_list():
    trips = ItineraryParser().parse("10.24／25上海", today=TODAY)
    assert [trip.trip_date for trip in trips] == [date(2026, 10, 24), date(2026, 10, 25)]
    assert {trip.location_activity for trip in trips} == {"上海"}


def test_slash_separated_dates_share_a_location():
    trips = ItineraryParser().parse("行程: 7.17/7.19/7.20青羽签售", today=TODAY)
    assert [trip.trip_date.day for trip in trips] == [17, 19, 20]
    assert {trip.location_activity for trip in trips} == {"青羽签售"}


def test_full_stop_after_a_date_is_not_a_line_break():
    trips = ItineraryParser().parse("8.21。   NX海南动漫游戏嘉年华", today=TODAY)
    assert [(t.trip_date, t.location_activity) for t in trips] == [
        (date(2026, 8, 21), "NX海南动漫游戏嘉年华")
    ]


def test_day_suffix_is_consumed_but_not_the_word_japan():
    assert ItineraryParser().parse("mx7.31签售 8.1日云图展台", today=TODAY)[-1].location_activity == "云图展台"
    trips = ItineraryParser().parse("7.31～8.2 日本深空列车快闪", today=TODAY)
    assert {trip.location_activity for trip in trips} == {"日本深空列车快闪"}


def test_undated_clue_needs_a_place_and_an_event():
    parser = ItineraryParser()
    assert parser.parse("偶尔接接商演活动", today=TODAY) == []
    clue = parser.parse("线下行程：上海ac全勤", today=TODAY)[0]
    assert clue.is_dated is False
    assert clue.location_activity == "上海ac全勤"
