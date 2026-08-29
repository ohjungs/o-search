import contextlib
import io
import itertools
import threading
import time
import unittest
import urllib.parse
from unittest import mock

from websearch import crawl, fetcher, urls
from websearch import robots as robots_mod
from websearch.frontier import DOMAIN_INTERVAL, MAX_DELAY
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
             workers=8, deadline=None):
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
        robots.delay = lambda url: (delays or {}).get(urls.domain_key(url))
        robots.known_delay = robots.delay  # 캐시 조회도 같은 계약을 흉내낸다
        clock = {"t": 1000.0}

        real_store = crawl.Store  # 패치 전에 잡는다 — 안 잡으면 자기를 부른다

        def spy_store(path):  # 저장 열쇠를 밖에서 볼 유일한 손잡이 — :memory: 는 안 남는다
            self.store = real_store(path)
            return self.store

        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms, \
             mock.patch("websearch.crawl.Store", spy_store):
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            # 가짜 시계: sleep 이 시간을 흘려보낸다 — 실제 대기 없이 결정적
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            n = crawl.crawl(seeds, max_pages, db_path=":memory:",
                            robots_cache=robots, now=lambda: clock["t"],
                            workers=workers, deadline=deadline)
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
                 if urls.domain_key(url) == domain]
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

    def test_one_server_paces_itself_across_spellings(self):
        """한 서버는 표기가 갈려도 한 칸이다 — **017 의 RED 를 018 이후의 자로 다시 잰다.**

        `_gaps` 가 이미 `domain_key` 로 묶으므로 이 테스트가 재는 것은 열쇠가 아니라
        **크롤 루프**다: 제출 직전(`crawl.py`)·큐(`frontier.add`)·robots 캐시가
        전부 같은 자를 써야 두 요청이 5초 떨어진다. 고치기 전 실측은 0.000초.

        **018 이 원래 축(대소문자·기본 포트)을 없앴다.** 그 표기들은 이제
        `urls.normalize` 가 URL 이 태어나는 자리에서 접어버려 크롤 루프까지 오지
        않는다 — 여기서 못 재는 것이 **정상이고**, 이 테스트의 옛 판본은 "대문자
        표기가 아예 안 나갔다" 로 정확히 그렇게 실패했다(조용히 통과하지 않았다).
        접히는지는 `TestUrlNormalization` 이, `domain_key` 의 접기 자체는
        `TestDomainKey` 가 단위로 잰다 — 그것은 없어진 게 아니라 **두 번째 방어선**이다.

        남은 살아 있는 축은 **스킴**이다: `http://a.com/` 과 `https://a.com/` 은
        서로 다른 URL 이고(정규화가 접지 않는다 — 접으면 다른 문서를 합치는 것이다)
        같은 서버다.
        """
        with mock.patch.dict(PAGES, {"http://a.com/": "x", "https://a.com/": "y"},
                             clear=True):
            self._run(["http://a.com/", "https://a.com/"], max_pages=10,
                      delays={"a.com": 5.0})
        gaps = self._gaps("a.com")
        self.assertTrue(gaps, "a.com 을 두 번 이상 요청해야 잴 수 있다")
        schemes = {url.partition(":")[0] for url, _ in self.fetch_times}
        self.assertEqual(schemes, {"http", "https"}, "두 스킴이 다 나가야 잴 수 있다")
        for gap in gaps:
            self.assertGreaterEqual(gap, 5.0, "%s" % (self.fetch_times,))

    def test_a_real_port_is_not_paced_by_the_other_server(self):
        # **대조군.** 위가 통과하는 가장 게으른 방법은 전부 한 칸에 넣는 것이다 —
        # 그러면 남의 5초가 여기 걸린다. `perf_crawl` 의 도메인 12개가 이쪽이다
        pages = {"http://b.com:8001/": "x", "http://b.com:8002/": "y"}
        with mock.patch.dict(PAGES, pages):
            self._run(["http://b.com:8001/", "http://b.com:8002/"], max_pages=10,
                      delays={"b.com:8001": 5.0})
        times = [t for _, t in self.fetch_times]
        self.assertEqual(len(times), 2, "%s" % (self.fetch_times,))
        self.assertLess(max(times) - min(times), 5.0,
                        "포트가 다른 서버가 남의 선언을 기다렸다: %s" % (self.fetch_times,))

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
            if urls.domain_key(url) == "b.test":
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
        self._delays = delays or {}       # "스킴://netloc" -> 초
        self._blocked = blocked
        self.loaded = set()               # robots.txt 를 실제로 받은 origin

    _host = staticmethod(robots_mod._base)
    """**진짜를 베끼지 않고 그대로 부른다.**

    베낀 열쇠는 진짜가 바뀌면 조용히 갈린다 — 그러면 이 가짜는 **있을 수 없는
    협력자**가 되고 그 위에서 잰 값은 전부 거짓이다(digest `[6]`: 가짜가 netloc 으로
    캐시해 `http://b.test` 와 `https://b.test` 가 한 칸을 나눠 썼다).
    `_base` 는 네트워크를 안 탄다 — 열쇠를 만드는 순수 함수다.
    """

    def allowed(self, url):
        self.loaded.add(self._host(url))
        return url not in self._blocked

    def delay(self, url):
        self.loaded.add(self._host(url))
        return self._delays.get(self._host(url))

    def known_delay(self, url):
        host = self._host(url)
        return self._delays.get(host) if host in self.loaded else None


class TestABrokenLinkDoesNotEndTheCrawl(unittest.TestCase):
    """**진짜 `RobotsCache` 로** 크롤 루프를 돌린다 (백지 리뷰 지적 #1·#2).

    가짜 robots 는 URL 을 다시 파싱하지 않으므로 이 사고를 표현조차 못 한다 —
    진짜는 `_base` 에서도, `can_fetch` 안에서도 파싱한다. 닫히지 않은 IPv6
    리터럴 하나가 섞이면 예외가 워커에서 나고, 그것을 잡은 복구 경로가 같은 URL 로
    `known_delay` 를 다시 불러 **두 번째 예외**가 크롤 전체를 끝냈다.
    """

    BAD = "http://[::1/x"

    def _crawl(self, seeds, pages):
        cache = robots_mod.RobotsCache()
        cache._fetch_robots = lambda base: (200, "User-agent: *\nAllow: /")  # 네트워크 차단
        clock = {"t": 1000.0}
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms:
            mf.fetch = sending(lambda url: (
                FetchResult(200, pages[url], url) if url in pages
                else FetchResult(404, None, url)))
            mf.RETRIES = fetcher.RETRIES
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            return crawl.crawl(seeds, 10, db_path=":memory:", robots_cache=cache,
                               now=lambda: clock["t"], workers=4)

    def test_a_broken_seed_does_not_end_the_crawl(self):
        n = self._crawl([self.BAD, "http://a.com/"], {"http://a.com/": "ok"})
        self.assertEqual(n, 1, "멀쩡한 씨앗까지 못 받았다")

    def test_a_broken_link_on_a_page_does_not_end_the_crawl(self):
        pages = {"http://a.com/": '<a href="%s">bad</a><a href="/ok">ok</a>' % self.BAD,
                 "http://a.com/ok": "ok"}
        self.assertEqual(self._crawl(["http://a.com/"], pages), 2)


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
            if urls.domain_key(url) == "b.test":
                sent.append(clock["t"])
            if url in boom:
                raise RuntimeError("워커가 죽었다")
            return FetchResult(200, self.PAGES.get(url), url)

        robots = FakeRobots({"http://b.test": delay})
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
                if urls.domain_key(url) == "b.test":
                    sent.append(clock["t"])
                if url not in failing:
                    return FetchResult(200, self.PAGES.get(url), url)
            return FetchResult(0, None, None)

        robots = FakeRobots({"http://b.test": delay} if delay is not None else {})
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


class TestRetryUsesWhatTheFrontierKnows(unittest.TestCase):
    """스킴이 다른 같은 서버 — **재시도가 프런티어보다 빨리 치면 안 된다.**

    `robots.delay(url)` 이 돌려주는 것은 **그 스킴의 robots.txt** 값이다(진짜
    `RobotsCache` 는 `스킴://netloc` 으로 캐시한다). 반면 `Frontier` 는 **netloc**
    단위로 간격을 들고 단조 증가시키므로, `http` 가 선언한 5초가 `https` 에도 걸린다.

    실측(반복 95 리뷰 탐침): URL 사이는 5.000초인데 `https` 재시도는 **1.000초**.
    절대 조건 위반은 아니지만(https 쪽 선언이 없다) **재시도 경로만 URL 사이 경로보다
    덜 조심한다** — 재시도가 나가는 상황은 서버가 이미 아플 때다.

    **보장의 범위를 정확히 적는다: 선언한 스킴을 이미 돌아본 뒤에만 걸린다.**
    프런티어는 아직 안 받아 온 robots.txt 를 알 방법이 없으므로, `https` 가 먼저
    돌면 그때의 바닥값은 하한 그대로다(`test_unseen_scheme_first_still_holds_
    the_floor` 가 그 순서를 고정한다). 닫으려면 투기적 robots.txt 왕복을 하나 더
    내야 하는데, 안 갈 수도 있는 곳에 미리 요청을 보내는 것이야말로 덜 예의 바르다.
    """

    HUB = "http://hub.test/"

    def _sends(self, delays, failing, https_first=False):
        """`b.test` 로 나간 **모든 시도**의 시각. 스킴이 달라도 같은 서버다."""
        links = ['<a href="http://b.test/1">1</a>', '<a href="https://b.test/2">2</a>']
        pages = {self.HUB: "".join(reversed(links) if https_first else links),
                 "http://b.test/1": "leaf", "https://b.test/2": "leaf"}
        sent = []
        clock = {"t": 1000.0}

        def flaky_fetch(url, before_send=None, retries=fetcher.RETRIES):
            for _ in range(1 + retries):
                if before_send is not None:
                    before_send()
                if urls.domain_key(url) == "b.test":
                    sent.append((url, clock["t"]))
                if url not in failing:
                    return FetchResult(200, pages.get(url), url)
            return FetchResult(0, None, None)

        robots = FakeRobots(delays)
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms, \
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = flaky_fetch
            mf.RETRIES = fetcher.RETRIES
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            crawl.crawl([self.HUB], 10, db_path=":memory:",
                        robots_cache=robots, now=lambda: clock["t"], workers=8)
        return sent

    def _retry_gaps(self, sent, url):
        times = [t for u, t in sent if u == url]
        self.assertGreaterEqual(len(times), 2, "재시도 표본이 없다: %s" % sent)
        return [b - a for a, b in zip(times, times[1:])]

    def test_other_scheme_declaration_paces_the_retries(self):
        # http 만 5초를 선언했다. https 쪽 robots 에는 아무 말이 없지만 **서버는 하나다**
        gaps = self._retry_gaps(
            self._sends({"http://b.test": 5.0}, {"https://b.test/2"}),
            "https://b.test/2")
        for gap in gaps:
            self.assertGreaterEqual(
                gap, 5.0, "재시도가 프런티어가 아는 간격보다 빨랐다: %s" % gaps)

    def test_undeclared_domain_keeps_the_plain_floor(self):
        # 대조군. 아무 데도 선언이 없으면 하한 1초 그대로다 — **올리지 않는다**.
        # 이 짝이 없으면 "전부 5초로 재우기" 로도 위 테스트가 통과한다
        gaps = self._retry_gaps(
            self._sends({}, {"https://b.test/2"}), "https://b.test/2")
        for gap in gaps:
            self.assertGreaterEqual(gap, 1.0, "하한이 풀렸다: %s" % gaps)
            self.assertLess(gap, 2.0, "선언이 없는데 간격이 늘었다: %s" % gaps)

    def test_own_declaration_wins_when_it_is_larger(self):
        # 둘 다 선언했으면 **큰 쪽**이다. 바닥을 올리는 것이지 덮어쓰는 것이 아니다
        gaps = self._retry_gaps(
            self._sends({"http://b.test": 5.0, "https://b.test": 7.0},
                        {"https://b.test/2"}),
            "https://b.test/2")
        for gap in gaps:
            self.assertGreaterEqual(gap, 7.0, "자기 선언 7초가 5초로 깎였다: %s" % gaps)

    def test_unseen_scheme_first_still_holds_the_floor(self):
        """**보장의 경계를 적어 둔다.** 안 받아 온 robots.txt 는 프런티어도 모른다.

        `https` 가 먼저 돌면 그때 프런티어가 아는 것은 하한뿐이라 재시도는 1초다.
        고칠 수 있는 종류가 아니다 — 닫으려면 안 갈 수도 있는 곳에 robots.txt 를
        미리 던져야 하고 그쪽이 덜 예의 바르다. **다만 하한은 어떤 순서에서도
        지켜진다** — 여기서 재는 것이 그것이다.
        """
        gaps = self._retry_gaps(
            self._sends({"http://b.test": 5.0}, {"https://b.test/2"}, https_first=True),
            "https://b.test/2")
        for gap in gaps:
            self.assertGreaterEqual(gap, DOMAIN_INTERVAL,
                                    "순서가 바뀌자 하한까지 풀렸다: %s" % gaps)

    def test_a_smaller_floor_cannot_undercut_the_absolute_minimum(self):
        """**하한은 절대 조건이다** — 바닥값을 낮게 넘겨도 1초 아래로 안 내려간다.

        `floor` 를 도입하면서 `DOMAIN_INTERVAL` 보장의 자리가 `_fetch_one` 안에서
        호출부로 옮겨갈 뻔했다. 오늘은 `frontier.interval()` 이 언제나 하한 이상을
        주지만, 그 보장이 **한 곳에만** 있으면 더 작은 값을 넘기는 호출이 하나
        생기는 순간 조용히 사라진다. 여기서 막는다.
        """
        sent = []
        clock = {"t": 1000.0}

        def flaky_fetch(url, before_send=None, retries=fetcher.RETRIES):
            for _ in range(1 + retries):
                if before_send is not None:
                    before_send()
                sent.append(clock["t"])
            return FetchResult(0, None, None)

        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms:
            mf.fetch = flaky_fetch
            mf.RETRIES = fetcher.RETRIES
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            crawl._fetch_one("http://b.test/1", FakeRobots(),
                             now=lambda: clock["t"], floor=0.0)

        gaps = [b - a for a, b in zip(sent, sent[1:])]
        self.assertTrue(gaps, "재시도 표본이 없다 — 잴 대상이 사라졌다")
        for gap in gaps:
            self.assertGreaterEqual(gap, DOMAIN_INTERVAL,
                                    "바닥값 0이 도메인 하한을 뚫었다: %s" % gaps)

    def test_worker_never_touches_the_frontier(self):
        """설계 계약 4 — 바닥값은 **제출 시점에 메인 스레드가** 읽어 넘긴다.

        워커가 `Frontier` 를 만지기 시작하면 계약 3(도메인당 in-flight 1개)에 기대
        생략해 둔 락이 전부 필요해진다. 여기서 막지 않으면 나중에 조용히 깨진다.

        **읽기만 보면 안 된다.** 락이 정말 필요해지는 것은 상태를 바꾸는 쪽이다 —
        `mark_sent`(`_last_fetch`) · `set_delay`(`_delays`·`_queues`) · `add`(`_seen`).
        읽기 둘만 감시하면 누가 워커에서 `mark_sent` 를 부르기 시작해도 그대로 통과한다.
        **진짜 메서드를 감싸서** 센다 — 가짜 반환값으로 바꾸면 밑에서 도는 시나리오가
        달라져 무엇을 쟀는지 알 수 없게 된다.
        """
        watched = ("next", "interval", "mark_sent", "set_delay", "add")
        touched = []

        def watcher(name):
            real = getattr(crawl.Frontier, name)

            def call(self, *args, **kw):
                touched.append((name, threading.current_thread().name))
                return real(self, *args, **kw)
            return mock.patch.object(crawl.Frontier, name, call)

        with contextlib.ExitStack() as stack:
            for name in watched:
                stack.enter_context(watcher(name))
            self._sends({"http://b.test": 5.0}, {"https://b.test/2"})

        seen = {name for name, _ in touched}
        self.assertEqual(seen, set(watched),
                         "감시한 메서드 중 안 불린 것이 있다 — 잴 대상이 사라졌다: %s"
                         % sorted(set(watched) - seen))
        threads = {thread for _, thread in touched}
        self.assertEqual(threads, {"MainThread"},
                         "워커가 프런티어를 만졌다: %s"
                         % sorted({t for n, t in touched if t != "MainThread"}))


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
            if urls.domain_key(url) == "b.test":
                sent.append(url)
                raise RuntimeError("워커가 죽었다")
            return FetchResult(200, self.PAGES.get(url), url)

        robots = FakeRobots({"http://b.test": delay})
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
            "example.com", FakeRobots(), now=lambda: 1000.0,
            floor=DOMAIN_INTERVAL)  # 스킴이 없다
        self.assertTrue(allowed)
        self.assertEqual(result, FetchResult(0, None, None))
        self.assertIsNone(sent_at, "나가지도 않은 요청에 발신 시각이 붙었다")

    def test_a_real_send_does_report_a_time(self):
        # 긍정 짝. 위 테스트만 있으면 "언제나 None" 으로도 통과한다
        with mock.patch("websearch.crawl.fetcher") as mf:
            mf.RETRIES = fetcher.RETRIES
            mf.fetch = sending(lambda url: FetchResult(200, "hi", url))
            _, _, sent_at, _ = crawl._fetch_one(
                "http://a.test/", FakeRobots(), now=lambda: 1000.0,
                floor=DOMAIN_INTERVAL)
        self.assertEqual(sent_at, 1000.0)


class TestUrlNormalization(unittest.TestCase):
    """표기가 여럿이어도 **문서는 하나다** — 계획 018.

    017(`domain_key`)이 모은 것은 **어느 서버인가**였다. 그 뒤에도 URL 자체는
    표기마다 살아 있어서 `Frontier._seen` 도 `pages.url` 도 색인도 표기 수만큼
    행을 가졌다 — 같은 문서를 세 번 받고 세 번 저장한다. 여기서 그것을 잰다.
    """
    _run = TestCrawl._run  # 저장소 관례. 상속하면 TestCrawl 의 6건이 여기서 또 돈다

    def test_three_notations_of_one_document_are_fetched_once(self):
        with mock.patch.dict(PAGES, {"http://a.com/p": "leaf"}, clear=True):
            n, fetched, _ = self._run(
                ["http://a.com/p", "http://A.com/p", "http://a.com:80/p"],
                max_pages=10)
        self.assertEqual(fetched, ["http://a.com/p"])
        self.assertEqual(n, 1)
        self.assertEqual(self.store.count(), 1)

    def test_a_non_default_port_is_still_another_document(self):
        # 대조군 — 정규화가 과하면 여기서 죽는다. 서버가 다르니 문서도 다르다
        pages = {"http://a.com/p": "leaf", "http://a.com:8080/p": "other"}
        with mock.patch.dict(PAGES, pages, clear=True):
            n, fetched, _ = self._run(["http://a.com/p", "http://a.com:8080/p"],
                                      max_pages=10)
        self.assertEqual(sorted(fetched), ["http://a.com/p", "http://a.com:8080/p"])
        self.assertEqual(n, 2)

    def test_empty_path_and_slash_are_one_document(self):
        with mock.patch.dict(PAGES, {"http://a.com/": "leaf"}, clear=True):
            n, fetched, _ = self._run(["http://a.com", "http://a.com/"], max_pages=10)
        self.assertEqual(fetched, ["http://a.com/"])
        self.assertEqual(n, 1)

    def test_percent_case_is_one_document(self):
        with mock.patch.dict(PAGES, {"http://a.com/%EA%B0%80": "leaf"}, clear=True):
            n, fetched, _ = self._run(["http://a.com/%ea%b0%80", "http://a.com/%EA%B0%80"],
                                      max_pages=10)
        self.assertEqual(fetched, ["http://a.com/%EA%B0%80"])
        self.assertEqual(n, 1)

    def test_links_in_a_page_collapse_to_one_url(self):
        # 링크 경로 — 시드 경로와 다른 자리다(`links.extract`). 둘 다 안 막으면 샌다
        page = ('<a href="http://a.com/p">1</a><a href="http://A.com/p">2</a>'
                '<a href="http://a.com:80/p">3</a>')
        with mock.patch.dict(PAGES, {"http://a.com/": page, "http://a.com/p": "leaf"},
                             clear=True):
            n, fetched, _ = self._run(["http://a.com/"], max_pages=10)
        self.assertEqual(fetched, ["http://a.com/", "http://a.com/p"])
        self.assertEqual(n, 2)

    def test_a_redirect_target_is_stored_under_the_normalized_url(self):
        # 세 번째 자리 — 리다이렉트 최종 URL(`crawl.py` `_store_result`).
        # 여기만 안 걸면 `links.extract` 가 링크를 고쳐 주는 바람에 조용히 통과한다
        with mock.patch.dict(REDIRECTS, {"http://a.com/moved": "http://A.com:80/"}), \
             mock.patch.dict(PAGES, {"http://A.com:80/": "leaf"}, clear=True):
            n, _, _ = self._run(["http://a.com/moved"], max_pages=10)
        self.assertEqual(n, 1)
        self.assertTrue(self.store.has("http://a.com/"))
        self.assertFalse(self.store.has("http://A.com:80/"))

    def test_a_fragment_in_a_seed_is_not_a_second_document(self):
        # `links.extract` 만 `urldefrag` 를 갖고 있었다 — 시드는 그 자리를 안 지난다
        # (백지 리뷰 5번). 정규화로 올렸으니 세 경계가 다 같은 답을 낸다
        with mock.patch.dict(PAGES, {"http://a.com/p": "leaf"}, clear=True):
            n, fetched, _ = self._run(["http://a.com/p#top", "http://a.com/p"],
                                      max_pages=10)
        self.assertEqual(fetched, ["http://a.com/p"])
        self.assertEqual(n, 1)
        self.assertTrue(self.store.has("http://a.com/p"))


class TestDeadline(unittest.TestCase):
    """총 크롤 시간 예산 — docs/design_deadline.md.

    예산이 하는 일은 **"덜 보낸다" 뿐**이고 "빨리 보낸다" 는 아니다. 후자가 되는
    순간 `test_budget_never_shortens_the_interval` 이 먼저 죽는다.

    시간은 가짜 시계로만 흐른다 — 잔 만큼이 곧 흐른 시간이라 `ms` 의 인자 합이
    경과 시간이다(`TestCrawl._run` 의 `ms.side_effect`).
    """

    _run = TestCrawl._run
    _gaps = TestCrawlDelayWiring._gaps

    @staticmethod
    def _elapsed(ms):
        return sum(call.args[0] for call in ms.call_args_list)

    def test_short_budget_does_not_fill_max_pages(self):
        # a.com 이 5초를 요구하는데 예산이 3초다 — 셋째 페이지는 살 수 없다
        n, _, ms = self._run(["http://a.com/"], max_pages=3,
                             delays={"a.com": 5.0}, deadline=3)
        self.assertLess(n, 3, "예산이 있는데도 max_pages 를 채웠다")
        # 남은 예산으로 잘랐다. 안 자르면 5초 대기가 통째로 지나 8초가 된다
        self.assertEqual(self._elapsed(ms), 3.0)

    def test_no_deadline_fills_max_pages(self):
        """**대조군.** 예산을 안 주면 오늘과 한 글자도 다르면 안 된다."""
        n, _, ms = self._run(["http://a.com/"], max_pages=3,
                             delays={"a.com": 5.0})
        self.assertEqual(n, 3)
        self.assertGreater(self._elapsed(ms), 3.0, "위 테스트가 재는 대기가 사라졌다")

    def test_budget_never_shortens_the_interval(self):
        """**간격 대조군.** 예산으로 끊긴 크롤도 `Crawl-delay` 를 지킨다.

        예산을 지키려고 간격을 깎는 코드는 RED 다
        (`project.md ## 한도` · `concept.md` 갈림길 1순위).
        """
        # 한 도메인에 4쪽을 두고 5초 간격 · 예산 8초 — 예산 안에 2쪽밖에 못 산다.
        # `max_pages` 로 끊으면 "덜 보냈다" 를 예산이 한 것인지 알 수 없어 넉넉히 준다
        pages = {"http://a.com/": '<a href="/x">x</a><a href="/y">y</a><a href="/z">z</a>',
                 "http://a.com/x": "x", "http://a.com/y": "y", "http://a.com/z": "z"}
        with mock.patch.dict(PAGES, pages, clear=True):
            n, fetched, ms = self._run(["http://a.com/"], max_pages=10,
                                       delays={"a.com": 5.0}, deadline=8)
        gaps = self._gaps("a.com")
        self.assertTrue(gaps, "a.com 을 두 번 이상 요청해야 잴 수 있다")
        for gap in gaps:
            self.assertGreaterEqual(gap, 5.0, "%s" % (self.fetch_times,))
        # 간격을 깎아 예산 안에 더 밀어넣으면 여기가 먼저 죽는다 (8초 / 5초 = 2쪽)
        self.assertEqual(n, 2, "%s" % (fetched,))
        self.assertEqual(self._elapsed(ms), 8.0)

    def test_deadline_flag_errors_return_usage_not_traceback(self):
        # 가드가 회귀하면 `main` 이 진짜 `crawl()` 을 불러 a.com 으로 요청이 나간다.
        # RED 일 때 실네트워크로 나가지 않도록 막는다 — 가드가 살아 있으면 안 불린다
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            for bad in (["--deadline"], ["--deadline", "abc"], ["--deadline", "0"],
                        ["--deadline", "-1"]):
                self.assertEqual(crawl.main(["prog", "http://a.com/"] + bad), 2, bad)
        crawled.assert_not_called()

    def test_inflight_results_are_reaped_when_budget_expires(self):
        """예산 만료로 끊을 때 **떠 있는 요청의 결과를 줍는다** (설계 4절 공백을 메운 결정).

        `ThreadPoolExecutor` 는 `with` 를 나갈 때 그 요청들을 어차피 기다린다 —
        안 주우면 **시간은 치르고 결과만 버리는** 것이고, 다음 실행이 같은 URL 을
        또 때린다. 크롤 윤리로도 손해다.

        시계가 `sleep` 에서만 흐르면 이 상태를 만들 수 없다 — `sleep` 은 inflight 가
        빌 때만 하기 때문이다. 그래서 **a.com 저장이 끝난 순간**(메인 스레드,
        예산 재검사 직전)에 시계를 예산 밖으로 보내고 b.com 을 풀어 준다.
        b 는 그때까지 응답할 수 없으므로 첫 `wait` 의 `done` 에 들어갈 수 없고,
        따라서 **`inflight` 에 남은 채로** 예산 검사를 맞는다.
        """
        released = threading.Event()
        pages = {"http://a.com/": "a", "http://b.com/": "b"}
        clock = {"t": 1000.0}

        def fake_fetch(url, before_send=None, **kw):
            if before_send is not None:
                before_send()
            if url.startswith("http://b.com/"):  # 메인이 예산을 다시 볼 때까지 떠 있는다
                self.assertTrue(released.wait(10), "b.com 을 풀어 주지 못했다")
            return FetchResult(200, pages[url], url)

        robots = mock.Mock()
        robots.allowed = lambda url: True
        robots.delay = lambda url: None
        robots.known_delay = robots.delay

        real_store = crawl.Store
        holder = {}

        def spy_store(path):
            store = real_store(path)
            upsert = store.upsert

            def hooked(url, html, status):  # 첫 저장 = a.com — 그 순간 예산을 넘긴다
                upsert(url, html, status)
                if not released.is_set():
                    clock["t"] += 100
                    released.set()

            store.upsert = hooked
            holder["store"] = store
            return store

        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.time.sleep") as ms, \
             mock.patch("websearch.crawl.Store", spy_store), \
             mock.patch("sys.stderr", new_callable=io.StringIO):
            mf.fetch = fake_fetch
            mf.RETRIES = fetcher.RETRIES
            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
            n = crawl.crawl(["http://a.com/", "http://b.com/"], 5, db_path=":memory:",
                            robots_cache=robots, now=lambda: clock["t"],
                            workers=8, deadline=10)
        self.assertTrue(holder["store"].has("http://b.com/"),
                        "떠 있던 요청의 결과를 버렸다 — 응답을 받아 놓고 버리면 "
                        "다음 실행이 같은 URL 을 또 때린다")
        self.assertEqual(n, 2, "주운 페이지가 수집 수에 안 들어갔다")

    def test_exhausted_budget_is_reported(self):
        # 조용히 적게 수집한 것과 "예산대로 끝났다" 가 구별되지 않으면 안 된다
        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            self._run(["http://a.com/"], max_pages=3, delays={"a.com": 5.0},
                      deadline=3)
        self.assertIn("예산", err.getvalue())
        self.assertIn("3", err.getvalue())
        with mock.patch("sys.stderr", new_callable=io.StringIO) as quiet:
            self._run(["http://a.com/"], max_pages=3, delays={"a.com": 5.0})
        self.assertNotIn("예산", quiet.getvalue())  # 대조군 — 안 끊겼으면 말이 없다
