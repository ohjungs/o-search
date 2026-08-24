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
