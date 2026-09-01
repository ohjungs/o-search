import concurrent.futures
import contextlib
import inspect
import io
import itertools
import os
import signal
import tempfile
import signal
import threading
import time
import unittest
import urllib.parse
from unittest import mock

from websearch import crawl, fetcher, indexer, urls
from websearch import robots as robots_mod
from websearch.frontier import Frontier, DOMAIN_INTERVAL, MAX_DELAY
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
             mock.patch("websearch.crawl.Store", spy_store):
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            # 가짜 시계: sleep 이 시간을 흘려보낸다 — 실제 대기 없이 결정적
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            n = crawl.crawl(seeds, max_pages, db_path=":memory:",
                            robots_cache=robots, now=lambda: clock["t"],
                            workers=workers, deadline=deadline, sleep=ms)
        return n, fetched, ms

    def test_crawls_seed_and_follows_links(self):
        n, fetched, _ = self._run(["http://a.com/"], max_pages=10)
        self.assertEqual(n, 3)
        self.assertIn("http://b.com/", fetched)

    def test_robots_blocked_url_never_fetched(self):
        _, fetched, _ = self._run(["http://a.com/"], max_pages=10)
        self.assertNotIn("http://a.com/blocked", fetched)

    def test_seed_without_scheme_never_reaches_the_network(self):
        """스킴 없는 시드는 **가져올 수 없는 주소**다 — 크롤이 시작될 수조차 없다.

        오늘은 `example.com` 이 fetcher 까지 내려가 `unknown url type:
        ':///robots.txt'` 를 stderr 에 남기고 `수집 0 페이지` **rc 0** 으로 끝난다(실측).
        0건 수집이 성공으로 보고되면 크롤 실패와 구별되지 않는다 — 26(`--max 0`)·
        21 과 같은 값이다.

        **새 계약이 아니라 이미 있는 계약의 구멍이다.** `links.py:30` 이
        발견된 링크에 대해 `http(s)` 만 프런티어에 넣는다고 이미 정해 뒀다.
        시드만 그 가드를 안 지나가는 형제 호출부였다.
        """
        with self.assertRaises(crawl.NoUsableSeedsError):
            self._run(["example.com"], max_pages=3)

    def test_one_good_seed_is_enough(self):
        """**대조군 1 — 경계의 안쪽.** 못 쓰는 시드가 섞였다고 크롤을 죽이지 않는다.

        실측(E): `example.com http://a.com/` 은 오늘도 2페이지를 모은다. 가드가
        "하나라도 이상하면 rc 2" 로 넓어지면 이 단언이 깨진다 — 그것은
        **시드 하나하나를 거절하는** 또 다른 계약이고 여기서 주장한 적 없다.
        """
        n, fetched, _ = self._run(["example.com", "http://a.com/"], max_pages=10)
        self.assertEqual(n, 3)
        self.assertIn("http://a.com/", fetched)

    def test_unfetchable_schemes_are_rejected_fetchable_ones_are_not(self):
        """**대조군 2 — 경계를 양쪽에서 잰다.** 거절 기준은 `links.py` 와 같은 화이트리스트다.

        아래쪽 단언이 핵심이다: `https://nope.com/` 은 **404 로 0페이지**지만
        예외는 아니다. "시드가 거절됐다" 와 "시드를 받아 갔는데 못 가져왔다" 는
        다른 일이고, rc 도 달라야 한다(전자 2, 후자 0). 이 구분이 없으면
        가드는 그냥 "0페이지면 실패" 가 되어 robots 가 정당하게 막은 사이트까지
        오류로 만든다 — 크롤 윤리를 오작동으로 보고하는 쪽이다.
        """
        for bad in ["example.com", "ftp://a.com/", "javascript:alert(1)",
                    "file:///etc/passwd", "mailto:x@a.com"]:
            with self.assertRaises(crawl.NoUsableSeedsError, msg=bad):
                self._run([bad], max_pages=3)
        # 가져올 수 있는 스킴은 못 가져와도 거절이 아니다 — 0페이지 rc 0
        for ok in ["http://nope.com/", "https://nope.com/"]:
            n, _, _ = self._run([ok], max_pages=3)
            self.assertEqual(n, 0, ok)

    def test_no_seed_at_all_is_the_same_hole(self):
        """시드가 0건인 것도 "크롤이 돌 수 없다" 는 같은 이유다.

        `main` 의 `len(argv) < 2` 는 **플래그가 채운 자리를 시드로 착각한다** —
        `crawl --max 1` 은 그 검사를 통과하고 `crawl([], 1)` 을 불러 `수집 0 페이지`
        rc 0 으로 끝났다(실측). 변이(`if seeds and not ascii_seeds`)가 살아남아
        드러난 형제 구멍이라 같은 자리에서 막는다.
        """
        with self.assertRaises(crawl.NoUsableSeedsError):
            self._run([], max_pages=3)

    def test_flags_without_a_seed_are_not_a_successful_crawl(self):
        with mock.patch("websearch.crawl.crawl",
                        side_effect=crawl.NoUsableSeedsError("x")):
            self.assertEqual(crawl.main(["prog", "--max", "1"]), 2)

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

    def test_max_zero_is_rejected_like_workers_and_deadline(self):
        """`--max 0` 은 **요청 0건 · `수집 0 페이지` · rc 0** 이었다(실측).

        같은 파서·같은 관용구를 쓰는 셋 중 `--max` 만 하한이 없었다 —
        `--workers 0`·`--deadline 0` 은 진작 rc 2 다. 0 은 아무도 일부러 치지 않는
        값이고, 낸 결과는 **크롤이 아무것도 못 찾은 것과 구별되지 않는 성공**이다.
        이 저장소가 두 번 닫은 실패 유형이다(`indexer-cli-guard` 의 "없는 DB 를 0건
        성공으로 합치지 않는다" · 25 의 "없는 명령이 rc 0 으로 위장된다").

        **0 을 일괄 금지하는 것이 아니다** — `serve --port 0` 은 "임의 포트" 라는
        뜻이 있어 계속 받는다. 하한은 파서가 아니라 플래그의 뜻이 정한다.
        """
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            for bad in (["--max", "0"], ["--max=0"]):
                self.assertEqual(crawl.main(["prog", "http://a.com/"] + bad), 2, bad)
        crawled.assert_not_called()
        # **대조군은 하한 그 자체다** — `< 1` 을 `< 2` 로 잘못 조이면 위의 단언은
        # 전부 초록인 채 1페이지 크롤만 조용히 죽는다(`--max=3` 은 그것을 못 본다)
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            self.assertEqual(crawl.main(["prog", "http://a.com/", "--max", "1"]), 0)
        self.assertEqual(crawled.call_args[0][1], 1)

    def test_unknown_or_repeated_flags_are_not_seeds(self):
        """**남은 `-` 는 시드가 아니다.** 오타 하나가 크롤 전체를 기본값으로 돌린다.

        실측(고치기 전, 전부 rc **0** · `수집 0 페이지`):

        | 준 인자 | 시드로 샌 것 |
        |---|---|
        | `--maxx 3` (오타) | `['http://a.com/', '--maxx', '3']` |
        | `-max 3` (하이픈 하나) | `['http://a.com/', '-max', '3']` |
        | `--max 3 --max 5` (중복) | `['http://a.com/', '--max', '5']` |

        `--maxx` 는 `--max` 로 안 읽히므로 크롤은 **기본값 100페이지**로 돌고
        운영자는 자기 값이 안 먹었다는 것을 알 방법이 없다. 새어 나간 토큰은
        시드로 요청까지 나갔다 — `unknown url type: ':///robots.txt'`.
        `indexer.main`·`serve.main` 은 `len(args) != 1` 이 이것을 이미 거른다.
        **시드 개수가 가변인 `crawl` 만 셀 수가 없어 구멍이었다.**
        """
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            for bad in (["--maxx", "3"], ["-max", "3"], ["--max", "3", "--max", "5"],
                        ["--max=3", "--max=5"], ["--workers", "2", "--workers", "0"],
                        ["--deadline=5", "--deadline=9"]):
                self.assertEqual(crawl.main(["prog", "http://a.com/"] + bad), 2, bad)
        crawled.assert_not_called()

    def test_several_seeds_still_pass_through(self):
        """**대조군.** 시드는 여럿일 수 있다 — 남은 인자를 세어서 막으면 안 된다."""
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            rc = crawl.main(["prog", "http://a.com/", "http://b.com/", "--max", "3"])
        self.assertEqual(rc, 0)
        self.assertEqual(crawled.call_args[0][0], ["http://a.com/", "http://b.com/"])

    def test_the_guard_rejects_leftover_flags_not_odd_looking_seeds(self):
        """**대조군 2 — 가드의 경계 그 자체다.** 거절하는 것은 `-` 지 스킴이 아니다.

        `if not a.startswith("http")` 로 잘못 넓히는 변이가 위의 단언들을 **전부
        통과한다**(실측). 그 변이는 스킴 없는 시드까지 rc 2 로 만드는데, 그것은
        이 가드가 주장한 적 없는 **다른 계약**(시드 스킴 화이트리스트)이다.
        오늘 `crawl.main` 은 `example.com` 을 `crawl()` 로 넘기고, 왜 못 받았는지는
        `crawl()` 이 시드마다 알린다 — 여기서 가로채면 그 자리가 죽는다.
        """
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            self.assertEqual(crawl.main(["prog", "example.com", "--max", "3"]), 0)
        self.assertEqual(crawled.call_args[0][0], ["example.com"])

    def test_main_returns_2_when_crawl_says_no_seed_was_usable(self):
        """`main` 의 몫은 **잡아서 rc 2 로 바꾸는 것**뿐이다 — 판정은 `crawl()` 이 한다.

        위 대조군(`...not_odd_looking_seeds`)이 고정한 계약은 그대로다: `main` 은
        `example.com` 을 여전히 **그대로 넘긴다**. 스킴을 보는 자리는 `main` 의
        미지 인자 가드가 아니라 시드 루프다 — 두 자리를 합치면 `-` 를 거절하는
        가드와 스킴을 거절하는 가드가 한 덩어리가 되고, 27 의 변이 M4 가
        경고한 **다른 계약**으로 조용히 넓어진다.
        """
        with mock.patch("websearch.crawl.crawl",
                        side_effect=crawl.NoUsableSeedsError("x")):
            self.assertEqual(crawl.main(["prog", "example.com", "--max", "3"]), 2)

    def test_flags_accept_the_equals_form(self):
        """`--name=값` 이 조용히 무시되면 안 된다 — 셋 다 같은 파서를 쓴다.

        무시되면 사용자가 준 값이 시드로 새고 크롤은 **기본값으로 돈다** —
        `--deadline=5` 는 예산 없이, `--max=3` 은 100페이지로 도는 식이다.
        """
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            rc = crawl.main(["prog", "http://a.com/", "--deadline=5", "--max=3",
                             "--workers=2"])
        self.assertEqual(rc, 0)
        args, kwargs = crawled.call_args
        self.assertEqual(args[0], ["http://a.com/"], "플래그가 시드로 샜다")
        self.assertEqual(args[1], 3)
        self.assertEqual(kwargs["workers"], 2)
        self.assertEqual(kwargs["deadline"], 5)

    def test_space_form_still_works(self):
        """**대조군.** `=` 를 받는다고 띄어쓰기 형태가 죽으면 안 된다."""
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            rc = crawl.main(["prog", "http://a.com/", "--deadline", "5", "--max", "3",
                             "--workers", "2"])
        self.assertEqual(rc, 0)
        args, kwargs = crawled.call_args
        self.assertEqual((args[0], args[1]), (["http://a.com/"], 3))
        self.assertEqual((kwargs["workers"], kwargs["deadline"]), (2, 5))

    def test_absent_deadline_is_none_not_the_parser_sentinel(self):
        """`--deadline` 없음은 `crawl(deadline=None)` 이다 — 센티널이 새면 안 된다.

        `--deadline` 은 **없는 것이 정상값(None)** 이라 파서의 오류값(None)과 겹친다.
        가르려고 센티널을 쓰는데 그것을 `crawl()` 까지 흘리면 예산 비교가
        `float > object` 로 죽는다. **이 분기는 여기 말고 아무도 안 밟는다** —
        `deadline = None` 줄을 지우는 변이가 414건을 전부 통과했다(실측).
        """
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            self.assertEqual(crawl.main(["prog", "http://a.com/"]), 0)
        self.assertIsNone(crawled.call_args[1]["deadline"])

    def test_non_ascii_digits_and_python_int_forms_are_not_numbers(self):
        """`int("٨٠")` 은 **80 이다** — 운영자가 친 적 없는 값으로 조용히 돈다.

        `int()` 가 받아 주는 것이 사람이 생각하는 숫자보다 넓다: 아랍-인도 숫자,
        언더스코어 구분자(`8_0`), 앞뒤 공백, 부호. 셋 다 조용히 통과했다(실측).
        `urls.domain_key`(019)·`serve --port ٨٠٨٠`(24)가 **각자 자기 파일에서만**
        막은 그 함정의 세 번째 자리다.

        **파서가 한 자리로 모였다는 증거이기도 하다** — `flags.number_flag` 에서
        `isascii()` 를 떼면 여기와 `test_serve.py` 의 같은 테스트가 **함께** 죽는다.
        한쪽만 죽으면 아직 두 벌이다.
        """
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            for bad in (["--max", "٨٠"], ["--workers", "٨"], ["--deadline", "٦٠"],
                        ["--max=٨٠"], ["--max", "8_0"], ["--max", " 80 "],
                        ["--max", "+80"], ["--workers", "²"],
                        # `--max -5` 는 **이 계획 전까지 rc 0 이었다** — `int("-5")` 가
                        # -5 를 주고 `--max` 에는 `< 1` 검사가 없어 `crawl(seeds, -5)`
                        # 로 갔다. 이제 부호는 파서가 거른다. 여기 없으면 아무도 안 밟는다.
                        ["--max", "-5"], ["--max=-5"]):
                self.assertEqual(crawl.main(["prog", "http://a.com/"] + bad), 2, bad)
        crawled.assert_not_called()

    def test_equals_form_errors_return_usage_not_a_default_run(self):
        # 값이 틀렸으면 기본값으로 조용히 도는 것이 아니라 사용법을 낸다
        with mock.patch("websearch.crawl.crawl", return_value=0) as crawled:
            for bad in ("--deadline=abc", "--deadline=0", "--max=abc", "--workers=0"):
                self.assertEqual(crawl.main(["prog", "http://a.com/", bad]), 2, bad)
        crawled.assert_not_called()

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
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            crawl.crawl(seeds, 10, db_path=":memory:", robots_cache=robots,
                        now=lambda: clock["t"], workers=8, sleep=ms)
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
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            crawl.crawl(["http://hub.test/"], 10, db_path=":memory:",
                        robots_cache=robots, now=lambda: clock["t"], workers=8,
                        sleep=ms)

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
        with mock.patch("websearch.crawl.fetcher") as mf:
            mf.fetch = sending(lambda url: (
                FetchResult(200, pages[url], url) if url in pages
                else FetchResult(404, None, url)))
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            return crawl.crawl(seeds, 10, db_path=":memory:", robots_cache=cache,
                               now=lambda: clock["t"], workers=4, sleep=ms)

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
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            crawl.crawl(["http://hub.test/"], 10, db_path=":memory:",
                        robots_cache=robots, now=lambda: clock["t"], workers=8,
                        sleep=ms)
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
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = flaky_fetch
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            crawl.crawl(["http://hub.test/"], 10, db_path=":memory:",
                        robots_cache=robots, now=lambda: clock["t"], workers=8,
                        sleep=ms)
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
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = flaky_fetch
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            crawl.crawl([self.HUB], 10, db_path=":memory:",
                        robots_cache=robots, now=lambda: clock["t"], workers=8,
                        sleep=ms)
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

        with mock.patch("websearch.crawl.fetcher") as mf:
            mf.fetch = flaky_fetch
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            crawl._fetch_one("http://b.test/1", FakeRobots(),
                             now=lambda: clock["t"], floor=0.0, sleep=ms)

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
             mock.patch("sys.stderr", err):
            mf.fetch = sending(fake_fetch)
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            crawl.crawl(["http://hub.test/"], 10, db_path=":memory:",
                        robots_cache=robots, now=lambda: clock["t"], workers=8,
                        sleep=ms)
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
             mock.patch("websearch.crawl.Store", spy_store), \
             mock.patch("sys.stderr", new_callable=io.StringIO):
            mf.fetch = fake_fetch
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            n = crawl.crawl(["http://a.com/", "http://b.com/"], 5, db_path=":memory:",
                            robots_cache=robots, now=lambda: clock["t"],
                            workers=8, deadline=10, sleep=ms)
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


class TestSleepIsInjected(unittest.TestCase):
    """잠드는 자리도 `now` 와 같은 주입 지점인가 — 계획 33 (`design_clock-injection.md`).

    이 파일의 간격 단언 10곳은 한때 전역 `time.sleep` 을 몽키패치했는데, 그 패치는
    `websearch.crawl` 만이 아니라 **stdlib `time` 모듈을 프로세스 전역·전 스레드로**
    갈아끼운다(설계가 실측). 지금은 전부 `sleep=` 으로 넘긴다. 아래 두 건이 그
    사정거리를 인자 하나로 좁히는 계약이다 — 이게 깨지면 몽키패치가 돌아온다.
    """

    def test_injected_sleep_is_the_only_one_used(self):
        """`sleep=` 을 넘기면 그것만 불리고 전역 `time.sleep` 은 한 번도 안 불린다.

        전역은 **가짜로 바꾸지 않고 진짜를 감싸 세기만 한다** — 동작이 그대로여야
        주입이 샜을 때 "그래도 잤다" 가 보인다. **대기 자리 둘을 다 지난다**:
        재시도 사이가 워커 쪽(`crawl.py:74`)이고, 한 도메인에 URL 둘·`workers=1`
        이라 첫 URL 뒤 쿨다운에서 `frontier.next()` 가 None 을 줘 메인 쪽
        (`crawl.py:179`)도 지난다. 한 자리만 덮으면 다른 자리에 새로 생긴 전역
        대기를 못 잡는다 — 시계를 안 쓰는 고정 대기(`time.sleep(0.1)`)는 행조차
        안 나서 조용히 산다.
        """
        slept, clock = [], {"t": 1000.0}

        def fake_sleep(s):
            slept.append(s)
            clock["t"] += s

        def failing_fetch(url, before_send=None, retries=fetcher.RETRIES):
            for _ in range(1 + retries):
                if before_send is not None:
                    before_send()
            return FetchResult(0, None, None)

        started = time.monotonic()
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("time.sleep", wraps=time.sleep) as global_sleep, \
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = failing_fetch
            mf.RETRIES = fetcher.RETRIES
            crawl.crawl(["http://a.test/1", "http://a.test/2"], 10,
                        db_path=":memory:", robots_cache=FakeRobots(),
                        now=lambda: clock["t"], workers=1, sleep=fake_sleep)
        elapsed = time.monotonic() - started
        self.assertTrue(slept, "넘긴 sleep 이 한 번도 안 불렸다")
        self.assertEqual(global_sleep.call_count, 0,
                         "전역 time.sleep 이 %d번 불렸다 — 주입이 새고 있다"
                         % global_sleep.call_count)
        # **위 두 단언이 못 보는 누수가 하나 있다.** `mock.patch("time.sleep")` 은
        # `time` 모듈의 **속성**을 갈아끼우는데, 기본값 `sleep=time.sleep` 은 def 시점에
        # 진짜 함수 객체를 붙들고 있어 그 패치가 안 닿는다. 그래서 `crawl.py:171` 이
        # `sleep` 을 안 넘겨 `_fetch_one` 이 **기본값으로 새면** `slept` 는 메인 쪽에서
        # 차고 `call_count` 는 0 그대로라 **둘 다 초록인 채로 진짜로 잔다**(실측: 그
        # 변이에서 이 클래스가 0.003초 대신 4.02초 걸리며 OK). 벽시계만이 그것을 본다 —
        # digest `[7]` "기본값이 있는 인자는 특히 위험하다(0 이 아니다)" 가 이 자리다.
        self.assertLess(elapsed, 0.5,
                        "%.2f초 걸렸다 — 어딘가에서 진짜로 잤다(주입이 기본값으로 샌다)"
                        % elapsed)

    def test_default_sleep_is_the_real_one(self):
        # 짝. 위 테스트만 있으면 "안 넘기면 아무데서도 안 잔다" 로도 통과한다 —
        # 기본값이 진짜 `time.sleep` 이라야 아무것도 안 넘긴 오늘 동작이 안 바뀐다
        for fn in (crawl.crawl, crawl._fetch_one):
            self.assertIs(inspect.signature(fn).parameters["sleep"].default,
                          time.sleep, fn.__name__)


class FakeStop:
    """`threading.Event` 의 계약만 흉내낸다 — `is_set()` 과 `wait(t)` (설계 계약 1).

    `wait` 가 **가짜 시계를 흘리고 `False`(시간이 다 됐다)를 준다.** 진짜 `Event` 를
    쓰면 메인 루프의 쿨다운 대기가 벽시계로 1초를 진짜로 자고, 그러면 이 파일의
    가짜 시계가 안 흐르는 채로 실시간만 지나간다.
    """

    def __init__(self, clock):
        self._clock = clock
        self._set = False
        self.waits = []

    def set(self):
        self._set = True

    def is_set(self):
        return self._set

    def wait(self, timeout=None):
        self.waits.append(timeout)
        self._clock["t"] += timeout
        return self._set


class WokenStop(FakeStop):
    """잠든 **동안** 신호가 서는 경우 — `wait` 가 `True`(중단으로 깼다)를 준다.

    `FakeStop` 은 잠들기 전에 이미 서 있던 신호만 흉내낸다. 그것만으로는 계약 3
    (깬 이유를 구별한다)이 진입 검사에 가려져 안 재진다.
    """

    def wait(self, timeout=None):
        self.set()
        return super().wait(timeout)


class TestGracefulInterrupt(unittest.TestCase):
    """중단 신호가 메인 루프를 접는다 — docs/design_graceful-interrupt.md 계약 2·6.

    **스텝 1 은 메인 루프만 본다.** 워커 쪽(재시도 잠을 깨우기·발신 취소)은 스텝 2 라
    여기서 재지 않는다.
    """

    def test_signal_stops_new_submissions_and_reaps_inflight(self):
        """첫 결과 뒤 신호를 세우면 **새 URL 이 안 나가고**, 떠 있던 결과는 DB 에 들어온다.

        `test_inflight_results_are_reaped_when_budget_expires` 와 같은 형태다 —
        예산을 넘기는 대신 신호를 세운다. 신호는 **a.com 저장이 끝난 순간**(메인 스레드,
        루프 꼭대기 재검사 직전)에 선다. b.com 은 그때까지 응답할 수 없으므로 첫
        `futures.wait` 의 `done` 에 못 들어가고 **`inflight` 에 남은 채로** 검사를 맞는다.

        a.com 은 링크를 하나 갖고 있다 — 중단이 안 걸리면 그 링크가 프런티어에서
        올라와 **신호 뒤에 새 요청이 나간다**. 그것이 이 테스트가 재는 것이다.
        """
        released = threading.Event()
        sent = threading.Event()  # b.com 의 요청이 **실제로 나갔다**
        pages = {"http://a.com/": '<a href="/1">1</a>', "http://a.com/1": "one",
                 "http://b.com/": "b"}
        clock = {"t": 1000.0}
        # **진짜 `Event` 를 쓰면 이 테스트가 실패 대신 멈춘다.** 선 이벤트의 `wait` 는
        # 즉시 돌아오는데 가짜 시계는 그때 안 흐른다 — 루프 꼭대기 검사를 지운 변이가
        # 쿨다운이 영영 안 차는 자리를 무한히 돈다(실측). 가짜는 잔 만큼 시계를 흘려
        # 그 변이도 **끝까지 가서 죽는다**
        stop = FakeStop(clock)
        fetched = []

        def fake_fetch(url, before_send=None, **kw):
            fetched.append(url)
            if before_send is not None:
                before_send()
            if url.startswith("http://b.com/"):  # 메인이 꼭대기를 다시 볼 때까지 떠 있는다
                sent.set()
                self.assertTrue(released.wait(10), "b.com 을 풀어 주지 못했다")
            return FetchResult(200, pages[url], url)

        real_store = crawl.Store
        holder = {}

        def spy_store(path):
            store = real_store(path)
            upsert = store.upsert

            def hooked(url, html, status):  # 첫 저장 = a.com — 그 순간 신호가 선다
                upsert(url, html, status)
                if not released.is_set():
                    # **b.com 이 발신한 뒤에** 신호를 세운다. 스텝 2 의 진입 검사(계약 4)
                    # 때문에 아직 요청을 안 낸 워커는 신호를 보면 **정당하게 접는다** —
                    # 그러면 이 테스트가 재려는 "이미 나간 요청의 결과" 가 아예 안 생긴다.
                    # 안 기다리면 전체 스위트 부하에서 간헐적으로 그쪽으로 샜다(실측)
                    self.assertTrue(sent.wait(10), "b.com 이 발신까지 못 갔다")
                    stop.set()
                    released.set()

            store.upsert = hooked
            holder["store"] = store
            return store

        started = time.monotonic()
        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("websearch.crawl.Store", spy_store), \
             mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            mf.fetch = fake_fetch
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            n = crawl.crawl(["http://a.com/", "http://b.com/"], 10, db_path=":memory:",
                            robots_cache=FakeRobots(), now=lambda: clock["t"],
                            workers=8, sleep=ms, stop=stop)
        self.assertEqual(sorted(fetched), ["http://a.com/", "http://b.com/"],
                         "신호 뒤에 새 요청이 나갔다")
        self.assertTrue(holder["store"].has("http://b.com/"),
                        "떠 있던 요청의 결과를 버렸다 — 응답을 받아 놓고 버리면 "
                        "다음 실행이 같은 URL 을 또 때린다")
        self.assertEqual(n, 2, "주운 페이지가 수집 수에 안 들어갔다")
        # 조용히 적게 수집한 것과 "중단으로 끝났다" 는 구별돼야 한다 (계약 6)
        self.assertIn("중단", err.getvalue())
        self.assertLess(time.monotonic() - started, 5.0, "중단이 5초 안에 안 돌아왔다")

    def test_no_signal_keeps_today(self):
        """**대조군.** `stop` 을 안 주면 오늘과 한 글자도 다르면 안 된다."""
        n, fetched, _ = TestCrawl._run(self, ["http://a.com/"], max_pages=10)
        self.assertEqual(n, 3)
        self.assertIn("http://b.com/", fetched)

    def test_main_loop_waits_on_the_signal_not_the_sleep(self):
        """`stop` 을 주면 메인 루프의 쿨다운 대기가 `stop.wait` 로 간다 (계약 2).

        신호는 **잠자는 메인을 깨워야** 하는데 주입된 `sleep` 에 잠들면 못 깬다 —
        `crawl.py:179` 는 워커가 없어 `futures.wait` 처럼 저절로 깨지도 않는
        유일한 자리다(설계서 축3). 한 도메인에 URL 둘·`workers=1` 이라 첫 URL 뒤
        쿨다운에서 `frontier.next()` 가 None 을 줘 그 자리를 반드시 지난다.
        """
        clock = {"t": 1000.0}
        stop = FakeStop(clock)

        def fake_fetch(url, before_send=None, **kw):
            if before_send is not None:
                before_send()
            return FetchResult(200, "x", url)

        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("sys.stderr", io.StringIO()):
            mf.fetch = fake_fetch
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            n = crawl.crawl(["http://a.test/1", "http://a.test/2"], 10,
                            db_path=":memory:", robots_cache=FakeRobots(),
                            now=lambda: clock["t"], workers=1, sleep=ms, stop=stop)
        self.assertEqual(n, 2)
        self.assertEqual(stop.waits, [DOMAIN_INTERVAL],
                         "메인 루프가 stop.wait 로 안 기다렸다 — 신호가 못 깨운다")
        self.assertEqual(ms.call_count, 0,
                         "stop 을 줬는데도 주입된 sleep 에 잠들었다 (%r)"
                         % (ms.call_args_list,))


class TestWorkerSeesTheSignal(unittest.TestCase):
    """워커가 중단을 본다 — design_graceful-interrupt.md 계약 3·4·5.

    **깨우기와 취소는 한 변경이다.** 재시도 잠을 깨우기만 하고 발신을 안 접으면
    `Crawl-delay: 30` 을 선언한 서버에 10초 간격으로 3발이 나간다 — 지금 워커가
    40초를 붙들고 있는 것이 바로 그 예절이다(계획 2절 3번).
    """

    def _retrying_fetch(self, clock, stop, on_first_send=None):
        """b.test 로 **끝까지 실패하는** `_fetch_one` 한 판. `(반환값, 발신들, sleep목)`.

        가짜 `fetch` 는 진짜와 같은 순서로 훅을 부르고, 훅이 던진 예외를 안 잡는다 —
        진짜도 훅 호출이 `try` 밖이라 그대로 나온다(`fetcher.py:36-37`).
        발신 카운터는 **훅이 돌아온 뒤에만** 올라간다: 접힌 시도는 나간 요청이 아니다.
        """
        sends = []

        def flaky_fetch(url, before_send=None, retries=fetcher.RETRIES):
            for _ in range(1 + retries):
                if before_send is not None:
                    before_send()
                sends.append(clock["t"])
                if on_first_send is not None and len(sends) == 1:
                    on_first_send()
            return FetchResult(0, None, None)  # 계속 실패 — 재시도를 다 쓴다

        ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
        with mock.patch("websearch.crawl.fetcher") as mf:
            mf.fetch = flaky_fetch
            mf.RETRIES = fetcher.RETRIES
            out = crawl._fetch_one("http://b.test/1", FakeRobots(),
                                   now=lambda: clock["t"], floor=DOMAIN_INTERVAL,
                                   sleep=ms, stop=stop)
        return out, sends, ms

    def test_signal_before_a_retry_sends_nothing(self):
        """첫 발신 뒤 신호가 서면 **재시도가 안 나간다** (계약 4).

        간격 대기를 건너뛰고 마지막 한 발을 보내는 것은 중단으로 예절을 우회하는 것이다.
        """
        clock = {"t": 1000.0}
        stop = FakeStop(clock)
        (allowed, _, sent_at, result), sends, ms = self._retrying_fetch(
            clock, stop, on_first_send=stop.set)
        self.assertEqual(len(sends), 1, "신호가 섰는데 재시도가 나갔다: %s" % (sends,))
        self.assertIsNone(result, "중단된 시도가 결과처럼 돌아왔다 (계약 5)")
        self.assertTrue(allowed)
        self.assertEqual(sent_at, 1000.0,
                         "이미 나간 발신의 시각을 잃었다 — 도메인 쿨다운이 안 걸린다")

    def test_a_signal_during_the_wait_cancels_the_retry(self):
        """간격 대기 **중에** 신호가 서면 깨어나서 안 보낸다 (계약 3).

        진입 검사(계약 4)는 잠들기 **전에** 이미 서 있던 신호만 본다. 잠든 사이에 선
        신호는 `wait` 의 반환값으로만 알 수 있고, 그 값을 안 보면 워커는 깨자마자
        마지막 한 발을 보낸다 — `Crawl-delay: 30` 을 선언한 서버에 중단이 예절을
        우회해 요청을 밀어 넣는 것이다.
        """
        clock = {"t": 1000.0}
        stop = WokenStop(clock)
        (allowed, _, sent_at, result), sends, _ = self._retrying_fetch(clock, stop)
        self.assertEqual(len(sends), 1,
                         "중단으로 깨고도 재시도를 보냈다: %s" % (sends,))
        self.assertEqual(stop.waits, [DOMAIN_INTERVAL],
                         "간격 대기를 stop.wait 로 안 잤다 — 깰 수가 없다")
        self.assertIsNone(result, "중단된 시도가 결과처럼 돌아왔다 (계약 5)")
        self.assertTrue(allowed)
        self.assertEqual(sent_at, 1000.0,
                         "이미 나간 발신의 시각을 잃었다 — 도메인 쿨다운이 안 걸린다")

    def test_a_retry_past_its_interval_is_still_cancelled(self):
        """간격이 **이미 지난** 재시도도 신호를 보면 안 나간다 (계약 4, `before_send`).

        앞선 시도가 간격보다 오래 걸리면(소켓 타임아웃 10초 > 간격 1초) 잘 일이
        없다. 잠이 없으면 계약 3 의 `wait` 반환값도 없으니, 이 자리를 막는 것은
        `before_send` 진입 검사뿐이다.
        """
        clock = {"t": 1000.0}
        stop = FakeStop(clock)

        def slow_first_send():
            stop.set()
            clock["t"] += fetcher.TIMEOUT  # 소켓이 간격보다 오래 붙들었다

        (allowed, _, sent_at, result), sends, ms = self._retrying_fetch(
            clock, stop, on_first_send=slow_first_send)
        self.assertEqual(len(sends), 1,
                         "간격이 지났다고 신호를 무시하고 보냈다: %s" % (sends,))
        self.assertEqual(stop.waits, [],
                         "간격이 이미 지났는데 잤다 — 이 테스트가 계약 3 을 재고 있다")
        self.assertEqual(ms.call_count, 0, "주입된 sleep 에 잠들었다")
        self.assertIsNone(result, "중단된 시도가 결과처럼 돌아왔다 (계약 5)")
        self.assertTrue(allowed)
        self.assertEqual(sent_at, 1000.0,
                         "이미 나간 발신의 시각을 잃었다 — 도메인 쿨다운이 안 걸린다")

    def test_a_signal_already_up_opens_no_socket(self):
        """진입 검사 — 그 바로 뒤가 `robots.txt` 왕복이다 (계약 4).

        신호 뒤에 **새로 여는 소켓은 0개**다. 재시도 취소만으로는 이 왕복이 안 막힌다.
        """
        clock = {"t": 1000.0}
        stop = FakeStop(clock)
        stop.set()
        robots = FakeRobots()
        with mock.patch("websearch.crawl.fetcher") as mf:
            mf.RETRIES = fetcher.RETRIES
            mf.fetch = sending(lambda url: FetchResult(200, "hi", url))
            allowed, _, sent_at, result = crawl._fetch_one(
                "http://b.test/1", robots, now=lambda: clock["t"],
                floor=DOMAIN_INTERVAL, sleep=None, stop=stop)
        self.assertEqual(robots.loaded, set(), "신호 뒤에 robots.txt 를 새로 받았다")
        self.assertIsNone(result, "신호가 섰는데 페이지 요청이 나갔다")
        self.assertIsNone(sent_at, "나가지도 않은 요청에 발신 시각이 붙었다")
        self.assertTrue(allowed)

    def test_no_signal_keeps_the_retry_interval(self):
        """**대조군.** `stop` 을 줘도 안 세우면 재시도는 오늘 그대로 나간다.

        그리고 그 잠은 `stop.wait` 로 잔다 (계약 2) — 주입된 `sleep` 에 잠들면
        신호가 잠든 워커를 못 깨워 재시도 하나당 최대 `interval` 이 그대로 남는다.
        """
        clock = {"t": 1000.0}
        stop = FakeStop(clock)
        (_, _, _, result), sends, ms = self._retrying_fetch(clock, stop)
        self.assertEqual(len(sends), 1 + fetcher.RETRIES,
                         "신호가 없는데 재시도가 사라졌다: %s" % (sends,))
        self.assertEqual([b - a for a, b in zip(sends, sends[1:])],
                         [DOMAIN_INTERVAL] * fetcher.RETRIES,
                         "재시도 간격이 오늘과 달라졌다: %s" % (sends,))
        self.assertEqual(stop.waits, [DOMAIN_INTERVAL] * fetcher.RETRIES,
                         "워커가 stop.wait 로 안 잤다 — 신호가 못 깨운다")
        self.assertEqual(ms.call_count, 0,
                         "stop 을 줬는데도 주입된 sleep 에 잠들었다 (%r)"
                         % (ms.call_args_list,))
        self.assertEqual(result, FetchResult(0, None, None))

    def test_an_interrupted_attempt_is_not_stored(self):
        """중단된 시도는 **DB 에 안 박힌다** — 그래도 쿨다운과 간격은 건다 (계약 5).

        `FetchResult(0, None, None)` 로 돌려주면 안 받은 페이지가 status 0 으로 박히고,
        다음 실행의 `store.has()` 가 그 URL 을 영영 건너뛴다 — 중단이 프런티어를
        오염시키는 종류다.
        """
        future = concurrent.futures.Future()
        future.set_result((True, 5.0, 1000.0, None))
        store = crawl.Store(":memory:")
        frontier = Frontier()
        saved = crawl._store_result(future, "http://b.test/1", "b.test", store,
                                    frontier, lambda: 2000.0, FakeRobots())
        self.assertEqual(saved, 0)
        self.assertFalse(store.has("http://b.test/1"),
                         "안 받은 페이지가 DB 에 박혔다 — 다음 실행이 이 URL 을 건너뛴다")
        self.assertEqual(frontier.interval("b.test"), 5.0,
                         "중단이 선언된 Crawl-delay 를 잊었다")

    def test_a_running_crawl_hands_the_signal_to_its_workers(self):
        """돌고 있는 크롤이 **워커에게 신호를 넘긴다** — 배선이 없으면 워커는 못 본다.

        위 네 건은 `_fetch_one` 을 직접 부른다. `crawl()` 이 `pool.submit` 에 `stop` 을
        안 실으면 그 넷은 전부 통과하는데 실제 크롤은 오늘 그대로 재시도를 계속한다.
        """
        clock = {"t": 1000.0}
        stop = FakeStop(clock)
        sends = []

        def flaky_fetch(url, before_send=None, retries=fetcher.RETRIES):
            for _ in range(1 + retries):
                if before_send is not None:
                    before_send()
                sends.append(clock["t"])
                stop.set()  # 첫 발신 뒤 Ctrl-C — 재시도가 나가면 안 된다
            return FetchResult(0, None, None)

        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            mf.fetch = flaky_fetch
            mf.RETRIES = fetcher.RETRIES
            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
            n = crawl.crawl(["http://b.test/1"], 10, db_path=":memory:",
                            robots_cache=FakeRobots(), now=lambda: clock["t"],
                            workers=1, sleep=ms, stop=stop)
        self.assertEqual(len(sends), 1,
                         "크롤이 워커에게 신호를 안 넘겼다 — 재시도가 나갔다: %s" % (sends,))
        self.assertEqual(n, 0)
        self.assertIn("중단", err.getvalue())


class TestBudgetFoldsRetries(unittest.TestCase):
    """예산 만료가 **중단 신호와 같은 기제로** 재시도를 접는다 — 계획 35 `deadline-stop`.

    `--deadline` 의 계약은 "예산을 다하면 새 요청을 안 던진다" 인데(`crawl()` 독스트링),
    그 약속이 워커 안에서 깨진다 — 메인 루프가 끊겨도 워커의 재시도는 나간다.
    착수 탐침: `--deadline 2` · 안 답하는 서버 · `Crawl-delay: 30` 에서 종료 70.08초,
    서버가 받은 요청 3건(t=0.05/30.05/60.06). 뒤의 두 건이 **예산 만료 뒤**다.

    두 자리를 **따로** 잰다 — 탐침이 보였듯 한쪽만으로는 1초도 안 줄어든다.
    """

    def test_expired_budget_raises_the_stop_signal(self):
        """예산이 만료되면 `stop` 이 서 있다 — 워커는 그걸 보고 재시도를 접는다 (계약 4).

        떠 있는 요청이 **없는** 자리(쿨다운 대기)에서 만료시킨다 — 아래 `futures.wait`
        자르기와 섞이지 않게 하려는 것이다.

        신호는 **`interrupted` 판정 뒤에** 서야 한다. 앞에 세우면 예산 만료가 중단으로
        보고돼 사용자가 끝난 이유를 잃는다 — 그것이 두 번째 단언이다.
        """
        clock = {"t": 1000.0}
        # 진짜 `Event` 를 쓰면 메인 루프의 쿨다운 대기가 벽시계로 진짜 5초를 잔다
        stop = FakeStop(clock)

        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            mf.fetch = sending(lambda url: FetchResult(200, '<a href="/1">1</a>', url))
            mf.RETRIES = fetcher.RETRIES
            n = crawl.crawl(["http://a.com/"], 10, db_path=":memory:",
                            robots_cache=FakeRobots({"http://a.com": 5.0}),
                            now=lambda: clock["t"], workers=1, deadline=3, stop=stop)
        self.assertEqual(n, 1, "5초 간격 · 예산 3초 — 한 쪽만 살 수 있다")
        self.assertTrue(stop.is_set(),
                        "예산이 만료됐는데 신호가 안 섰다 — 워커의 재시도가 그대로 나간다")
        self.assertIn("예산", err.getvalue(),
                      "예산 만료를 중단으로 보고했다 — 신호를 판정 앞에서 세웠다: %r"
                      % err.getvalue())

    def test_waiting_for_results_never_outlasts_the_budget(self):
        """결과를 기다리는 잠도 **예산 안에서만** 잔다.

        안 자르면 답 없는 서버 하나가 만료 판정을 무한정 미루고, 그동안 워커의 재시도가
        계속 나간다 — 위의 신호를 세워 놔도 **메인이 그 줄에 도달하지 못한다**.

        **벽시계로 잰다.** `futures.wait` 는 주입한 가짜 시계를 안 보고 진짜로 잔다
        (digest `[7]`: mock 이 못 보는 자리를 mock 으로 재면 안 된다).
        """
        stop = threading.Event()
        naps = []
        real_wait = concurrent.futures.wait

        def timed_wait(fs, timeout=None, **kw):
            began = time.monotonic()
            try:
                return real_wait(fs, timeout=timeout, **kw)
            finally:
                naps.append(time.monotonic() - began)

        def hanging_fetch(url, before_send=None, **kw):
            if before_send is not None:
                before_send()
            stop.wait(2.0)  # 답이 없는 서버 — 신호를 봐야 접는다
            return FetchResult(0, None, None)

        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("concurrent.futures.wait", timed_wait), \
             mock.patch("sys.stderr", new_callable=io.StringIO):
            mf.fetch = hanging_fetch
            mf.RETRIES = fetcher.RETRIES
            crawl.crawl(["http://a.com/"], 10, db_path=":memory:",
                        robots_cache=FakeRobots(), now=time.monotonic,
                        workers=1, deadline=0.2, stop=stop)
        self.assertTrue(naps, "결과를 기다리는 자리에 못 갔다 — 재는 것이 없다")
        self.assertLess(max(naps), 1.0,
                        "예산 0.2초인데 %.2f초를 잤다 — 그만큼 만료 판정이 밀린다"
                        % max(naps))

    def test_a_cooling_sibling_domain_never_extends_the_budget_wait(self):
        """쿨다운 중인 **형제 도메인**이 있어도 잠은 예산 안에서 끝난다.

        위 테스트는 도메인이 하나뿐이라 `busy` 가 그것을 빼고 나면
        `seconds_until_ready()` 가 `0.0` 을 주고(`frontier.py`), `or None` 때문에
        **자르기가 "예산을 그대로 쓴다" 가지로만** 간다 — `min(wait_for, left)` 는
        한 번도 안 불린다. 실측: 그 `min` 을 `max` 로 뒤집는 변이가 단위 450건을
        **전부 통과했다**(digest `[7]`: 살아남은 변이가 곧 형제 구멍이다).

        여기는 그 가지를 재는 자리다. 다중 도메인이야말로 실제 크롤의 모습이고,
        형제의 쿨다운(최대 `MAX_DELAY` 30초)을 기다려 버리면 그동안 워커의 재시도가
        나간다 — 계획 35 가 없애려던 바로 그 증상이 다른 문으로 돌아온다.
        """
        stop = threading.Event()
        naps = []
        real_wait = concurrent.futures.wait

        def timed_wait(fs, timeout=None, **kw):
            began = time.monotonic()
            try:
                return real_wait(fs, timeout=timeout, **kw)
            finally:
                naps.append(time.monotonic() - began)

        def fetch(url, before_send=None, **kw):
            if before_send is not None:
                before_send()
            if "b.com" in url:
                # 답하는 형제. 링크를 남겨 b 의 큐를 안 비운다 — 큐가 비면 그 도메인은
                # 쿨다운을 세는 대상에서 빠져 재려는 자리가 사라진다
                return FetchResult(200, '<a href="/2">2</a>'
                                        '<a href="http://a.com/">a</a>', url)
            stop.wait(2.0)          # 안 답하는 서버 — 신호를 봐야 접는다
            return FetchResult(0, None, None)

        with mock.patch("websearch.crawl.fetcher") as mf, \
             mock.patch("concurrent.futures.wait", timed_wait), \
             mock.patch("sys.stderr", new_callable=io.StringIO):
            mf.fetch = fetch
            mf.RETRIES = fetcher.RETRIES
            n = crawl.crawl(["http://b.com/"], 10, db_path=":memory:",
                            robots_cache=FakeRobots({"http://b.com": 5.0}),
                            now=time.monotonic, workers=1, deadline=0.3,
                            stop=stop)
        # 시나리오 가드. b 를 실제로 주웠다는 것이 곧 "b 가 5초 쿨다운 중이고 큐에
        # `/2` 가 남아 있다" 는 증거다 — 이게 아니면 `min` 가지에 도달조차 못 했다
        self.assertEqual(n, 1, "형제 도메인을 안 주웠다 — 쿨다운이 시작되지 않았다")
        self.assertTrue(naps, "결과를 기다리는 자리에 못 갔다 — 재는 것이 없다")
        self.assertLess(max(naps), 1.0,
                        "예산 0.3초인데 %.2f초를 잤다 — 형제의 5초 쿨다운을 기다렸다"
                        % max(naps))


class TestCliTurnsSigintIntoTheSignal(unittest.TestCase):
    """CLI 가 SIGINT 를 `stop` 으로 바꾼다 — design_graceful-interrupt.md 계약 7.

    **진짜 `os.kill(os.getpid(), SIGINT)` 는 안 쓴다.** 핸들러가 제 손으로 SIG_DFL 로
    돌아간 뒤라면 그 신호가 테스트 프로세스를 죽인다. 대신 **설치된 핸들러를 직접
    부른다** — 재는 것은 "신호가 왔을 때 무엇을 하는가" 지 커널 배달이 아니다.
    """

    @contextlib.contextmanager
    def sentinel_handler(self):
        """테스트 프로세스의 SIGINT 핸들러를 아는 값으로 세워 두고 끝나면 되돌린다."""
        def sentinel(signum, frame):  # pragma: no cover — 부르지 않는다
            raise AssertionError("센티널 핸들러가 불렸다")

        previous = signal.signal(signal.SIGINT, sentinel)
        try:
            yield sentinel
        finally:
            signal.signal(signal.SIGINT, previous)

    def test_main_hands_a_stop_event_to_the_crawl(self):
        """`main()` 이 `crawl(stop=...)` 로 신호를 넘긴다 — 안 넘기면 Ctrl-C 는 오늘 그대로다."""
        with self.sentinel_handler(), \
             mock.patch("websearch.crawl.crawl", return_value=0) as crawled, \
             mock.patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(crawl.main(["prog", "http://a.com/"]), 0)
        stop = crawled.call_args.kwargs.get("stop")
        self.assertIsNotNone(stop, "CLI 가 crawl 에 stop 을 안 넘겼다")
        self.assertFalse(stop.is_set())
        self.assertTrue(hasattr(stop, "wait"), "wait(t) 가 없으면 잠을 못 깨운다")

    def test_the_handler_disarms_itself_before_setting_the_signal(self):
        """핸들러는 **SIG_DFL 먼저, `stop.set()` 그다음** — 두 번째 Ctrl-C 는 즉사다.

        순서가 뒤집히면 첫 신호와 둘째 신호 사이에 창이 생긴다. **핸들러가 돌아온
        뒤의 상태로는 그 순서를 못 잰다** — 두 순서 다 끝나고 보면 `SIG_DFL` 이고
        신호도 서 있다(변이 실측: 순서를 뒤집어도 447건이 전부 통과했다). 그래서
        `stop.set()` 이 불리는 **그 순간** 핸들러가 이미 내려갔는지를 본다.
        """
        seen = {}

        def fake_crawl(*args, **kwargs):
            stop = kwargs["stop"]
            real_set = stop.set

            def spy_set():
                seen["armed_at_set"] = signal.getsignal(signal.SIGINT)
                real_set()

            stop.set = spy_set
            signal.getsignal(signal.SIGINT)(signal.SIGINT, None)  # Ctrl-C
            seen["armed"] = signal.getsignal(signal.SIGINT)
            seen["set"] = stop.is_set()
            return 3

        with self.sentinel_handler(), \
             mock.patch("websearch.crawl.crawl", fake_crawl), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = crawl.main(["prog", "http://a.com/"])
        self.assertTrue(seen["set"], "핸들러가 stop 을 안 세웠다 — 크롤이 안 멈춘다")
        self.assertIs(seen["armed"], signal.SIG_DFL,
                      "핸들러가 자기를 안 내렸다 — 두 번째 Ctrl-C 가 안 먹는다")
        self.assertIs(seen.get("armed_at_set"), signal.SIG_DFL,
                      "stop 을 세울 때 핸들러가 아직 우리 것이었다 — 그 사이에 온 "
                      "두 번째 Ctrl-C 는 이미 선 신호를 다시 세울 뿐이라 탈출구가 없다")
        self.assertEqual(rc, 130, "중단인데 rc 0 을 냈다 — `crawl && indexer` 가 계속 돈다")
        self.assertIn("수집 3 페이지", out.getvalue(), "중단이어도 수집 수는 찍는다")

    def test_the_original_handler_comes_back(self):
        """세 갈래(정상·중단·시드 오류) **모두** 원래 핸들러를 복원한다.

        안 하면 한 프로세스에서 여러 번 도는 테스트·래퍼가 오염된다 — 특히 중단 갈래는
        핸들러가 SIG_DFL 로 내려가 있어 복원이 없으면 그대로 남는다.
        """
        def interrupting(*args, **kwargs):
            signal.getsignal(signal.SIGINT)(signal.SIGINT, None)
            return 0

        def raising(*args, **kwargs):
            raise crawl.NoUsableSeedsError("no seeds")

        for name, fake, expected in (("정상", mock.Mock(return_value=0), 0),
                                     ("중단", interrupting, 130),
                                     ("시드 오류", raising, 2)):
            with self.subTest(name), self.sentinel_handler() as sentinel, \
                 mock.patch("websearch.crawl.crawl", fake), \
                 mock.patch("sys.stdout", new_callable=io.StringIO), \
                 mock.patch("sys.stderr", new_callable=io.StringIO):
                rc = crawl.main(["prog", "http://a.com/"])
                self.assertEqual(rc, expected)
                self.assertIs(signal.getsignal(signal.SIGINT), sentinel,
                              "원래 핸들러가 안 돌아왔다")

    def test_an_expired_budget_is_not_an_interrupt(self):
        """예산 만료도 `stop` 을 세운다 — **그래도 rc 0** 이다 (계획 35).

        rc 를 `stop` 으로 가르면 `--deadline` 이 130 을 내고 `crawl && indexer` 가
        예산대로 끝난 크롤 뒤에도 통째로 선다. 130 은 **신호가 왔을 때만**이다.
        """
        def budget_expires(*args, **kwargs):
            kwargs["stop"].set()  # 만료 때 `crawl()` 이 하는 일 그대로
            return 4

        with self.sentinel_handler(), \
             mock.patch("websearch.crawl.crawl", budget_expires), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = crawl.main(["prog", "http://a.com/", "--deadline", "2"])
        self.assertEqual(rc, 0, "예산 만료를 중단으로 읽었다 — `crawl && indexer` 가 선다")
        self.assertIn("수집 4 페이지", out.getvalue())

    def test_a_signal_wins_over_an_expired_budget_in_either_order(self):
        """예산 만료와 SIGINT 가 **함께** 오면 순서와 무관하게 rc **130** 이다.

        예산만(rc 0)·신호만(rc 130)은 각각 위에서 재는데 **겹치는 자리는 아무도 안
        쟀다** — 그래서 겹침에서 0 을 내는 변이가 조용히 통과했다. 실제로 그렇게 되면
        `--deadline` 을 켠 사용자만 Ctrl-C 로 끊은 뒤에도 `crawl && indexer` 가 다음
        단계를 돈다. **순서를 하나만 재면 부족하다** — `signaled.set()` 을
        `if not stop.is_set():` 뒤에 숨기는 변이는 **만료가 먼저** 온 갈래에서만 죽는다
        (만료 갈래에서 일찍 `return 0` 하는 변이는 둘 다 죽인다).
        착수 탐침(`docs/status.md`)이 CLI 서브프로세스로 두 순서를 실측한 값이다 —
        rc 는 둘 다 130 이고 갈리는 것은 문구뿐이다(`중단` / `예산 2초 소진`).
        """
        def signal_then_budget(*args, **kwargs):
            signal.getsignal(signal.SIGINT)(signal.SIGINT, None)  # Ctrl-C 가 먼저
            kwargs["stop"].set()  # 드레인하는 사이 예산도 만료 — `crawl()` 이 하는 그대로
            return 1

        def budget_then_signal(*args, **kwargs):
            kwargs["stop"].set()  # 예산이 먼저 만료
            signal.getsignal(signal.SIGINT)(signal.SIGINT, None)  # 드레인 중 Ctrl-C
            return 1

        for name, fake in (("신호 먼저", signal_then_budget),
                           ("만료 먼저", budget_then_signal)):
            with self.subTest(name), self.sentinel_handler(), \
                 mock.patch("websearch.crawl.crawl", fake), \
                 mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                rc = crawl.main(["prog", "http://a.com/", "--deadline", "2"])
                self.assertEqual(rc, 130, "예산과 신호가 겹쳤는데 rc 0 — 중단 뒤에도 "
                                          "`crawl && indexer` 가 다음 단계를 돈다")
                self.assertIn("수집 1 페이지", out.getvalue(), "중단이어도 수집 수는 찍는다")

    def test_no_signal_still_returns_zero(self):
        """**대조군.** 중단이 없으면 오늘 그대로 rc 0 이다."""
        with self.sentinel_handler(), \
             mock.patch("websearch.crawl.crawl", return_value=2), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(crawl.main(["prog", "http://a.com/"]), 0)
        self.assertIn("수집 2 페이지", out.getvalue())


class TestUnopenableDb(unittest.TestCase):
    """DB 를 열 수조차 없으면 트레이스백이 아니라 안내 한 줄 + rc 1 이다.

    오늘은 `Store(db_path)`(`crawl.py:157`) 의 `sqlite3`·`OSError` 가 그대로 밖으로
    나가 stderr 에 14~16줄을 낸다 — 값(rc 1)은 맞지만 화면이 거짓이다.
    `indexer` 는 같은 상황을 이미 한 줄로 낸다(`indexer.py:264`).
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def test_unopenable_db_raises_store_open_error(self):
        """비 DB 파일 — `sqlite3.DatabaseError` 갈래. 안내가 **경로와 원인**을 부른다."""
        path = os.path.join(self.dir.name, "남의.db")
        with open(path, "wb") as f:
            f.write(b"not a database" * 8)
        with self.assertRaises(crawl.StoreOpenError) as caught:
            crawl.crawl(["http://a.com/"], 1, db_path=path)
        message = str(caught.exception)
        # 경로: 사용자가 준 적 없는 기본값(`data/crawl.db`)일 수 있어 더 필요하다
        self.assertIn(path, message)
        # 원문: 손상·비 DB·락을 뭉뚱그리면 무엇을 고쳐야 하는지 사라진다
        self.assertIn(str(caught.exception.__cause__), message)

    def test_unusable_db_parent_is_the_same_error(self):
        """부모가 일반 파일 — `OSError` 갈래. 같은 예외 하나로 받는다.

        권한과 무관하다(`chmod` 없음) — root 로 돌려도 결과가 같다.
        """
        path = os.path.join(self.dir.name, "파일", "crawl.db")
        with open(os.path.dirname(path), "w"):
            pass
        with self.assertRaises(crawl.StoreOpenError):
            crawl.crawl(["http://a.com/"], 1, db_path=path)

    def test_wording_is_identical_to_indexer(self):
        """**같은 상황을 두 CLI 가 같은 문장으로 부른다** — 설계 계약("글자까지 같다").

        어제까지 이 계약을 붙들고 있는 것은 설계서 한 줄뿐이었다. `crawl.py:178` 과
        `indexer.py:264` 중 **한쪽만 고치면 조용히 갈린다** — 같은 상황에 두 이름이
        붙으면 그건 안내가 아니라 소음이다. 그물(1·2번)·번역(3번)과 달리 이 축은
        **두 모듈을 함께** 돌려야 재진다: 원문(`file is not a database`)도 각자 만든다.
        """
        path = os.path.join(self.dir.name, "남의.db")
        with open(path, "wb") as f:
            f.write(b"not a database" * 8)
        with self.assertRaises(crawl.StoreOpenError) as caught:
            crawl.crawl(["http://a.com/"], 1, db_path=path)
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            self.assertEqual(indexer.main(["prog", path]), 1)
        self.assertEqual(buf.getvalue().strip(), str(caught.exception))

    def test_store_open_error_is_environment_not_usage(self):
        """환경이 안 된 것이라 **rc 1** 이다 — 명령줄 오류 2 와 가른다."""
        buf = io.StringIO()
        with mock.patch("websearch.crawl.crawl",
                        side_effect=crawl.StoreOpenError("DB 를 열 수 없다: x — y")), \
             contextlib.redirect_stderr(buf):
            self.assertEqual(crawl.main(["prog", "http://a.com/"]), 1)
        out = buf.getvalue()
        self.assertNotIn("Traceback", out)
        self.assertEqual(len(out.strip().split("\n")), 1)
