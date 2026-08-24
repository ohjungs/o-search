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

    def test_fractional_fallback_takes_the_slowest_line(self):
        # 폴백은 UA 그룹을 구분하지 않는다(설계 "범위 밖"). 구분 못 할 바에는
        # 가장 느린 값을 고른다 — 틀리더라도 느린 쪽으로만 틀린다
        c = _cache_with(lambda base: (200, "User-agent: other\nCrawl-delay: 7.5\n"
                                           "User-agent: *\nCrawl-delay: 2.5"))
        self.assertEqual(c.delay("http://a.com/page"), 7.5)
