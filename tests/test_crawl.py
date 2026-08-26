import io
import itertools
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


class TestNonAsciiUrl(unittest.TestCase):
    """비ASCII URL 이 태어나는 자리(시드·리다이렉트 최종 URL)에서 ASCII 가 되는가."""

    _run = TestCrawl._run

    def test_non_ascii_seed_fetched_as_ascii(self):
        with mock.patch.dict(PAGES, {"http://a.com/%EA%B0%80": "leaf"}):
            n, fetched, _ = self._run(["http://a.com/가"], max_pages=5)
        self.assertEqual(fetched, ["http://a.com/%EA%B0%80"])
        self.assertEqual(n, 1)

    def test_unconvertible_seed_dropped_rest_crawled(self):
        # CLI 는 신뢰 경계 — 못 바꾸는 시드 하나가 나머지 크롤을 막지 않는다
        n, fetched, _ = self._run(["http://.가/x", "http://a.com/"], max_pages=10)
        self.assertNotIn("http://.가/x", fetched)
        self.assertEqual(n, 3)

    def test_redirect_final_url_normalized_before_store(self):
        # 저장 키가 정규형이라야 ASCII 표기로 다시 온 같은 페이지를 두 번 받지 않는다
        with mock.patch.dict(REDIRECTS, {"http://a.com/moved2": "http://b.com/가"}), \
             mock.patch.dict(PAGES, {"http://b.com/가": "leaf"}):
            _, fetched, _ = self._run(
                ["http://a.com/moved2", "http://b.com/%EA%B0%80"], max_pages=10)
        self.assertEqual(fetched, ["http://a.com/moved2"])

    def test_unconvertible_redirect_target_falls_back_to_requested_url(self):
        # 최종 URL 을 못 바꿔도 받아온 페이지를 잃지 않는다 — 요청한 url 이 저장 키·링크 base
        with mock.patch.dict(REDIRECTS, {"http://a.com/moved3": "http://.가/"}), \
             mock.patch.dict(PAGES, {"http://.가/": '<a href="/x">x</a>'}):
            n, fetched, _ = self._run(["http://a.com/moved3"], max_pages=10)
        self.assertEqual(n, 1)
        self.assertIn("http://a.com/x", fetched)


    def test_robots_and_store_never_see_non_ascii_url(self):
        # 정규화가 URL 이 태어나는 자리에서 끝난다는 계약을 순서로 못박는다.
        # robots.allowed() 는 비ASCII 호스트에서 UnicodeEncodeError 를 그대로 던지고
        # (robots.py 는 URLError·OSError 만 잡는다) crawl 에도 잡는 곳이 없다 —
        # 정규화가 robots 뒤로 밀리는 순간 크롤 루프를 죽인 원래 버그가 되살아난다.
        # store 쪽은 죽지는 않지만 같은 페이지가 두 표기로 2행이 된다.
        asked, keys = [], []
        pages = {
            "http://a.com/%EA%B0%80":
                '<a href="/나">n</a><a href="http://한글도메인.test/">i</a>',
            "http://a.com/%EB%82%98": "leaf",
            "http://xn--bj0bj3i97fq8o5lq.test/": "leaf",
        }

        def fake_fetch(url):
            return (FetchResult(200, pages[url], url) if url in pages
                    else FetchResult(404, None, url))

        robots = mock.Mock()
        robots.allowed = lambda url: asked.append(url) or True
        robots.delay = lambda url: None
        real_store = crawl.Store

        def recording_store(path):
            store = real_store(path)
            has, upsert = store.has, store.upsert
            store.has = lambda u: keys.append(u) or has(u)
            store.upsert = lambda u, *a: keys.append(u) or upsert(u, *a)
            return store

        tick = itertools.count(1000.0, 10.0)  # 매 조회마다 시간이 흘러 간격이 걸리지 않는다
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.Store", recording_store):
            mf.fetch = fake_fetch
            n = crawl.crawl(["http://a.com/가"], 10, db_path=":memory:",
                            robots_cache=robots, now=lambda: next(tick))

        self.assertEqual(n, 3)  # 비ASCII 시드·링크·IDN 호스트를 실제로 다 돌았다
        for url in asked:
            self.assertTrue(url.isascii(), "robots 가 비ASCII 를 받았다: %r" % url)
        for url in keys:
            self.assertTrue(url.isascii(), "store 키가 비ASCII 다: %r" % url)


class TestCrawlDelayWiring(unittest.TestCase):
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

    def test_dropped_domain_is_reported_not_silent(self):
        # 조용히 1페이지만 받고 끝나면 사용자는 이유를 알 방법이 없다
        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            self._run(["http://b.com/"], max_pages=10, delays={"b.com": 3600})
        self.assertIn("b.com", err.getvalue())
        self.assertIn("3600", err.getvalue())
