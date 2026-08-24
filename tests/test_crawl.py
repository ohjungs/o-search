import unittest
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
    def _run(self, seeds, max_pages, blocked=("http://a.com/blocked",)):
        fetched = []

        def fake_fetch(url):
            fetched.append(url)
            target = REDIRECTS.get(url, url)
            html = PAGES.get(target)
            return FetchResult(200, html, target) if html is not None else FetchResult(404, None, url)

        robots = mock.Mock()
        robots.allowed = lambda url: url not in blocked
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
