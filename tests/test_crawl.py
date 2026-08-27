import io
import itertools
import threading
import time
import unittest
import urllib.parse
from unittest import mock

from websearch import crawl, fetcher
from websearch.frontier import MAX_DELAY
from websearch.fetcher import FetchResult


REDIRECTS = {"http://a.com/moved": "http://b.com/"}


def sending(fn):
    """가짜 fetch 를 **진짜처럼 발신 훅을 부르는** 가짜로 감싼다.

    `**kw` 로 `before_send` 를 조용히 삼키는 가짜는 있을 수 없는 fetcher 다 — 진짜는
    요청이 나갈 때 반드시 훅을 부른다. 안 부르면 크롤러는 "요청이 안 나갔다" 로 읽어
    도메인 시계를 걸지 않고, 그 위에서 잰 간격은 전부 거짓이 된다.
    """
    def fetch(url, before_send=None, **kw):
        if before_send is not None:
            before_send()
        return fn(url)
    return fetch

PAGES = {
    "http://a.com/": '<a href="/1">1</a><a href="/blocked">b</a><a href="http://b.com/">b</a>',
    "http://a.com/1": '<a href="/">home</a>',
    "http://b.com/": "leaf",
}


class TestCrawl(unittest.TestCase):
    def _run(self, seeds, max_pages, blocked=("http://a.com/blocked",), delays=None,
             workers=8):
        fetched = []
        self.fetch_times = []  # (url, 그때의 가짜 시각) — 간격 계약을 여기서 잰다

        def fake_fetch(url, **kw):  # 진짜 fetch 는 before_send·retries 를 받는다
            fetched.append(url)
            self.fetch_times.append((url, clock["t"]))
            target = REDIRECTS.get(url, url)
            html = PAGES.get(target)
            return FetchResult(200, html, target) if html is not None else FetchResult(404, None, url)

        robots = mock.Mock()
        robots.allowed = lambda url: url not in blocked
        robots.delay = lambda url: (delays or {}).get(
            urllib.parse.urlsplit(url).netloc)
        robots.known_delay = robots.delay  # 캐시 조회도 같은 계약을 흉내낸다
        clock = {"t": 1000.0}
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms:
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            # 가짜 시계: sleep 이 시간을 흘려보낸다 — 실제 대기 없이 결정적
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            n = crawl.crawl(seeds, max_pages, db_path=":memory:",
                            robots_cache=robots, now=lambda: clock["t"],
                            workers=workers)
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
        # CLI 는 신뢰 경계 — 못 바꾸는 시드 하나가 나머지 크롤을 막지 않는다.
        # 조용히 버리지도 않는다 — 사용자가 직접 준 URL 이라 왜 안 갔는지 알려준다
        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            n, fetched, _ = self._run(["http://.가/x", "http://a.com/"], max_pages=10)
        self.assertNotIn("http://.가/x", fetched)
        self.assertEqual(n, 3)
        self.assertIn("http://.가/x", err.getvalue())

    def test_redirect_final_url_normalized_before_store(self):
        # 저장 키가 정규형이라야 ASCII 표기로 다시 온 같은 페이지를 두 번 받지 않는다.
        #
        # **동시 크롤은 "이미 떠 있는 요청" 까지는 못 막는다** — 리다이렉트가
        # 어디로 갈지는 응답이 와야 알고, 그때 다른 워커는 이미 나갔다.
        # 큐에 남아 있는 URL 은 그대로 막힌다(제출 전 `store.has(url)`).
        # workers=1 은 되돌리기 수단이자 **옛 보장이 살아 있다는 증거**다.
        with mock.patch.dict(REDIRECTS, {"http://a.com/moved2": "http://b.com/가"}), \
             mock.patch.dict(PAGES, {"http://b.com/가": "leaf"}):
            _, fetched, _ = self._run(
                ["http://a.com/moved2", "http://b.com/%EA%B0%80"], max_pages=10,
                workers=1)
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

        def fake_fetch(url, **kw):  # 진짜 fetch 는 before_send·retries 를 받는다
            return (FetchResult(200, pages[url], url) if url in pages
                    else FetchResult(404, None, url))

        robots = mock.Mock()
        robots.allowed = lambda url: asked.append(url) or True
        robots.delay = lambda url: None
        robots.known_delay = robots.delay  # 캐시 조회도 같은 계약을 흉내낸다
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
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
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


class TestConcurrency(unittest.TestCase):
    """동시 fetch 계약 — docs/design_crawl-throughput.md 계약 1·3·6·7.

    시간을 재지 않는다 — 시간으로 동시성을 판정하면 부하 걸린 기계에서 흔들린다.
    배리어(만나야만 통과)와 동시 실행 수 최고치로 본다.
    """

    def _crawl(self, seeds, max_pages, fetch, workers=8, now=None):
        robots = mock.Mock()
        robots.allowed = lambda url: True
        robots.delay = lambda url: None
        robots.known_delay = robots.delay  # 캐시 조회도 같은 계약을 흉내낸다
        kwargs = {"db_path": ":memory:", "robots_cache": robots, "workers": workers}
        if now is not None:
            kwargs["now"] = now
        with mock.patch("websearch.crawl.fetcher") as mf:
            mf.fetch = sending(fetch)
            mf.RETRIES = fetcher.RETRIES
            return crawl.crawl(list(seeds), max_pages, **kwargs)

    def test_requests_run_concurrently(self):
        # 순차 루프면 넷이 배리어에서 만날 수 없어 타임아웃한다
        seeds = ["http://d%d.test/" % i for i in range(8)]
        barrier = threading.Barrier(4, timeout=5)

        def fake_fetch(url, **kw):  # 진짜 fetch 는 before_send·retries 를 받는다
            barrier.wait()  # 넷이 모여야 통과 — 순차면 BrokenBarrierError
            return FetchResult(200, "leaf", url)

        n = self._crawl(seeds, 8, fake_fetch)
        self.assertEqual(n, 8, "동시에 넷이 뜨지 못했다")

    def test_never_two_requests_in_flight_on_one_domain(self):
        # 동시성이 politeness 를 먹는 유일한 경로다. 시계를 빠르게 흘려 간격 자체는
        # 안 걸리게 해두고, **떠 있는 요청**이 막는지만 본다
        pages = {"http://one.test/": "".join('<a href="/p%d">p</a>' % i for i in range(6))}
        state = {"live": 0, "peak": 0}
        lock = threading.Lock()

        def fake_fetch(url, **kw):  # 진짜 fetch 는 before_send·retries 를 받는다
            with lock:
                state["live"] += 1
                state["peak"] = max(state["peak"], state["live"])
            time.sleep(0.05)
            with lock:
                state["live"] -= 1
            return FetchResult(200, pages.get(url, "leaf"), url)

        tick = itertools.count(1000.0, 10.0)  # 매 조회 10초 — 간격은 절대 안 걸린다
        self._crawl(["http://one.test/"], 7, fake_fetch, now=lambda: next(tick))
        self.assertEqual(state["peak"], 1,
                         "한 도메인에 동시 요청 %d개" % state["peak"])

    def test_max_pages_not_exceeded_under_concurrency(self):
        seeds = ["http://d%d.test/" % i for i in range(8)]
        fetched, lock = [], threading.Lock()

        def fake_fetch(url, **kw):  # 진짜 fetch 는 before_send·retries 를 받는다
            with lock:
                fetched.append(url)
            return FetchResult(200, "leaf", url)

        n = self._crawl(seeds, 3, fake_fetch)
        self.assertEqual(n, 3)
        self.assertLessEqual(len(fetched), 3, "상한을 넘겨 받았다: %s" % fetched)

    def test_worker_exception_does_not_kill_crawl(self):
        # 워커 하나가 죽어도 나머지는 간다. 조용히 죽지도 않는다
        def fake_fetch(url, **kw):  # 진짜 fetch 는 before_send·retries 를 받는다
            if url == "http://d1.test/":
                raise RuntimeError("워커가 죽었다")
            return FetchResult(200, "leaf", url)

        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            n = self._crawl(["http://d%d.test/" % i for i in range(4)], 4, fake_fetch)
        self.assertEqual(n, 3)
        self.assertIn("d1.test", err.getvalue())

    def test_single_worker_gets_the_same_pages(self):
        # 되돌리기 수단(--workers 1)이 진짜 도는지 — 느릴 뿐 결과가 같아야 한다
        seeds = ["http://d%d.test/" % i for i in range(4)]

        def run(workers):
            got, lock = [], threading.Lock()

            def fake_fetch(url, **kw):  # 진짜 fetch 는 before_send·retries 를 받는다
                with lock:
                    got.append(url)
                return FetchResult(200, "leaf", url)

            n = self._crawl(seeds, 4, fake_fetch, workers=workers)
            return n, sorted(got)

        self.assertEqual(run(1), run(8))

    def test_workers_flag_errors_return_usage_not_traceback(self):
        # CLI 진입점마다 방어를 따로 쓰다 같은 부류가 3회 재발했다 (digest 반복실패)
        self.assertEqual(crawl.main(["prog", "http://a.com/", "--workers"]), 2)
        self.assertEqual(crawl.main(["prog", "http://a.com/", "--workers", "abc"]), 2)
        self.assertEqual(crawl.main(["prog", "http://a.com/", "--workers", "0"]), 2)


class TestCooldownBurn(unittest.TestCase):
    """팝했지만 **요청을 안 보낸** URL 이 도메인 쿨다운을 태우지 않는가.

    design_cooldown-burn.md 계약 2·3. 시간을 재지 않고 **가짜 시계**로 결정적으로 본다 —
    `time.sleep` 이 시계를 흘려보내므로 간격이 정확히 몇 초였는지 단언할 수 있다.
    """

    def _gaps(self, seeds, pages, blocked=(), boom=(), skip=()):
        """a.test 로 **실제로 나간 요청들**의 간격. 예외로 끝난 요청도 나간 것이다."""
        sent = []
        clock = {"t": 1000.0}

        def fake_fetch(url, **kw):  # 진짜 fetch 는 before_send·retries 를 받는다
            sent.append(clock["t"])          # 여기가 발신 시점이다
            if url in boom:
                raise RuntimeError("워커가 죽었다")
            return FetchResult(200, pages.get(url), url)

        robots = mock.Mock()
        robots.allowed = lambda url: url not in blocked
        robots.delay = lambda url: None
        robots.known_delay = robots.delay  # 캐시 조회도 같은 계약을 흉내낸다
        real_store = crawl.Store

        def skipping_store(path):
            store = real_store(path)
            has = store.has
            store.has = lambda u: u in skip or has(u)
            return store

        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.Store", skipping_store), \
             mock.patch("websearch.crawl.time.sleep") as ms, \
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            crawl.crawl(seeds, 10, db_path=":memory:", robots_cache=robots,
                        now=lambda: clock["t"], workers=8)
        return [b - a for a, b in zip(sent, sent[1:])]

    # 링크 순서가 곧 팝 순서다 — 안 보내는 URL 을 먼저 팝하게 해야 태우는지 보인다
    PAGES = {"http://a.test/": '<a href="/x">x</a><a href="/2">2</a>',
             "http://a.test/2": "leaf"}

    def test_store_skipped_url_does_not_burn_cooldown(self):
        gaps = self._gaps(["http://a.test/"], self.PAGES, skip={"http://a.test/x"})
        self.assertEqual(gaps, [1.0], "요청도 안 보낸 URL 이 쿨다운을 태웠다")

    def test_robots_blocked_url_does_not_burn_cooldown(self):
        gaps = self._gaps(["http://a.test/"], self.PAGES, blocked={"http://a.test/x"})
        self.assertEqual(gaps, [1.0], "robots 가 막은 URL 이 쿨다운을 태웠다")

    def test_real_request_does_burn_cooldown(self):
        # 긍정 짝. 위 둘만 있으면 "아무것도 안 태운다" 로도 통과한다
        pages = {"http://a.test/": '<a href="/x">x</a><a href="/2">2</a>',
                 "http://a.test/x": "leaf", "http://a.test/2": "leaf"}
        self.assertEqual(self._gaps(["http://a.test/"], pages), [1.0, 1.0])

    def test_first_ever_request_to_a_domain_may_fail_and_still_holds(self):
        # **빈 상태 경계다.** 그 도메인의 첫 요청이 예외로 끝나면 `_last_fetch` 에 항목이
        # 없다 — `next()` 는 `last is None` 을 "간격 제한 없음" 으로 읽으므로, 시계를
        # 안 걸면 다음 URL 이 **즉시** 나간다. 위 테스트는 홈이 먼저 성공해서 이 경계를
        # 안 지난다 (테스트 phase 갭 탐색, 반복 86)
        pages = {"http://hub.test/": '<a href="http://b.test/1">1</a>'
                                     '<a href="http://b.test/2">2</a>',
                 "http://b.test/2": "leaf"}
        sent = []
        clock = {"t": 1000.0}

        def fake_fetch(url, **kw):  # 진짜 fetch 는 before_send·retries 를 받는다
            if urllib.parse.urlsplit(url).netloc == "b.test":
                sent.append(clock["t"])
            if url == "http://b.test/1":
                raise RuntimeError("첫 요청이 죽었다")
            return FetchResult(200, pages.get(url), url)

        robots = mock.Mock()
        robots.allowed = lambda url: True
        robots.delay = lambda url: None
        robots.known_delay = robots.delay  # 캐시 조회도 같은 계약을 흉내낸다
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms, \
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            crawl.crawl(["http://hub.test/"], 10, db_path=":memory:",
                        robots_cache=robots, now=lambda: clock["t"], workers=8)

        self.assertEqual(len(sent), 2, "b.test 를 두 번 요청해야 간격을 잰다")
        self.assertGreaterEqual(sent[1] - sent[0], 1.0,
                                "첫 요청이 예외로 끝나자 다음 요청이 즉시 나갔다")

    def test_worker_exception_still_holds_the_interval(self):
        # **요청은 나갔고 결과만 터졌다.** 여기서 시계를 안 걸면 다음 요청이 즉시 나간다
        # — 008 리뷰가 경고했고 설계 탐침이 0.310s 로 실증한 구멍이다
        gaps = self._gaps(["http://a.test/"], self.PAGES, boom={"http://a.test/x"})
        for gap in gaps:
            self.assertGreaterEqual(gap, 1.0, "예외 뒤 간격이 깨졌다: %s" % gaps)


class FakeRobots:
    """`RobotsCache` 의 계약만 흉내낸다 (design_crawl-politeness.md 1-1절).

    `delay()` 는 필요하면 받아 오지만 `known_delay()` 는 **이미 받아 둔 것만** 준다 —
    그 차이가 이 테스트들이 재는 것이다.
    """

    def __init__(self, delays=None, blocked=()):
        self._delays = delays or {}       # netloc -> 초
        self._blocked = blocked
        self.loaded = set()               # robots.txt 를 실제로 받은 netloc

    @staticmethod
    def _host(url):
        return urllib.parse.urlsplit(url).netloc

    def allowed(self, url):
        self.loaded.add(self._host(url))
        return url not in self._blocked

    def delay(self, url):
        self.loaded.add(self._host(url))
        return self._delays.get(self._host(url))

    def known_delay(self, url):
        host = self._host(url)
        return self._delays.get(host) if host in self.loaded else None


class TestDelaySurvivesWorkerException(unittest.TestCase):
    """`Crawl-delay` 를 선언한 도메인이 예외 한 번에 기본 1초로 떨어지지 않는가.

    실측(반복 86): `Crawl-delay: 5` 도메인의 첫 요청이 예외 → 다음 간격 **1.0초**.
    `_fetch_one` 이 간격을 반환값으로만 넘겨서, 예외 가지가 `set_delay` 를 못 불렀다.
    """

    # hub 가 b.test 의 URL 둘을 물어다 준다 — b.test 안에서 간격을 재려면 요청이 둘 필요하다
    PAGES = {"http://hub.test/": '<a href="http://b.test/1">1</a>'
                                 '<a href="http://b.test/2">2</a>',
             "http://b.test/1": "leaf", "http://b.test/2": "leaf"}

    def _b_gaps(self, delay, boom=()):
        """b.test 로 **실제로 나간** 요청들의 간격. 예외로 끝난 요청도 나간 것이다."""
        sent = []
        clock = {"t": 1000.0}

        def fake_fetch(url, **kw):
            if urllib.parse.urlsplit(url).netloc == "b.test":
                sent.append(clock["t"])
            if url in boom:
                raise RuntimeError("워커가 죽었다")
            return FetchResult(200, self.PAGES.get(url), url)

        robots = FakeRobots({"b.test": delay})
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms, \
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            crawl.crawl(["http://hub.test/"], 10, db_path=":memory:",
                        robots_cache=robots, now=lambda: clock["t"], workers=8)
        self.assertEqual(len(sent), 2, "b.test 를 두 번 요청해야 간격을 잰다: %s" % sent)
        return [b - a for a, b in zip(sent, sent[1:])]

    def test_declared_delay_survives_a_dead_worker(self):
        gaps = self._b_gaps(5.0, boom={"http://b.test/1"})
        self.assertGreaterEqual(gaps[0], 5.0,
                                "예외 한 번에 Crawl-delay 가 기본 1초로 떨어졌다: %s" % gaps)

    def test_declared_delay_holds_without_any_exception(self):
        # 긍정 짝. 위 테스트만 있으면 "5초를 어디서도 안 쓴다" 를 못 본다
        self.assertEqual(self._b_gaps(5.0), [5.0])

    def test_domain_without_declared_delay_keeps_the_floor(self):
        # 음성 대조. 모르는 값을 지어내지 않는다 — 하한 1초가 답이다
        self.assertEqual(self._b_gaps(None, boom={"http://b.test/1"}), [1.0])


class TestRetriesKeepTheInterval(unittest.TestCase):
    """`fetcher` 의 재시도가 도메인 간격을 지키는가 (design_crawl-politeness.md 2절).

    실측(반복 87 리뷰 탐침): 연결 거부 도메인 1건 → **TCP 연결 3회, 간격 0.0002초**.
    재시도는 `fetcher` 안에서 일어나 `mark_sent` 를 한 번도 안 지나므로 프런티어는
    이것을 요청 1회로 안다.

    여기서 쓰는 가짜 `fetch` 는 **진짜와 같은 순서로 훅을 부른다** — 진짜가 그러는지는
    `tests/test_fetcher.py` 의 `TestSendHook` 이 따로 고정한다.
    """

    PAGES = {"http://hub.test/": '<a href="http://b.test/1">1</a>'
                                 '<a href="http://b.test/2">2</a>',
             "http://b.test/1": "leaf", "http://b.test/2": "leaf"}

    def _b_sends(self, delay=None, failing=()):
        """b.test 로 나간 **모든 시도**의 시각. 재시도도 나간 요청이다."""
        sent = []
        clock = {"t": 1000.0}

        def flaky_fetch(url, before_send=None, retries=fetcher.RETRIES):
            for _ in range(1 + retries):
                if before_send is not None:
                    before_send()
                if urllib.parse.urlsplit(url).netloc == "b.test":
                    sent.append(clock["t"])
                if url not in failing:
                    return FetchResult(200, self.PAGES.get(url), url)
            return FetchResult(0, None, None)

        robots = FakeRobots({"b.test": delay} if delay is not None else {})
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms, \
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = flaky_fetch
            mf.RETRIES = fetcher.RETRIES
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            crawl.crawl(["http://hub.test/"], 10, db_path=":memory:",
                        robots_cache=robots, now=lambda: clock["t"], workers=8)
        return sent

    def test_retries_are_spaced_by_the_domain_interval(self):
        sent = self._b_sends(failing={"http://b.test/1"})
        self.assertEqual(len(sent), 4, "시도 3회 + 다음 URL 1회를 봐야 한다: %s" % sent)
        gaps = [b - a for a, b in zip(sent, sent[1:])]
        for gap in gaps:
            self.assertGreaterEqual(gap, 1.0, "재시도가 간격 없이 몰아쳤다: %s" % gaps)

    def test_next_url_waits_for_the_last_retry_not_the_first(self):
        # 마지막 발신이 아니라 **첫** 발신으로 시계를 걸면, 마지막 재시도 직후 0초 만에
        # 다음 요청이 나간다. 고치면서 여는 구멍이라 따로 잰다
        sent = self._b_sends(failing={"http://b.test/1"})
        self.assertGreaterEqual(sent[-1] - sent[-2], 1.0,
                                "마지막 재시도 직후에 다음 URL 이 나갔다: %s" % sent)

    def test_happy_path_keeps_the_interval_exactly(self):
        # 긍정 짝. 재시도 대기가 성공 경로로 새면 여기가 1.0 을 넘긴다 (계약 9 불변)
        sent = self._b_sends()
        self.assertEqual([b - a for a, b in zip(sent, sent[1:])], [1.0])

    def test_declared_delay_paces_the_retries_too(self):
        sent = self._b_sends(delay=5.0, failing={"http://b.test/1"})
        gaps = [b - a for a, b in zip(sent, sent[1:])]
        for gap in gaps:
            self.assertGreaterEqual(gap, 5.0, "재시도가 Crawl-delay 를 무시했다: %s" % gaps)

    def test_unkeepable_interval_means_no_retry_at_all(self):
        # 설계 2-4절. 상한(30초)을 넘게 요구한 도메인은 어차피 버려진다. 버릴 도메인이라도
        # 이미 나간 요청 뒤에 몰아치면 안 되고, 60초를 자며 워커를 붙들 수도 없다
        sent = self._b_sends(delay=60.0, failing={"http://b.test/1"})
        self.assertEqual(len(sent), 1, "간격을 못 지키는 도메인에 다시 보냈다: %s" % sent)

    def test_keepable_interval_still_retries(self):
        # 긍정 짝. 위 테스트만 있으면 "재시도가 통째로 사라졌다" 로도 통과한다
        self.assertEqual(len(self._b_sends(delay=5.0, failing={"http://b.test/1"})), 4)

    def test_zero_delay_still_gets_the_floor_between_retries(self):
        # 경계값 0. `Crawl-delay: 0` 은 "얼마든지 빨리 와도 된다" 지만 도메인당 1초는
        # 컨셉의 하한이라 내리지 않는다 — 재시도에도 같이 걸려야 한다
        sent = self._b_sends(delay=0.0, failing={"http://b.test/1"})
        gaps = [b - a for a, b in zip(sent, sent[1:])]
        self.assertEqual(len(sent), 4)
        for gap in gaps:
            self.assertGreaterEqual(gap, 1.0, "0초 선언이 하한을 뚫었다: %s" % gaps)

    def test_interval_exactly_at_the_cap_still_retries(self):
        # 경계값. `set_delay` 는 `> MAX_DELAY` 에서 버리고 `_fetch_one` 은
        # `<= MAX_DELAY` 에서 재시도한다 — 두 부등호가 어긋나면 여기가 갈라진다
        self.assertEqual(len(self._b_sends(delay=MAX_DELAY,
                                           failing={"http://b.test/1"})), 4)

    def test_a_hair_over_the_cap_does_not_retry(self):
        # 음성 짝. 위 테스트와 붙어야 경계가 어느 쪽인지 고정된다
        self.assertEqual(len(self._b_sends(delay=MAX_DELAY + 0.1,
                                           failing={"http://b.test/1"})), 1)


class TestUnkeepableDelayFoundOnFailure(unittest.TestCase):
    """예외로 끝난 요청에서 알아낸 간격이 상한을 넘으면 그 도메인을 버리는가.

    성공 가지에는 테스트가 있었지만(`TestCrawlDelayWiring`), 예외 가지는 `_apply_delay` 를
    이번에 처음 지난다 — 초록불인데 새 분기는 아무도 안 밟는 자리였다 (test.md 갭 ⑥).
    """

    PAGES = {"http://hub.test/": '<a href="http://b.test/1">1</a>'
                                 '<a href="http://b.test/2">2</a>'}

    def _run(self, delay):
        sent, err = [], io.StringIO()
        clock = {"t": 1000.0}

        def fake_fetch(url, **kw):
            if urllib.parse.urlsplit(url).netloc == "b.test":
                sent.append(url)
                raise RuntimeError("워커가 죽었다")
            return FetchResult(200, self.PAGES.get(url), url)

        robots = FakeRobots({"b.test": delay})
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms, \
             mock.patch("sys.stderr", err):
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            crawl.crawl(["http://hub.test/"], 10, db_path=":memory:",
                        robots_cache=robots, now=lambda: clock["t"], workers=8)
        return sent, err.getvalue()

    def test_over_the_cap_domain_is_dropped_and_reported(self):
        sent, err = self._run(MAX_DELAY + 30)
        self.assertEqual(len(sent), 1, "버려야 할 도메인에 계속 갔다: %s" % sent)
        self.assertIn("b.test", err)
        self.assertIn("더 가지 않는다", err, "조용히 멈추면 이유를 알 방법이 없다")

    def test_keepable_domain_keeps_going_after_a_failure(self):
        # 긍정 짝. 위 테스트만 있으면 "예외가 나면 무조건 버린다" 로도 통과한다
        sent, err = self._run(5.0)
        self.assertEqual(len(sent), 2)
        self.assertNotIn("더 가지 않는다", err)


class TestNoSendMeansNoClock(unittest.TestCase):
    """훅이 한 번도 안 불렸으면 도메인 시계를 걸지 않는다 (cooldown-burn 계약 1).

    `fetcher.fetch` 는 `Request()` 생성이 실패하면 훅을 못 부르고 돌아온다. 그때
    `_fetch_one` 이 "지금" 을 발신 시각으로 지어내면 **나가지도 않은 요청**이
    쿨다운을 태운다 — robots 가 막은 URL 을 안 태우는 것과 같은 이유다.
    """

    def test_unsendable_url_reports_no_send_time(self):
        allowed, _, sent_at, result = crawl._fetch_one(
            "example.com", FakeRobots(), now=lambda: 1000.0)  # 스킴이 없다
        self.assertTrue(allowed)
        self.assertEqual(result, FetchResult(0, None, None))
        self.assertIsNone(sent_at, "나가지도 않은 요청에 발신 시각이 붙었다")

    def test_a_real_send_does_report_a_time(self):
        # 긍정 짝. 위 테스트만 있으면 "언제나 None" 으로도 통과한다
        with mock.patch("websearch.crawl.fetcher") as mf:
            mf.RETRIES = fetcher.RETRIES
            mf.fetch = sending(lambda url: FetchResult(200, "hi", url))
            _, _, sent_at, _ = crawl._fetch_one(
                "http://a.test/", FakeRobots(), now=lambda: 1000.0)
        self.assertEqual(sent_at, 1000.0)
