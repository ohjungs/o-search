import unittest
from unittest import mock

from websearch import robots


def _cache_with(fetch):
    c = robots.RobotsCache()
    c._fetch_robots = fetch  # 네트워크 차단 (project.md 한도)
    return c


class TestRobotsCache(unittest.TestCase):
    def test_allows_when_robots_permits(self):
        c = _cache_with(lambda base: (200, "User-agent: *\nAllow: /"))
        self.assertTrue(c.allowed("http://a.com/page"))

    def test_blocks_when_robots_disallows(self):
        c = _cache_with(lambda base: (200, "User-agent: *\nDisallow: /secret"))
        self.assertFalse(c.allowed("http://a.com/secret/x"))
        self.assertTrue(c.allowed("http://a.com/open"))

    def test_allows_when_robots_missing(self):
        c = _cache_with(lambda base: (404, ""))
        self.assertTrue(c.allowed("http://a.com/page"))

    def test_blocks_when_robots_fetch_fails(self):
        c = _cache_with(lambda base: (503, ""))
        self.assertFalse(c.allowed("http://a.com/page"))

    def test_fetches_once_per_domain(self):
        fetch = mock.Mock(return_value=(200, "User-agent: *\nAllow: /"))
        c = _cache_with(fetch)
        c.allowed("http://a.com/1")
        c.allowed("http://a.com/2")
        self.assertEqual(fetch.call_count, 1)


class TestCrawlDelay(unittest.TestCase):
    def test_reports_declared_delay(self):
        c = _cache_with(lambda base: (200, "User-agent: *\nCrawl-delay: 3\nAllow: /"))
        self.assertEqual(c.delay("http://a.com/page"), 3.0)

    def test_no_directive_reports_none(self):
        c = _cache_with(lambda base: (200, "User-agent: *\nAllow: /"))
        self.assertIsNone(c.delay("http://a.com/page"))

    def test_fractional_delay_is_not_lost(self):
        # stdlib 은 isdigit 검사로 "3.5" 를 조용히 버린다 — 그러면 1초로 떨어져
        # 사이트가 요청한 것보다 3.5배 빠르게 때린다. 윤리 축에서 이건 위반이다
        c = _cache_with(lambda base: (200, "User-agent: *\nCrawl-delay: 3.5"))
        self.assertEqual(c.delay("http://a.com/page"), 3.5)

    def test_missing_robots_has_no_delay(self):
        c = _cache_with(lambda base: (404, ""))
        self.assertIsNone(c.delay("http://a.com/page"))

    def test_shares_one_robots_fetch_with_allowed(self):
        fetch = mock.Mock(return_value=(200, "User-agent: *\nCrawl-delay: 2"))
        c = _cache_with(fetch)
        c.allowed("http://a.com/1")
        self.assertEqual(c.delay("http://a.com/2"), 2.0)
        self.assertEqual(fetch.call_count, 1)

    def test_fallback_takes_the_slowest_line_in_our_group(self):
        # 한 그룹이 여러 번 말하면 가장 느린 것을 고른다 — 느린 쪽으로만 틀린다.
        # 남의 그룹(other)은 우리 값이 아니므로 보지 않는다
        c = _cache_with(lambda base: (200, "User-agent: other\nCrawl-delay: 30.5\n\n"
                                           "User-agent: *\nCrawl-delay: 2.5\n"
                                           "Crawl-delay: 7.5"))
        self.assertEqual(c.delay("http://a.com/page"), 7.5)

    def test_malformed_delay_never_speeds_us_up(self):
        # robots.txt 는 원격 입력이다. 망가진 값에 예외를 내면 크롤 전체가 죽고,
        # 마음대로 빠르게 잡으면 윤리 위반이다. 규칙은 하나 — **느린 쪽으로만 틀린다.**
        # 숫자가 없으면 지시 없음(호출부가 기본 1초), 숫자가 앞에 있으면 그 값을 쓴다
        # ("5s" 를 5초로 읽는 것은 1초로 떨어지는 것보다 사이트 뜻에 가깝다)
        for value, want in [("abc", None), ("", None), ("-5", None),
                            ("5s", 5.0), ("2 # 주석", 2.0)]:
            with self.subTest(value=value):
                c = _cache_with(lambda base, v=value: (200, "User-agent: *\nCrawl-delay: %s" % v))
                self.assertEqual(c.delay("http://a.com/page"), want)

    def test_fallback_ignores_other_agents_groups(self):
        # 폴백은 "우리에게 적용되는 그룹"만 본다. 남의 그룹(86400)을 집으면
        # 1.5초면 지킬 수 있는 사이트를 통째로 버리게 된다 (frontier.MAX_DELAY)
        c = _cache_with(lambda base: (200, "User-agent: *\nCrawl-delay: 1.5\n\n"
                                           "User-agent: AhrefsBot\nCrawl-delay: 86400\n"))
        self.assertEqual(c.delay("http://a.com/page"), 1.5)

    def test_our_own_group_wins_over_wildcard(self):
        c = _cache_with(lambda base: (200, "User-agent: websearchbot\nCrawl-delay: 4.5\n\n"
                                           "User-agent: *\nCrawl-delay: 0.5\n"))
        self.assertEqual(c.delay("http://a.com/page"), 4.5)

    def test_exponent_notation_is_not_read_as_one_second(self):
        # "1e3" 의 앞 숫자만 집으면 1000초를 요구한 사이트를 1초로 때린다
        c = _cache_with(lambda base: (200, "User-agent: *\nCrawl-delay: 1e3"))
        self.assertEqual(c.delay("http://a.com/page"), 1000.0)
