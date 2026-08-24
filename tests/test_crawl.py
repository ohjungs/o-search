import unittest
from unittest import mock

from websearch import crawl
from websearch.fetcher import FetchResult


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
            html = PAGES.get(url)
            return FetchResult(200, html) if html is not None else FetchResult(404, None)

        robots = mock.Mock()
        robots.allowed = lambda url: url not in blocked
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms:
            mf.fetch = fake_fetch
            n = crawl.crawl(seeds, max_pages, db_path=":memory:", robots_cache=robots)
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

    def test_failed_fetch_counted_not_as_page(self):
        n, _, _ = self._run(["http://nowhere.test/"], max_pages=5)
        self.assertEqual(n, 0)
