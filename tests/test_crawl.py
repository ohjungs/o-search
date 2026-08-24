import unittest
import urllib.parse
from unittest import mock

from websearch import crawl
from websearch.fetcher import FetchResult


REDIRECTS = {"http://a.com/moved": "http://b.com/"}

PAGES = {
    "http://a.com/": '<a href="/1">1</a><a href="/blocked">b</a><a href="http://b.com/">b</a>',
    "http://a.com/1": '<a href="/">home</a>',
    "http://b.com/": "leaf",
}


class TestCrawl(unittest.TestCase):
    def _run(self, seeds, max_pages, blocked=("http://a.com/blocked",), delays=None):
        fetched = []
        self.fetch_times = []  # (url, 그때의 가짜 시각) — 간격 계약을 여기서 잰다

        def fake_fetch(url):
            fetched.append(url)
            self.fetch_times.append((url, clock["t"]))
            target = REDIRECTS.get(url, url)
            html = PAGES.get(target)
            return FetchResult(200, html, target) if html is not None else FetchResult(404, None, url)

        robots = mock.Mock()
        robots.allowed = lambda url: url not in blocked
        robots.delay = lambda url: (delays or {}).get(
            urllib.parse.urlsplit(url).netloc)
        clock = {"t": 1000.0}
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms:
            mf.fetch = fake_fetch
            # 가짜 시계: sleep 이 시간을 흘려보낸다 — 실제 대기 없이 결정적
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            n = crawl.crawl(seeds, max_pages, db_path=":memory:",
                            robots_cache=robots, now=lambda: clock["t"])
        return n, fetched, ms

    def test_crawls_seed_and_follows_links(self):
        n, fetched, _ = self._run(["http://a.com/"], max_pages=10)
        self.assertEqual(n, 3)
        self.assertIn("http://b.com/", fetched)

    def test_robots_blocked_url_never_fetched(self):
        _, fetched, _ = self._run(["http://a.com/"], max_pages=10)
        self.assertNotIn("http://a.com/blocked", fetched)

    def test_max_pages_respected(self):
        n, fetched, _ = self._run(["http://a.com/"], max_pages=1)
        self.assertEqual(n, 1)
        self.assertEqual(len(fetched), 1)

    def test_redirect_stored_and_resolved_at_final_url(self):
        # a.com/moved 가 b.com/ 으로 리다이렉트 — 저장 키·링크 base 는 최종 URL
        global PAGES
        pages = dict(PAGES)
        pages["http://b.com/"] = '<a href="/leaf">l</a>'
        pages["http://b.com/leaf"] = "x"
        with mock.patch.dict(PAGES, pages):
            _, fetched, _ = self._run(["http://a.com/moved"], max_pages=10)
        self.assertIn("http://b.com/leaf", fetched)  # 상대 링크가 b.com 기준으로 풀림

    def test_max_flag_errors_return_usage_not_traceback(self):
        self.assertEqual(crawl.main(["prog", "http://a.com/", "--max"]), 2)
        self.assertEqual(crawl.main(["prog", "http://a.com/", "--max", "abc"]), 2)

    def test_failed_fetch_counted_not_as_page(self):
        n, _, _ = self._run(["http://nowhere.test/"], max_pages=5)
        self.assertEqual(n, 0)


class TestCrawlDelayWiring(unittest.TestCase, ):
    """robots 가 요청한 간격이 크롤 루프를 거쳐 실제 요청 간격이 되는가."""

    _run = TestCrawl._run

    def _gaps(self, domain):
        times = [t for url, t in self.fetch_times
                 if urllib.parse.urlsplit(url).netloc == domain]
        return [b - a for a, b in zip(times, times[1:])]

    def test_declared_delay_paces_that_domain(self):
        self._run(["http://a.com/"], max_pages=10, delays={"a.com": 5.0})
        self.assertTrue(self._gaps("a.com"), "a.com 을 두 번 이상 요청해야 잴 수 있다")
        for gap in self._gaps("a.com"):
            self.assertGreaterEqual(gap, 5.0)

    def test_default_interval_when_no_directive(self):
        self._run(["http://a.com/"], max_pages=10)
        for gap in self._gaps("a.com"):
            self.assertGreaterEqual(gap, 1.0)
            self.assertLess(gap, 5.0)  # 요청도 없는데 느려지지 않는다

    def test_unkeepable_delay_stops_after_first_contact(self):
        # 첫 요청은 어떤 간격도 어기지 않는다. 어길 수 없는 것은 두 번째다 —
        # 그래서 간격을 깎는 대신 그 도메인을 더 가지 않는다
        pages = {"http://b.com/": '<a href="/x">x</a><a href="/y">y</a>',
                 "http://b.com/x": "x", "http://b.com/y": "y"}
        with mock.patch.dict(PAGES, pages):
            _, fetched, _ = self._run(["http://b.com/"], max_pages=10,
                                      delays={"b.com": 3600})
        self.assertEqual(fetched, ["http://b.com/"])
