"""GET /search 의 JSON 과 GET / 의 HTML 화면. 서버를 실제로 띄워 확인한다."""
import io
import json
import os
import re
import socket
import sqlite3
from concurrent import futures
from unittest import mock
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

from html import unescape as html_unescape

from websearch import indexer, serve

PAGES = {
    "http://a.test/1": "<html><title>김치찌개 만들기</title><body>"
                       "<p>김치찌개 는 김치 로 끓인다. 김치 김치 김치</p></body></html>",
    "http://a.test/2": "<html><title>김치 담그기</title><body>"
                       "<p>배추를 절여 김치 를 담근다</p></body></html>",
    "http://a.test/3": "<html><title>Search engine</title><body>"
                       "<p>An engine that indexes documents</p></body></html>",
}


# 20건 = 정확히 2페이지. has_next 를 limit+1 로 판정하므로 경계는 "딱 떨어지는" 마지막 페이지다.
# 낱말 수를 문서마다 달리해 **bm25 점수가 서로 다르게** 만든다 — 본문이 전부 같으면
# 20건이 동점이 되고(측정함: 서로 다른 점수 1/20), 그러면 페이지 경계 단언이 검증하는 것이
# 관련도순이 아니라 sqlite 의 동점 처리 순서가 된다.
MANY_PAGES = {
    "http://p.test/%02d" % i: "<html><title>김치 %02d</title><body>"
                              "<p>%s 를 담근다</p></body></html>" % (i, "김치 " * (i + 1))
    for i in range(20)
}


def build_db(path, pages, index=True):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE pages (url TEXT PRIMARY KEY, html TEXT, status INTEGER)")
    for url, html in pages.items():
        db.execute("INSERT INTO pages VALUES (?, ?, 200)", (url, html))
    db.commit()
    db.close()
    if index:
        indexer.index_pages(path)


class ServeTestCase(unittest.TestCase):
    """임시 DB 로 서버를 띄우고 실제 HTTP 로 때린다. 포트는 0 — 충돌하지 않는다."""

    pages = PAGES  # None 이면 DB 파일 자체를 만들지 않는다
    index = True   # False 면 pages 테이블만 있고 색인 전이다

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = os.path.join(self._tmp.name, "crawl.db")
        if self.pages is not None:
            build_db(self.db, self.pages, self.index)
        self.server = serve.make_server(self.db, port=0)
        self.addCleanup(self.server.server_close)
        # poll_interval 기본 0.5s 는 shutdown() 이 그만큼 기다린다 — 테스트마다 0.5s 씩 붙는다
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01},
                         daemon=True).start()
        self.addCleanup(self.server.shutdown)
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]

    def get(self, path):
        """(상태코드, 파싱된 본문). 4xx·5xx 도 예외 대신 값으로 돌려준다."""
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as resp:
                return resp.status, json.loads(resp.read().decode()), resp.headers
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode()), exc.headers

    def raw(self, path):
        """(상태코드, 본문 문자열, 헤더). HTML 은 파싱하지 않고 바이트 그대로 본다 —
        이스케이프를 검사하는 자리에서 파서를 끼우면 파서가 고쳐준 것을 통과로 읽는다."""
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as resp:
                return resp.status, resp.read().decode(), resp.headers
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode(), exc.headers


class TestSearchEndpoint(ServeTestCase):
    def test_returns_results_for_query(self):
        status, body, _ = self.get("/search?q=" + urllib.parse.quote("김치"))
        self.assertEqual(status, 200)
        self.assertEqual([r["url"] for r in body["results"]],
                         [url for url, _, _ in indexer.search(self.db, "김치")])

    def test_each_result_has_url_title_snippet(self):
        _, body, _ = self.get("/search?q=" + urllib.parse.quote("김치"))
        self.assertTrue(body["results"])
        for hit in body["results"]:
            self.assertEqual(set(hit), {"url", "title", "snippet"})
            self.assertTrue(hit["title"], "제목이 비었다: %r" % hit)

    def test_no_match_is_empty_list_not_error(self):
        status, body, _ = self.get("/search?q=zzzznotfound")
        self.assertEqual(status, 200)
        self.assertEqual(body["results"], [])

    def test_query_echoed_in_response(self):
        _, body, _ = self.get("/search?q=" + urllib.parse.quote("김치"))
        self.assertEqual(body["query"], "김치")

    def test_korean_is_not_escaped_to_ascii(self):
        """\\uXXXX 로 나가면 눈으로 검증할 수 없다 — 설계 계약."""
        with urllib.request.urlopen(
                self.base + "/search?q=" + urllib.parse.quote("김치"), timeout=10) as resp:
            raw = resp.read().decode()
            self.assertIn("김치", raw)
            self.assertNotIn("\\u", raw)

    def test_json_content_type_with_charset(self):
        _, _, headers = self.get("/search?q=" + urllib.parse.quote("김치"))
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")

    def test_missing_query_is_400_not_traceback(self):
        status, body, _ = self.get("/search")
        self.assertEqual(status, 400)
        self.assertIn("error", body)
        self.assertNotIn("Traceback", json.dumps(body))


class TestSchemaVersion(ServeTestCase):
    """응답 스키마의 버전(사양 기능 9). **JSON 다섯 응답 전부**가 갖는다.

    다섯을 따로 재는 이유: 버전은 `_send` 한 곳에서 붙는데, 200 만 재면 그것을
    호출부로 흩어 놓는 변이(오류 응답만 버전을 잃는다)가 안 죽는다.
    값이 **정수**인 것도 계약이다 — 사양이 *"새 버전에서만"* 이라 단조 증가고
    소비자가 `>=` 로 비교한다. `"1"` 이면 그 비교가 조용히 문자열 비교가 된다.
    """

    def q(self, path="/search?q=%EA%B9%80%EC%B9%98"):
        status, body, _ = self.get(path)
        return status, body

    def test_ok_response_carries_version_one(self):
        status, body = self.q()
        self.assertEqual((status, body["version"]), (200, 1))

    def test_bad_request_and_unknown_path_carry_it_too(self):
        # 최상위 키 집합까지 본다 — 버전이 error 를 덮거나 밀어내면 여기서 죽는다
        self.assertEqual(self.q("/search"),
                         (400, {"version": 1, "error": "q 파라미터에 질의 문자열이 필요하다"}))
        status, body = self.q("/no-such-path")
        self.assertEqual((status, body["version"]), (404, 1))

    def test_503_and_500_carry_it_too(self):
        """오류 응답이야말로 기계가 파싱하는 자리다 — 여기서 빠지면 계약이 아니다."""
        for exc, expected in ((FileNotFoundError("db"), 503), (AttributeError("boom"), 500)):
            with self.subTest(status=expected), \
                    mock.patch("websearch.serve._page_hits", side_effect=exc), \
                    mock.patch("sys.stderr", new_callable=io.StringIO):
                status, body = self.q()
            self.assertEqual((status, body["version"]), (expected, 1))

    def test_version_is_an_int_not_a_string(self):
        _, body = self.q()
        self.assertIsInstance(body["version"], int)

    def test_the_html_screen_does_not_carry_it(self):
        """화면에는 안 붙는다 — 계약은 기계가 읽고 화면은 사람이 읽는다.
        `_send_html` 이 `_send` 와 다른 함수라 구조로 성립하지만, 단언이 없으면
        다음 사람이 "일관성" 을 이유로 붙여도 아무도 안 막는다."""
        for path in ("/", "/?q=%EA%B9%80%EC%B9%98"):
            with self.subTest(path=path):
                _, body, _ = self.raw(path)
                self.assertNotIn("version", body.lower())


PASSAGE_Q = "/passages?q=%EA%B9%80%EC%B9%98"  # /passages?q=김치


class TestPassagesEndpoint(ServeTestCase):
    """GET /passages — 근거 문단(계획 48). 계약은 `/search` 와 **한 벌**이다."""

    def test_200_lists_url_title_position_text(self):
        status, body, headers = self.get(PASSAGE_Q)
        self.assertEqual(status, 200, body)
        self.assertIn("application/json", headers["Content-Type"])
        self.assertTrue(body["passages"], "매치가 있는 코퍼스인데 문단이 0건이다")
        for passage in body["passages"]:
            self.assertEqual(set(passage), {"url", "title", "position", "text"})
            # 순번은 정수다 — 문자열이면 소비자의 비교가 조용히 문자열 비교가 된다
            self.assertIsInstance(passage["position"], int)
            self.assertTrue(passage["text"].strip(), "빈 문단은 근거가 아니다")

    def test_response_carries_no_pagination_fields(self):
        """`has_next`·`page` 는 **응답에 없다**(설계 계약) — 없는 것도 계약이다.

        페이지네이션을 안 열었으므로 필드를 두면 소비자가 따라갈 손잡이가 생긴다.
        최상위 키 집합으로 잰다 — 한 필드만 보면 다른 필드가 새는 것을 못 본다.
        """
        _, body, _ = self.get(PASSAGE_Q)
        self.assertEqual(set(body), {"version", "query", "passages"})

    def test_server_does_not_pick_passages_of_its_own(self):
        """문단 로직은 `indexer.passages()` 한 벌이다 — 서버가 다시 고르면 여기서 죽는다."""
        _, body, _ = self.get(PASSAGE_Q)
        self.assertEqual(
            [(p["url"], p["position"], p["text"]) for p in body["passages"]],
            [(url, pos, text) for url, _title, pos, text
             in indexer.passages(self.db, "김치", limit=serve.PASSAGE_LIMIT)])

    def test_title_is_the_document_title_not_a_placeholder(self):
        """갭 탐색(테스트 5) — `title` **값**을 아무 데서도 안 쟀다.

        `"title": ""` 로 바꾸는 변이가 573건 전부 초록으로 살아남았다. 위 200 검사는
        키 **집합**만 보고, `test_server_does_not_pick_passages_of_its_own` 은
        (url·position·text)만 비교한다. 소비자가 근거를 인용할 때 사람에게 보이는
        것은 URL 이 아니라 제목이라 빈 값은 조용한 품질 손실이다.
        """
        _, body, _ = self.get(PASSAGE_Q)
        self.assertEqual({p["url"]: p["title"] for p in body["passages"]},
                         {"http://a.test/1": "김치찌개 만들기",
                          "http://a.test/2": "김치 담그기"})

    def test_query_echoed_in_response(self):
        _, body, _ = self.get(PASSAGE_Q)
        self.assertEqual(body["query"], "김치")

    def test_no_match_is_empty_list_not_error(self):
        status, body, _ = self.get("/passages?q=zzzznotfound")
        self.assertEqual((status, body["passages"]), (200, []))

    def test_missing_query_is_400_not_traceback(self):
        status, body, _ = self.get("/passages")
        self.assertEqual(status, 400, body)
        self.assertNotIn("Traceback", json.dumps(body, ensure_ascii=False))

    def test_long_query_is_400_here_too(self):
        """`_parse` 를 재사용하면 공짜로 참이다 — 안 쓰고 직접 읽는 변이가 여기서 죽는다."""
        status, _, _ = self.get(
            "/passages?q=" + urllib.parse.quote("가" * (serve.MAX_QUERY + 1)))
        self.assertEqual(status, 400)

    def test_page_two_is_400_not_the_same_passages_again(self):
        """페이지를 안 나누므로 **받되 거절한다**(설계 갈림길 2 · 변이 M6).

        조용히 무시하면 `page` 를 올리는 소비자가 같은 문단을 영원히 받는다 —
        그쪽이 400 보다 나쁘다. 200 이 나오면 그 침묵이 계약이 된 것이다.
        """
        status, body, _ = self.get(PASSAGE_Q + "&page=2")
        self.assertEqual(status, 400, body)
        self.assertIn("page", body["error"])

    def test_page_one_is_accepted(self):
        # 거절이 `page` 자체를 막는 것이 되면 안 된다 — 1 은 기본값이자 유일한 유효값이다
        status, _, _ = self.get(PASSAGE_Q + "&page=1")
        self.assertEqual(status, 200)


class TestPassageLimitIsServerSide(ServeTestCase):
    """문단 수는 **서버 상수**다(설계 갈림길 2) — 예산이 클라이언트 손에 있으면 안 된다."""

    pages = MANY_PAGES

    def test_client_cannot_turn_the_knob(self):
        _, body, _ = self.get(PASSAGE_Q)
        self.assertEqual(len(body["passages"]), serve.PASSAGE_LIMIT)
        _, wider, _ = self.get(PASSAGE_Q + "&limit=50")
        self.assertEqual(len(wider["passages"]), serve.PASSAGE_LIMIT)


class TestLongPassageIsTruncated(ServeTestCase):
    """문단 하나가 응답을 통째로 채우지 못한다 — MAX_QUERY·MAX_PAGE 와 같은 자원 상한(변이 M8)."""

    pages = {"http://long.test/1": "<html><title>김치</title><body><p>%s</p></body></html>"
                                   % ("김치 " * 2000)}

    def test_passage_is_cut_at_max(self):
        # **값까지 단언한다** — `serve.MAX_PASSAGE` 로 재면 fixture 가 값을 따라 움직여
        # 값을 바꾸는 변이가 안 죽는다(실측: 2000→500 · 2000→5000 둘 다 557건 전부 초록).
        # 잘라 놓고 상한만 넓히면 응답이 소리 없이 부풀고, 좁히면 근거 문단이 문장
        # 중간에서 끊겨 부르는 쪽 모델에 반 토막이 들어간다 — 둘 다 여기로 와야 한다.
        # fixture 는 8,000자라 넓히는 변이도 «안 잘린 길이 ≠ 2000» 으로 죽는다.
        _, body, _ = self.get(PASSAGE_Q)
        self.assertEqual(len(body["passages"][0]["text"]), 2000,
                         "MAX_PASSAGE 를 바꿨으면 이 줄도 함께 바꾼다")


class TestPassagesMissingDb(ServeTestCase):
    """없는 DB 는 여기서도 503 이다 — 색인을 다시 돌리면 낫는 상태다(사양 디자인 5)."""

    pages = None

    def test_missing_db_is_503_without_internals(self):
        with mock.patch("sys.stderr", new_callable=io.StringIO):
            status, body, headers = self.get(PASSAGE_Q)
        self.assertEqual(status, 503, body)
        self.assertIn("application/json", headers["Content-Type"])
        self.assertEqual(body["error"], "색인이 아직 준비되지 않았다")
        self.assertNotIn(self.db, json.dumps(body, ensure_ascii=False), "DB 경로가 응답으로 샜다")


class TestPassagesBrokenDb(ServeTestCase):
    """손상 DB 는 503 이 아니라 500 이다 — 기다린다고 낫지 않는다."""

    def test_corrupt_db_is_500_not_503(self):
        with open(self.db, "wb") as fh:
            fh.write(b"NOT a sqlite file\n" * 64)
        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            status, body, _ = self.get(PASSAGE_Q)
            logged = err.getvalue()
        self.assertEqual(status, 500, body)
        self.assertEqual(body["error"], "검색 중 오류가 났다")
        self.assertNotIn(self.db, json.dumps(body, ensure_ascii=False), "DB 경로가 샜다")
        self.assertIn("DatabaseError", logged, "500 의 원인이 로그에 안 남았다")


class TestPassagesSchemaVersion(ServeTestCase):
    """`_send` 를 안 쓰고 직접 JSON 을 쓰는 변이(M7)가 여기서 죽는다.

    `/search` 의 다섯을 재는 자리(`TestSchemaVersion`)와 같은 이유로 **오류 응답까지**
    잰다 — 200 만 재면 계약을 호출부로 흩어 놓는 변이가 안 죽는다.
    """

    def test_every_passages_response_carries_version(self):
        for path, expected in ((PASSAGE_Q, 200), ("/passages", 400),
                               (PASSAGE_Q + "&page=2", 400)):
            with self.subTest(path=path):
                status, body, _ = self.get(path)
                self.assertEqual((status, body["version"]), (expected, 1))
        for exc, expected in ((FileNotFoundError("db"), 503),
                              (indexer.StaleIndexError("old"), 503),
                              (AttributeError("boom"), 500)):
            with self.subTest(status=expected, exc=type(exc).__name__), \
                    mock.patch("websearch.indexer.passages", side_effect=exc), \
                    mock.patch("sys.stderr", new_callable=io.StringIO):
                status, body, _ = self.get(PASSAGE_Q)
            self.assertEqual((status, body["version"]), (expected, 1))


class TestPagination(ServeTestCase):
    """20건 색인 = 2페이지. 페이지 경계와 has_next 를 못박는다."""

    pages = MANY_PAGES
    Q = "/search?q=%EA%B9%80%EC%B9%98"  # q=김치

    def urls(self, path):
        status, body, _ = self.get(path)
        self.assertEqual(status, 200, body)
        return [r["url"] for r in body["results"]]

    def every(self):
        return [url for url, _, _ in indexer.search(self.db, "김치", limit=100)]

    def test_page_2_is_the_eleventh_through_twentieth(self):
        self.assertEqual(self.urls(self.Q + "&page=2"), self.every()[10:20])

    def test_missing_page_is_page_1(self):
        self.assertEqual(self.urls(self.Q), self.every()[:10])

    def test_pages_do_not_overlap(self):
        self.assertFalse(set(self.urls(self.Q)) & set(self.urls(self.Q + "&page=2")))

    def test_page_size_is_ten(self):
        self.assertEqual(len(self.urls(self.Q)), 10)

    def test_has_next_true_when_more_remain(self):
        _, body, _ = self.get(self.Q)
        self.assertTrue(body["has_next"])

    def test_has_next_false_on_exactly_full_last_page(self):
        # 20건이 딱 2페이지 — 11번째 유무로 판정하는 방식이 여기서 틀리기 쉽다
        _, body, _ = self.get(self.Q + "&page=2")
        self.assertEqual(len(body["results"]), 10)
        self.assertFalse(body["has_next"])

    def test_page_echoed_in_response(self):
        _, body, _ = self.get(self.Q + "&page=2")
        self.assertEqual(body["page"], 2)

    def test_has_next_is_false_at_the_page_cap(self):
        """상한도 서버가 정한 것이니 마지막이라는 사실도 서버가 알려야 한다.

        `while has_next: page += 1` 로 도는 클라이언트가 상한 다음 장을 달라고 하면
        400 을 맞는다 — 서버가 "다음이 있다"고 해놓고 그 다음을 거부하는 것이다.
        """
        with mock.patch.object(serve, "MAX_PAGE", 1):
            _, body, _ = self.get(self.Q)
        self.assertEqual(len(body["results"]), 10, "뒤에 10건이 더 있는 상황이어야 한다")
        self.assertFalse(body["has_next"], "상한이 1인데 2페이지가 있다고 답했다")


class TestScreenMatchesJson(ServeTestCase):
    """사양 기능 6 — 같은 질의·같은 페이지에서 화면의 결과 순서와 JSON 순서가 완전히 일치한다.

    두 경로가 `_page_hits` 한 벌을 나눠 쓰므로 오늘 **구조상** 참이다. 그런데 그 구조가
    계약인데 재는 단언이 0건이었다 — 화면 쪽만 페이지를 어긋내거나(`page + 1`) 순서를
    뒤집는 변이가 스위트를 하나도 못 죽였다(design_json-contract.md 변이 M13·M14).

    **리스트로 비교한다** — 집합이면 순서를 뒤집는 변이가 안 죽어 "일치"를 안 재게 된다.
    화면에서 URL 을 뽑는 자리는 `<div class="url">` 이다. 링크(`<a href>`)로 뽑으면
    `_safe_href` 가 거른 URL 이 빠져 길이부터 달라진다. 값은 `html.escape` 를 지났으므로
    `html.unescape` 로 되돌려 비교한다.
    **1·2페이지 둘 다** 잰다 — 한 페이지만 재면 페이지를 어긋내는 변이가 안 죽는다.
    """

    pages = MANY_PAGES
    Q = "q=%EA%B9%80%EC%B9%98"  # q=김치

    def screen_urls(self, page):
        status, body, _ = self.raw("/?%s&page=%d" % (self.Q, page))
        self.assertEqual(status, 200)
        return [html_unescape(u) for u in re.findall(r'<div class="url">(.*?)</div>', body)]

    def json_urls(self, page):
        status, body, _ = self.get("/search?%s&page=%d" % (self.Q, page))
        self.assertEqual(status, 200, body)
        return [r["url"] for r in body["results"]]

    def test_screen_and_json_list_the_same_urls_in_the_same_order(self):
        for page in (1, 2):
            with self.subTest(page=page):
                screen = self.screen_urls(page)
                # 빈 목록끼리는 무엇과도 같다 — 실제로 잴 것이 있는 상태인지 먼저 못박는다.
                # 탐침 한 줄(PAGE_SIZE + 1 번째)이 화면에 새는 것도 여기서 죽는다.
                self.assertEqual(len(screen), serve.PAGE_SIZE)
                self.assertEqual(screen, self.json_urls(page))


class TestTiedRanking(ServeTestCase):
    """bm25 동점 문서는 실제 색인에서 흔하다(같은 틀로 찍힌 페이지들).

    2차 정렬 키가 없으면 페이지 사이 순서가 sqlite 의 우연에 걸린다 —
    겹치거나 빠지는 결과가 나올 수 있는 자리다. `ORDER BY bm25(docs), rowid` 로 계약이 된다.
    """

    # 본문·제목이 완전히 같다 = bm25 가 정확히 동점 (실측: 서로 다른 점수 1/12)
    pages = {"http://tie.test/%02d" % i: "<html><title>김치</title><body>"
                                         "<p>김치 를 담근다</p></body></html>"
             for i in range(12)}
    Q = "/search?q=%EA%B9%80%EC%B9%98"

    def test_tied_order_is_repeatable(self):
        # 같은 질의를 두 번 하면 같은 순서여야 한다 — 페이지네이션이 여기 얹혀 있다
        self.assertEqual(self.get(self.Q)[1]["results"], self.get(self.Q)[1]["results"])

    def test_tied_pages_do_not_overlap_or_skip(self):
        _, first, _ = self.get(self.Q)
        _, second, _ = self.get(self.Q + "&page=2")
        got = [r["url"] for r in first["results"]] + [r["url"] for r in second["results"]]
        self.assertEqual(sorted(got), sorted(self.pages), "동점 12건이 겹침·누락 없이 나뉘어야 한다")


class TestTrustBoundary(ServeTestCase):
    """HTTP 는 CLI 두 개에 이은 세 번째 진입점이다 — 같은 방어를 여기서 다시 못박는다.

    (`docs/digest.md` 반복 실패 항목: 진입점마다 검증이 빠진다)
    """

    Q = "/search?q=%EA%B9%80%EC%B9%98"

    def assert_400(self, path):
        status, body, _ = self.get(path)
        self.assertEqual(status, 400, body)
        self.assertIn("error", body)
        self.assertNotIn("Traceback", json.dumps(body))
        return body["error"]

    def test_blank_query_is_400(self):
        self.assert_400("/search?q=%20%20")

    def test_page_not_a_number_is_400_in_plain_korean(self):
        # 파이썬 예외 문구가 그대로 새면 그것도 내부 노출이다
        err = self.assert_400(self.Q + "&page=abc")
        self.assertNotIn("invalid literal", err)
        self.assertIn("page", err)

    def test_page_zero_or_negative_is_400(self):
        for raw in ("0", "-1", "1.5", " 2", "²"):
            with self.subTest(page=raw):
                self.assert_400(self.Q + "&page=" + urllib.parse.quote(raw))

    def test_empty_page_value_falls_back_to_page_1(self):
        # `?page=` 는 parse_qs 가 통째로 버린다 = 없는 것과 같다. 폼이 빈 칸을 보내는
        # 모양이라 거부보다 기본값이 맞다 — 안전한 쪽(1페이지)으로 떨어진다
        status, body, _ = self.get(self.Q + "&page=")
        self.assertEqual((status, body["page"]), (200, 1))

    def test_page_above_cap_is_400(self):
        # 성능이 아니라 자원 고갈 방어 — OFFSET 은 선형으로 자란다(설계 탐침)
        self.assert_400(self.Q + "&page=101")
        self.assert_400(self.Q + "&page=99999")

    def test_page_at_cap_is_allowed(self):
        status, body, _ = self.get(self.Q + "&page=100")
        self.assertEqual(status, 200)
        self.assertEqual(body["results"], [])

    def test_overlong_query_is_400_but_the_limit_itself_passes(self):
        self.assert_400("/search?q=" + urllib.parse.quote("가" * 201))
        status, _, _ = self.get("/search?q=" + urllib.parse.quote("가" * 200))
        self.assertEqual(status, 200)

    def test_unknown_path_is_404_not_traceback(self):
        status, body, _ = self.get(urllib.parse.quote("/없는경로"))
        self.assertEqual(status, 404)
        self.assertNotIn("Traceback", json.dumps(body))

    def test_post_is_refused_without_a_stub_method(self):
        # do_POST 를 정의하지 않으면 stdlib 이 501 을 낸다 — 스텁을 두면 방어가 다시 흩어진다
        req = urllib.request.Request(self.base + "/search", data=b"", method="POST")
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(caught.exception.code, 501)

    def test_hostile_query_strings_do_not_500(self):
        """FTS5 문법·NUL·제어문자는 indexer._fts_query() 가 이미 막는다.

        HTTP 로 **도달 가능해졌으니** 여기서 다시 고정한다 — 막는 자리를 옮기는 게 아니다.
        """
        hostile = ['"', 'OR', '김치 OR "', '*', 'NEAR(a b)', 'a" OR "b', '김치\x00',
                   '김치\x07\x1b', '^김치', 'a AND (b', '"""', '김치*']
        for q in hostile:
            with self.subTest(q=q):
                status, body, _ = self.get("/search?q=" + urllib.parse.quote(q))
                self.assertEqual(status, 200, body)
                self.assertIsInstance(body["results"], list)


class TestConcurrency(ServeTestCase):
    """요청마다 새 sqlite 연결을 여는 것이 설계 결정이다(`docs/design_search-api.md` A안).

    sqlite 연결은 만든 스레드 밖에서 쓸 수 없다. 나중에 "연결을 아끼자" 며 하나로
    끌어올리면 **단일 요청 테스트는 전부 통과한 채** 동시 요청에서만 깨진다.
    재현 대신 계약을 고정한다 — 동시에 때려도 같은 답이 나온다.
    """

    Q = "/search?q=%EA%B9%80%EC%B9%98"

    def test_concurrent_requests_all_answer_alike(self):
        with futures.ThreadPoolExecutor(8) as pool:
            got = [f.result() for f in [pool.submit(self.get, self.Q) for _ in range(8)]]
        for status, body, _ in got:
            self.assertEqual(status, 200, body)
        urls = {tuple(r["url"] for r in body["results"]) for _, body, _ in got}
        self.assertEqual(len(urls), 1, "동시 요청이 서로 다른 결과를 냈다: %s" % urls)
        self.assertTrue(next(iter(urls)), "빈 결과다 — 질의가 아무것도 안 걸렸다")


class TestUnindexedDb(ServeTestCase):
    """수집만 하고 색인을 안 돌린 DB. docs 테이블이 아직 없다.

    **이 200 은 일부러 남긴 것이다**(`docs/design_json-contract.md` 갈림길 D). 사양
    디자인 5 는 *"503 = 색인이 없다"* 라 적었지 *"결과 0건"* 이라 안 적었다.
    crawl → index → serve 순서상 이 상태는 **정상적으로 존재하는 창**이지 고장이 아니다.
    `indexer.search` 는 `indexer.py:183-185` 에서 «docs 가 없다» 를 이미 판별하고서
    빈 목록으로 «매치 0건» 과 합친다 — 503 으로 가르려면 그 자리를 먼저 갈라야 하고,
    그것은 `indexer` 의 모든 호출부를 여는 일이라 계획 47 이 열 때 연다."""

    pages = {}
    index = False

    def test_unindexed_db_is_empty_result_not_500(self):
        status, body, _ = self.get("/search?q=%EA%B9%80%EC%B9%98")
        self.assertEqual((status, body["results"]), (200, []))


class TestMissingDb(ServeTestCase):
    """DB 파일 자체가 없다 — 색인을 아직 안 돌렸거나 운영 실수다.

    상태 코드를 읽는 것은 사람이 아니라 **인프라**다. 색인을 다시 돌리면 낫는 상태에
    500(재시도 안 함)은 틀린 신호라 **503** 을 낸다(사양 디자인 5).
    본문은 고정 문구다 — `str(exc)` 는 `FileNotFoundError(db_path)`, 곧 DB 경로 그 자체다.
    """

    pages = None

    def test_missing_db_is_503_without_internals(self):
        status, body, headers = self.get("/search?q=%EA%B9%80%EC%B9%98")
        self.assertEqual(status, 503, body)
        # 오류도 JSON 이다(사양 디자인 5) — 503 을 _send_html 로 내면 여기서 죽는다
        self.assertIn("application/json", headers["Content-Type"])
        self.assertEqual(body["error"], "색인이 아직 준비되지 않았다")
        raw = json.dumps(body, ensure_ascii=False)
        self.assertNotIn("Traceback", raw)
        self.assertNotIn(self.db, raw, "DB 경로가 응답으로 샜다")

    def test_503_is_logged_even_though_access_log_is_off(self):
        """응답에서 뺀 원인은 운영자가 볼 수 있는 곳에 남아야 한다.

        접근 로그를 끄려고 log_message 를 덮으면 log_error 도 같이 죽는다
        (stdlib 의 log_error 가 log_message 로 넘긴다). 그러면 클라이언트는
        "색인이 없다", 운영자는 **어느 DB 가** 없는지 아무것도 못 본다.
        """
        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            status, _, _ = self.get("/search?q=%EA%B9%80%EC%B9%98")
            logged = err.getvalue()
        self.assertEqual(status, 503)
        self.assertIn("색인 없음", logged, "503 이 stderr 에 한 줄도 안 남았다")
        # 한 줄이 남은 것으로는 부족하다. 본문이 고정 문구라 원인은 로그에만 있다.
        # `%r` 을 고정 문자열로 바꿔도 위 단언은 초록이고, 그 순간 이 503 은
        # 어느 DB 를 가리키는지 아무도 모르는 503 이 된다.
        self.assertIn("FileNotFoundError", logged, "503 의 원인이 로그에 안 남았다")

    def test_normal_request_stays_out_of_the_log(self):
        # 접근 로그는 계속 꺼져 있어야 한다 — 위 수정이 stdlib 기본 로그를 되살리면 안 된다
        build_db(self.db, PAGES)
        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            self.get("/search?q=%EA%B9%80%EC%B9%98")
        self.assertEqual(err.getvalue(), "")


class TestDriftedIndex(ServeTestCase):
    """옛 정의로 만든 docs 가 남아 있다 — `indexer.search` 가 StaleIndexError 를 던진다.

    DB 없음과 원인은 다르지만 운영자가 할 일은 같다(색인을 다시 돌린다). 그래서 같은 503 이다.
    이 상태를 HTTP 로 재는 단언은 여기가 처음이다 — 그전에는 `serve` 가
    `StaleIndexError` 라는 이름을 아예 모른 채 500 에 접어 넣고 있었다.
    """

    OLD_SCHEMA = ("CREATE VIRTUAL TABLE docs "
                  "USING fts5(title, body, url UNINDEXED, tokenize='unicode61')")

    def setUp(self):
        super().setUp()
        db = sqlite3.connect(self.db)
        db.execute("DROP TABLE docs")
        db.execute(self.OLD_SCHEMA)  # 코드만 새것으로 갈아탄 상황
        db.commit()
        db.close()

    def test_drifted_index_is_503(self):
        status, body, headers = self.get("/search?q=%EA%B9%80%EC%B9%98")
        self.assertEqual(status, 503, body)
        self.assertIn("application/json", headers["Content-Type"])
        self.assertEqual(body["error"], "색인이 아직 준비되지 않았다")
        self.assertNotIn(self.db, json.dumps(body, ensure_ascii=False), "DB 경로가 샜다")

    def test_drifted_index_is_503_on_the_html_path(self):
        status, body, _ = self.raw("/?q=%EA%B9%80%EC%B9%98")
        self.assertEqual(status, 503)
        self.assertNotIn(self.db, body, "DB 경로가 화면으로 샜다")


class TestProgrammingErrorStays500(ServeTestCase):
    """503 은 «색인이 없다» 만의 값이다 — 넓히면 프로그래밍 오류가 재시도 대상이 된다.

    503 절이 생기는 순간 두 경로의 500 을 재는 단언이 **0건**이 된다. `except Exception`
    을 통째로 503 으로 바꿔도 스위트가 전부 초록인 상태였다(설계 변이표 M5).
    500 은 "고쳐야 한다", 503 은 "기다렸다 다시 걸어라" 다 — 인프라가 그 둘로 갈린다.
    """

    def test_programming_error_is_500_not_503(self):
        with mock.patch("websearch.serve._page_hits", side_effect=AttributeError("boom")), \
                mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            status, body, _ = self.get("/search?q=%EA%B9%80%EC%B9%98")
            logged = err.getvalue()
        self.assertEqual(status, 500, body)
        self.assertEqual(body["error"], "검색 중 오류가 났다")
        # 앞의 `/` 까지 단언한다 — `"search 실패"` 로만 재면 경로를 안 찍는 옛 문구가
        # 부분문자열로 통과한다(리뷰 4 변이 Y4 가 564건 전부 초록이었다)
        self.assertIn("/search 실패", logged, "500 이 stderr 에 한 줄도 안 남았다")
        self.assertIn("AttributeError", logged, "500 의 원인이 로그에 안 남았다")

    def test_the_500_log_names_which_of_the_two_json_paths_broke(self):
        """500 의 유일한 흔적이 로그라, 두 경로가 사다리를 나눠 쓰면 **구별돼야** 한다.

        `/search` 쪽 단언만으로는 안 된다 — 경로를 안 찍어도 그 문구는 남는다.
        갈라지는 것을 재는 자리는 여기다.
        """
        with mock.patch("websearch.indexer.passages", side_effect=AttributeError("boom")), \
                mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            status, body, _ = self.get("/passages?q=%EA%B9%80%EC%B9%98")
            logged = err.getvalue()
        self.assertEqual(status, 500, body)
        self.assertEqual(body["error"], "검색 중 오류가 났다")
        self.assertIn("/passages 실패", logged, "/passages 의 500 이 어느 경로인지 안 남겼다")
        self.assertNotIn("/search 실패", logged, "터진 것은 /passages 인데 /search 라고 적었다")

    def test_programming_error_is_500_on_the_html_path(self):
        with mock.patch("websearch.serve._page_hits", side_effect=AttributeError("boom")), \
                mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            status, body, _ = self.raw("/?q=%EA%B9%80%EC%B9%98")
            logged = err.getvalue()
        self.assertEqual(status, 500)
        self.assertIn("검색 화면 실패", logged, "화면 500 이 stderr 에 한 줄도 안 남았다")
        self.assertNotIn("Traceback", body)


class TestBrokenDbStays500(ServeTestCase):
    """DB 파일이 **깨졌거나 못 읽는다** — 503 이 아니라 500 이다.

    위 두 단언은 `_page_hits` 를 mock 으로 갈아 `AttributeError` 를 던지게 한다. 그래서
    못박힌 것은 *"코드가 틀렸을 때 500"* 뿐이고 **실물 DB 상태로 500 을 재는 단언은
    0건**이었다 — 503 튜플에 `sqlite3.DatabaseError` 를 더하는 변이(*"DB 오류도 인프라니
    재시도"*)가 스위트를 하나도 못 죽인다. 손상은 기다린다고 낫지 않는다. 503 은
    *"색인을 다시 돌리면 낫는다"* 는 약속이라 거기 넣으면 인프라가 영영 재시도한다.

    설계서 §1 은 이 자리를 `PermissionError` 라 적었는데 **실물은 아니다**(탐침으로 측정):
    `sqlite3.connect` 가 `OperationalError('unable to open database file')` 로 바꿔 던진다.
    `DatabaseError` 의 하위라 잡히는 자리는 같지만, 예외 **이름**으로 짜는 단언은 빗나간다.
    """

    def corrupt(self):
        with open(self.db, "wb") as fh:
            fh.write(b"NOT a sqlite file\n" * 64)

    def test_corrupt_db_is_500_not_503(self):
        self.corrupt()
        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            status, body, _ = self.get("/search?q=%EA%B9%80%EC%B9%98")
            logged = err.getvalue()
        self.assertEqual(status, 500, body)
        self.assertEqual(body["error"], "검색 중 오류가 났다")
        self.assertNotIn(self.db, json.dumps(body, ensure_ascii=False), "DB 경로가 샜다")
        self.assertIn("DatabaseError", logged, "500 의 원인이 로그에 안 남았다")

    def test_corrupt_db_is_500_for_a_tokenless_query_too(self):
        """위 단언은 **`q=김치` 한 갈래에만** 걸려 있었다 — 계약의 두 번째 구멍이다.

        `indexer.search` 의 조기 반환(`if not match`)이 DB 를 여는 자리 **앞**에 있으면
        `%01` 처럼 토큰이 안 나오는 질의는 DB 를 아예 안 본 채 `[]`→**200** 으로 나간다.
        같은 파일, 같은 고장인데 질의어에 따라 500 과 200 이 갈리면 계약이 아니다.
        """
        self.corrupt()
        with mock.patch("sys.stderr", new_callable=io.StringIO):
            status, body, _ = self.get("/search?q=%01")
        self.assertEqual(status, 500, body)
        self.assertEqual(body["error"], "검색 중 오류가 났다")
        self.assertNotIn(self.db, json.dumps(body, ensure_ascii=False), "DB 경로가 샜다")

    def test_corrupt_db_screen_is_500_too(self):
        """두 경로의 튜플은 한 벌이어야 한다(설계 갈림길 C) — 한쪽만 넓히는 변이가 있다."""
        self.corrupt()
        with mock.patch("sys.stderr", new_callable=io.StringIO):
            status, body, _ = self.raw("/?q=%EA%B9%80%EC%B9%98")
        self.assertEqual(status, 500)
        self.assertIn("검색 중 오류가 났다", body)
        self.assertNotIn(self.db, body, "DB 경로가 화면으로 샜다")

    @unittest.skipIf(os.geteuid() == 0, "root 는 파일 권한을 무시한다")
    def test_unreadable_db_is_500_not_503(self):
        """읽을 수 없는 DB 는 사람이 `chmod` 를 해야 낫는다 — 재시도가 아니라 고칠 일이다."""
        os.chmod(self.db, 0o000)
        self.addCleanup(os.chmod, self.db, 0o600)
        with mock.patch("sys.stderr", new_callable=io.StringIO):
            status, body, _ = self.get("/search?q=%EA%B9%80%EC%B9%98")
        self.assertEqual(status, 500, body)
        self.assertEqual(body["error"], "검색 중 오류가 났다")


class TestSlowClient(ServeTestCase):
    def test_idle_connection_does_not_hold_a_thread_forever(self):
        """요청 라인을 끝내지 않는 연결은 스레드를 무기한 점유한다(슬로로리스).

        OFFSET 990 짜리 질의(7ms)를 상한으로 막으면서 이쪽을 열어두면 균형이 안 맞는다.
        """
        handler = self.server.RequestHandlerClass
        # 실제로 나가는 값을 단언한다 — 아래에서 짧게 갈아끼우고 재는 건 기제가 도는지만 본다.
        # **`is not None` 은 값을 안 붙든다** — 10→600 으로 넓히는 변이가 557건 전부
        # 초록으로 지나갔다(실측). 이 값이 곧 공격자가 스레드 하나를 공짜로 붙잡는 초다.
        self.assertEqual(handler.timeout, 10,
                         "핸들러 소켓 타임아웃이 REQUEST_TIMEOUT 10초가 아니다"
                         "(stdlib 기본은 None — 무한정 붙잡는다)")
        with mock.patch.object(handler, "timeout", 0.3):
            sock = socket.create_connection(self.server.server_address, timeout=10)
            self.addCleanup(sock.close)
            sock.sendall(b"GET /sea")  # 줄을 끝내지 않는다
            self.assertEqual(sock.recv(64), b"", "유휴 연결이 끊기지 않았다 — 스레드가 잡혀 있다")


# 크롤한 남의 문서에서 온 문자열이 HTML 로 다시 나가는 자리들이다.
# 아래 XSS 페이지들은 **엔티티로 인코딩된 원본**을 쓴다 — extract_text() 가 그것을
# 풀어서 제목·본문 텍스트로 만드는 것을 실측 확인했다(2026-08-27):
#   <title>&lt;script&gt;…</title>  →  '<script>…'
# 즉 크롤한 페이지가 우리 화면에 <script> 를 문자 그대로 넣을 수 있다. 가상의 위협이 아니다.
XSS_PAGES = {
    'http://evil.test/"><b>': "<html><head><title>&lt;script&gt;alert(1)&lt;/script&gt; 김치</title>"
                              "</head><body><p>&quot;&gt;&lt;img src=x onerror=alert(1)&gt;"
                              " 김치 김치 김치</p></body></html>",
    "javascript:alert(1)": "<html><head><title>김치 스킴</title></head>"
                           "<body><p>김치 김치</p></body></html>",
    # 멀쩡한 URL 하나가 있어야 "링크가 통째로 사라지는" 변이를 잡을 수 있다.
    "http://ok.test/kimchi": "<html><head><title>평범한 김치 문서</title></head>"
                            "<body><p>김치 김치 김치</p></body></html>",
}

# 홈·결과 두 화면에 공통으로 요구하는 것 (concept.md:49-54 디자인 축)
def assert_page_basics(t, body):
    t.assertIn('<html lang="ko"', body, "lang 이 없으면 스크린리더가 언어를 못 고른다")
    t.assertIn('name="viewport"', body, "viewport meta 가 없으면 360px 에서 가로 스크롤이 난다")
    t.assertNotIn("<script", body.lower(), "JS 0KB 계약 위반 (concept.md:50)")
    # 스크린리더 사용자가 화면을 훑는 첫 수단이 제목 계층이다. h2 만 있고 h1 이
    # 없으면 결과 목록이 무엇에 속한 목록인지 말해주는 것이 아무것도 없다.
    t.assertIn("<h1", body, "h1 이 없다 — 제목 계층이 h2 부터 시작한다")


class TestHomePage(ServeTestCase):
    """GET / — 검색 홈. concept.md:49 의 첫 번째 화면."""

    def test_home_is_html_not_404(self):
        status, body, headers = self.raw("/")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        assert_page_basics(self, body)

    def test_home_has_search_input_with_accessible_name(self):
        _, body, _ = self.raw("/")
        self.assertIn('name="q"', body)
        # 라벨이든 aria-label 이든 접근 가능한 이름이 있어야 한다 (concept.md:53)
        self.assertTrue("aria-label" in body or "<label" in body,
                        "검색 입력에 접근 가능한 이름이 없다")
        self.assertIn('role="search"', body)

    def test_empty_q_is_home_not_400(self):
        """홈은 q 가 없는 것이 정상이다 — _parse() 의 400 을 그대로 물려받으면 안 된다."""
        for path in ("/", "/?q=", "/?q=%20%20"):
            status, body, _ = self.raw(path)
            self.assertEqual(status, 200, path)
            self.assertIn('name="q"', body)

    def test_form_is_get_so_keyboard_alone_works(self):
        """폼 GET 이면 탭+엔터로 끝난다. JS 가 붙는 순간 이 단언이 깨진다."""
        _, body, _ = self.raw("/")
        self.assertIn('method="get"', body.lower())


class TestResultsPage(ServeTestCase):
    """GET /?q=… — 결과 페이지. concept.md:49 의 두 번째 화면."""

    def test_results_render_title_url_snippet(self):
        status, body, _ = self.raw("/?q=" + urllib.parse.quote("김치"))
        self.assertEqual(status, 200)
        assert_page_basics(self, body)
        hits = indexer.search(self.db, "김치")
        self.assertTrue(hits)
        for url, title, _snippet in hits:
            self.assertIn(url, body, "URL 이 화면에 없다")
            self.assertIn(title, body, "제목이 화면에 없다")

    def test_query_is_echoed_into_the_input(self):
        _, body, _ = self.raw("/?q=" + urllib.parse.quote("김치"))
        self.assertIn('value="김치"', body)

    def test_no_match_says_so_and_keeps_the_searchbox(self):
        status, body, _ = self.raw("/?q=zzzznotfound")
        self.assertEqual(status, 200)
        self.assertIn('name="q"', body, "결과가 없어도 검색창은 남아야 한다")

    def test_search_endpoint_still_returns_json(self):
        """회귀 방어 — HTML 을 붙이면서 이미 나가 있는 JSON 계약을 깨지 않는다."""
        status, body, headers = self.get("/search?q=" + urllib.parse.quote("김치"))
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertTrue(body["results"])

    def test_responses_carry_nosniff_and_html_carries_a_csp(self):
        """이스케이프가 이 계획에서 가장 공들인 자리다. 두 헤더가 그 뒤를 받친다 —
        한 줄이 뚫렸을 때 CSP 가 인라인 스크립트 실행을 막고, nosniff 는 브라우저가
        JSON 을 HTML 로 재해석하는 경로를 닫는다. JS 0KB 라 CSP 가 잃을 것이 없다."""
        for path in ("/", "/?q=" + urllib.parse.quote("김치"),
                     "/search?q=" + urllib.parse.quote("김치"), PASSAGE_Q):
            with self.subTest(path=path):
                _, _, headers = self.raw(path)
                self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff", path)
        _, _, headers = self.raw("/")
        csp = headers.get("Content-Security-Policy", "")
        self.assertIn("script-src 'none'", csp, "CSP 가 없다 — 이스케이프가 단일 방어선이다")

    def test_bad_page_param_is_400_html_without_traceback(self):
        status, body, headers = self.raw("/?q=%EA%B9%80%EC%B9%98&page=0")
        self.assertEqual(status, 400)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertNotIn("Traceback", body)

    def test_overlong_query_is_400_not_500(self):
        status, _, _ = self.raw("/?q=" + urllib.parse.quote("가" * 201))
        self.assertEqual(status, 400)


class TestHtmlEscaping(ServeTestCase):
    """이스케이프는 타협하지 않는 영역이다 (plan_search-ui.md 8절).

    질의어·제목·URL·스니펫 **네 자리 전부**를 본다. 한 자리만 막으면 나머지 셋이 열린다.
    """

    pages = XSS_PAGES

    def rendered(self, path):
        """결과 페이지 본문. **먼저 진짜 렌더됐는지 못박는다.**

        이 전제가 없으면 아래 단언들은 화면이 아예 없을 때(404 JSON)도 통과한다 —
        실제로 그랬다: 구현 전 RED 확인에서 이스케이프 테스트 3개가 공허하게 통과했다.
        "나쁜 것이 없다"는 "화면이 없다"로도 참이 되므로, 부정 단언에는 반드시
        긍정 전제가 붙어야 한다.
        """
        status, body, _ = self.raw(path)
        self.assertEqual(status, 200, body)
        self.assertIn('name="q"', body, "결과 페이지가 렌더되지 않았다")
        self.assertIn("evil.test", body, "위험한 문서가 결과에 안 실렸다 — 검사할 것이 없다")
        return body

    def test_query_is_escaped_in_input_and_title(self):
        payload = '"><script>alert(1)</script>'
        body = self.rendered("/?q=" + urllib.parse.quote(payload) + "%20" + urllib.parse.quote("김치"))
        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertIn("&lt;script&gt;", body)
        # 속성 자리 탈출: value="…" 를 닫고 나가는 따옴표가 살아 있으면 안 된다
        self.assertNotIn('value=""><', body)

    def test_crawled_title_and_snippet_are_escaped(self):
        body = self.rendered("/?q=" + urllib.parse.quote("김치"))
        self.assertNotIn("<script>alert(1)</script>", body,
                         "크롤한 문서의 제목이 스크립트로 실행된다")
        self.assertNotIn("<img src=x onerror=alert(1)>", body,
                         "크롤한 문서의 본문이 스니펫으로 실행된다")

    def test_crawled_url_is_escaped_in_href_and_text(self):
        body = self.rendered("/?q=" + urllib.parse.quote("김치"))
        self.assertNotIn('"><b>', body, "URL 이 href 속성을 탈출한다")

    def test_benign_url_actually_becomes_a_link(self):
        """이 파일의 XSS 단언은 전부 assertNotIn 이다 — **_safe_href 가 무조건
        None 을 돌려줘도 전부 통과한다.** 링크가 사라지는 변이를 아무도 못 잡는다.
        위생 검사에는 반드시 긍정 짝이 있어야 한다(리뷰 지적)."""
        body = self.rendered("/?q=" + urllib.parse.quote("김치"))
        self.assertIn('href="http://ok.test/', body,
                      "멀쩡한 http URL 이 링크가 되지 않았다 — 허용 목록이 전부를 막고 있다")

    def test_hostile_query_strings_do_not_500_on_the_html_path(self):
        """`/search` 에만 있던 단언을 화면 경로에도 건다.

        digest.md 의 반복 실패 항목이 "진입점마다 검증이 빠진다" 인데, 화면은
        CLI 둘·JSON 에 이은 **네 번째 진입점**이다. 같은 목록을 여기서 다시 친다.
        """
        hostile = ['"', 'OR', '김치 OR "', '*', 'NEAR(a b)', 'a" OR "b', '김치\x00',
                   '김치\x07\x1b', '^김치', 'a AND (b', '"""', '김치*']
        for q in hostile:
            with self.subTest(q=q):
                status, body, _ = self.raw("/?q=" + urllib.parse.quote(q))
                self.assertEqual(status, 200, body[:200])
                self.assertIn('name="q"', body)

    def test_scheme_allowlist_needs_an_actual_scheme(self):
        """`"http".split(":", 1)[0]` 은 `"http"` 다 — 콜론이 없는 문자열이
        허용 목록을 통과했다. 상대 경로가 크롤 결과에 섞이면 링크가 서버 자신을
        가리킨다. 신뢰 경계라 짧아도 닫는다(리뷰 지적)."""
        for bad in ("http", "https", "javascript", "//evil.test/x", "/relative"):
            with self.subTest(url=bad):
                self.assertIsNone(serve._safe_href(bad))
        for good in ("http://a.test/", "https://a.test/", "HTTPS://A.test/"):
            with self.subTest(url=good):
                self.assertEqual(serve._safe_href(good), good)

    def test_javascript_scheme_url_is_not_linked(self):
        """html.escape() 만으로는 못 막는다 — javascript: 에는 &, <, " 가 하나도 없다.

        크롤러가 http/https 만 담는다는 성질에 기대지 않는다. 렌더 시점에 확인한다.
        """
        body = self.rendered("/?q=" + urllib.parse.quote("김치"))
        self.assertNotIn('href="javascript:', body)


class TestHtmlPathFailsSafely(ServeTestCase):
    """DB 가 없다 — JSON 쪽은 TestMissingDb 가 이미 못박았는데
    화면 경로는 오류 문구를 **사람에게 보여주는** 자리라 새기 더 쉽다.

    화면도 같은 503 을 낸다(설계 갈림길 C) — 원인이 같은데 상태가 다르면
    운영자가 한 사고를 두 값으로 본다. 사람이 읽는 문구가 달라질 뿐이다.
    지금은 고정 문자열을 쓰지만, 단언이 없으면 다음 사람이 `str(exc)` 로 바꿔도
    아무도 못 잡는다. 흘리면 안 되는 것을 흘리지 않는다고 여기서 고정한다.
    """

    pages = None

    def test_503_page_leaks_neither_traceback_nor_db_path(self):
        status, body, headers = self.raw("/?q=%EA%B9%80%EC%B9%98")
        self.assertEqual(status, 503)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn("색인이 아직 준비되지 않았다", body)
        self.assertNotIn("Traceback", body)
        self.assertNotIn("sqlite3", body.lower())
        self.assertNotIn(self.db, body, "DB 경로가 화면으로 샜다")

    def test_503_page_still_lets_you_search_again(self):
        """막다른 화면을 주지 않는다 — 오류 페이지에도 검색창이 남는다."""
        _, body, _ = self.raw("/?q=%EA%B9%80%EC%B9%98")
        self.assertIn('name="q"', body)

    def test_error_page_keeps_what_you_typed_and_does_not_steal_focus(self):
        """오류 페이지가 `SEARCHBOX % ("", " autofocus")` 였다 — 두 가지가 틀렸다.
        방금 친 질의어를 버려서 다시 치게 만들고, autofocus 가 스크린리더 사용자를
        오류 문구를 지나쳐 입력창으로 끌고 간다(serve.py:104 주석이 결과 페이지에
        대해 직접 금지한 것과 같은 상황이다)."""
        _, body, _ = self.raw("/?q=%EA%B9%80%EC%B9%98")
        self.assertIn('value="김치"', body, "오류 페이지가 입력한 질의어를 버렸다")
        self.assertNotIn("autofocus", body, "오류 문구를 지나쳐 입력창으로 끌려간다")

    def test_503_page_logs_its_cause(self):
        """화면 경로에도 같은 넓은 `try` 가 있는데 로그 단언은 JSON 쪽에만 있었다.

        사람에게 보여줄 수 없어서 뺀 원인이 로그에도 없으면 아무 데도 없다.
        `_do_html` 의 log_error 를 통째로 지워도 여기 오기 전까지는 다 초록이었다.
        """
        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            status, _, _ = self.raw("/?q=%EA%B9%80%EC%B9%98")
            logged = err.getvalue()
        self.assertEqual(status, 503)
        self.assertIn("색인 없음", logged, "화면 503 이 stderr 에 한 줄도 안 남았다")
        self.assertIn("FileNotFoundError", logged, "503 의 원인이 로그에 안 남았다")

    def test_home_still_renders_without_a_db(self):
        """홈은 색인을 읽지 않는다 — DB 가 죽어도 첫 화면은 떠야 한다."""
        status, body, _ = self.raw("/")
        self.assertEqual(status, 200)
        self.assertIn('name="q"', body)


class TestPagerUi(ServeTestCase):
    """결과 화면의 이전/다음. **주소창을 편집할 줄 아는 사람만 11번째 결과를 보면 안 된다.**

    20건 색인 = 정확히 2페이지. `TestPagination` 이 JSON 쪽에서 못박은 경계와 같은 자리를
    HTML 쪽에서 잰다 — 판정 규칙이 두 벌이면 한쪽만 고쳐진다.
    """

    pages = MANY_PAGES
    Q = "/?q=%EA%B9%80%EC%B9%98"  # q=김치

    def pager(self, path):
        """결과 화면의 이동 링크를 `{rel: href}` 로. 없으면 빈 dict.

        속성 **순서에 기대지 않는다** — 태그를 먼저 뽑고 그 안에서 rel·href 를 각각 찾는다.
        순서에 기대면 프로덕션에서 속성을 바꿔 쓴 날 테스트가 이유 없이 깨진다.
        """
        status, body, _ = self.raw(path)
        self.assertEqual(status, 200, body[:200])
        assert_page_basics(self, body)  # 이동을 붙이며 JS·viewport·h1 을 깨지 않았는가
        block = re.search(r"<nav[^>]*class=\"pager\"[^>]*>(.*?)</nav>", body, re.S)
        if not block:
            return {}
        found = {}
        for tag in re.findall(r"<a\b[^>]*>", block.group(1)):
            rel = re.search(r'rel="([^"]*)"', tag)
            href = re.search(r'href="([^"]*)"', tag)
            self.assertTrue(rel and href, "이동 링크에 rel 또는 href 가 없다: %s" % tag)
            found[rel.group(1)] = href.group(1)
        return found

    def page_of(self, href):
        """href 가 가리키는 page 번호. 질의도 함께 실려 있어야 한다."""
        parts = urllib.parse.urlsplit(html_unescape(href))
        params = urllib.parse.parse_qs(parts.query)
        self.assertEqual(params.get("q"), ["김치"], "이동 링크가 질의를 잃었다: %s" % href)
        return int(params["page"][0])

    def test_first_page_offers_the_next_one(self):
        self.assertEqual(self.page_of(self.pager(self.Q)["next"]), 2)

    def test_first_page_has_no_previous(self):
        # 긍정 짝은 아래 test_second_page_offers_previous — 둘이 같이 있어야 뜻이 있다
        self.assertNotIn("prev", self.pager(self.Q))

    def test_second_page_offers_previous(self):
        self.assertEqual(self.page_of(self.pager(self.Q + "&page=2")["prev"]), 1)

    def test_last_page_has_no_next(self):
        # 20건이 딱 2페이지 — limit+1 로 판정하는 방식이 여기서 틀리기 쉽다
        self.assertNotIn("next", self.pager(self.Q + "&page=2"))

    def test_page_cap_hides_the_next_link(self):
        """상한도 서버가 정한 것이니 마지막이라는 사실도 화면이 말해야 한다.

        JSON 쪽 `test_has_next_is_false_at_the_page_cap` 과 같은 계약이다 — 다음을
        내주면 따라간 사용자가 400 화면을 맞는다.
        """
        with mock.patch.object(serve, "MAX_PAGE", 1):
            self.assertNotIn("next", self.pager(self.Q))

    def test_empty_later_page_still_offers_a_way_back(self):
        # 3페이지는 0건이다. 여기서 이동을 통째로 감추면 **막다른 길**이 된다
        self.assertEqual(self.page_of(self.pager(self.Q + "&page=3")["prev"]), 2)

    def test_count_does_not_leak_the_probe_row(self):
        """`limit=PAGE_SIZE + 1` 로 받은 11번째가 "N건" 으로 새면 안 된다."""
        _, body, _ = self.raw(self.Q)
        self.assertIn("10건", body)
        self.assertNotIn("11건", body)

    def test_results_shown_are_still_ten(self):
        # 위 단언의 짝 — 세는 수가 아니라 **그리는 수**도 11이 되면 안 된다
        _, body, _ = self.raw(self.Q)
        self.assertEqual(body.count('<li class="hit">'), 10)

    def test_pager_nav_exists_when_there_is_somewhere_to_go(self):
        """`TestPagerAbsent` 의 긍정 짝 — 없다는 단언만 있으면 통째로 지워도 통과한다."""
        _, body, _ = self.raw(self.Q)
        self.assertIn("<nav", body)

    def test_pager_href_escapes_the_parameter_separator(self):
        """속성값 안의 날 `&` 는 HTML 유효성 위반이다 — `urlencode` 뒤에 하나 남는다.

        XSS 를 막는 것은 `urlencode` 쪽이다(`"`·`<` 를 퍼센트 인코딩한다). 이 단언이
        지키는 것은 **그 뒤에 남는 구분자 하나**뿐이고, 그래서 그렇게만 적는다.
        """
        self.assertIn("&amp;page=2", self.pager(self.Q)["next"])

    def test_pager_link_survives_a_hostile_query(self):
        """질의는 사용자가 쓴 문자열이다 — 이동 링크도 안전하게 나가야 한다.

        **HTTP 로는 이 자리를 못 잰다.** 특수문자 질의는 히트가 0건이라 `_pager` 가
        조기 반환하고 이동 블록 자체가 안 그려진다 — 화면을 훑는 단언은 검색창의
        이스케이프를 보고 통과할 뿐 이동 링크는 재지 않는다. 그리는 함수를 직접 부른다.
        """
        payload = '"><script>x</script>'
        nav = serve._pager(payload, page=2, has_next=True)
        self.assertNotIn("<script>", nav)
        hrefs = re.findall(r'href="([^"]*)"', nav)
        self.assertEqual(len(hrefs), 2, "잴 링크가 없다 — 공집합 위에서 참이 됐다")
        for href in hrefs:
            # 긍정 짝: 막기만 한 게 아니라 질의가 **살아서** 돌아와야 한다
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(html_unescape(href)).query)
            self.assertEqual(q["q"], [payload], "이동 링크가 질의를 망가뜨렸다: %s" % href)


class TestPagerBoundaries(ServeTestCase):
    """마지막 페이지가 **꽉 차지 않은** 경우 — 실제 검색에서 가장 흔한 모양이다.

    `MANY_PAGES`(20건)는 마지막 페이지가 정확히 10건인 **특수 케이스**만 덮는다.
    질의 대부분은 10의 배수가 아니다. 11건이면 2페이지에 1건만 남는다 —
    `len(hits) > PAGE_SIZE` 의 부등호가 여기서 틀리면 사용자는 다음을 눌러 **빈 화면**을 본다.
    """

    pages = dict(sorted(MANY_PAGES.items())[:11])
    Q = "/?q=%EA%B9%80%EC%B9%98"

    def body_of(self, path):
        status, body, _ = self.raw(path)
        self.assertEqual(status, 200, body[:200])
        return body

    def test_partial_last_page_offers_no_next(self):
        self.assertNotIn('rel="next"', self.body_of(self.Q + "&page=2"))

    def test_partial_last_page_still_shows_its_one_result(self):
        # 긍정 짝 — "다음이 없다" 는 결과가 0건이어도 참이다. 1건이 실제로 보여야 한다
        body = self.body_of(self.Q + "&page=2")
        self.assertEqual(body.count('<li class="hit">'), 1)
        self.assertIn("1건", body)

    def test_first_page_of_eleven_offers_next(self):
        # 긍정 짝 — 11번째 하나가 다음 장을 만든다
        self.assertIn('rel="next"', self.body_of(self.Q))


class TestPagerAbsent(ServeTestCase):
    """갈 곳이 아예 없으면 `<nav>` 를 **그리지 않는다**.

    `_pager` 의 `if not steps: return ""` 는 조기 반환이라 아무 단언도 안 밟는
    자리였다. 빈 `<nav>` 는 눈에도 보인다 — `.pager` 에 `border-top` 이 있어
    결과 아래 **의미 없는 줄 하나**가 그어진다.
    """

    pages = PAGES  # 김치 2건 = 1페이지로 끝, 앞뒤 어느 쪽으로도 갈 곳이 없다

    def test_single_page_has_no_pager_at_all(self):
        _, body, _ = self.raw("/?q=%EA%B9%80%EC%B9%98")
        self.assertNotIn("<nav", body, "갈 곳이 없는데 이동 블록을 그렸다")
        self.assertIn('<li class="hit">', body, "결과 자체는 나와야 한다")


class TestCliArgs(unittest.TestCase):
    """`serve.main` 인자 처리 — 여기까지 단위 테스트가 0 이었다.

    `e2e/search_api_e2e.py` 등 넷이 `--port 0` 정상 경로만 밟는다. `crawl.main` 쪽
    같은 갭 아래에 `--max=3` 이 조용히 무시되는 실버그가 있었다(`deadline-patches`).

    **가드는 `main()` 에 있고 `make_server()` 에는 없다** — 여기 테스트가 부는
    호루라기는 CLI 계약이지 라이브러리 계약이 아니다.
    """

    def call(self, *argv, bind=None):
        """`main(["websearch.serve", ...])` 을 부르고 (rc, stderr, make_server 목) 를 준다.

        **`make_server` 는 항상 가짜다.** 통과한 인자는 `serve_forever()` 로 들어가
        영영 안 돌아오기 때문이다 — 실제로 `--port ٨٠٨٠` 이 8080 에 진짜 서버를
        띄우고 매달렸다. 가드가 회귀했을 때 **테스트가 죽지 않고 매달리면** 신호가
        아니라 사고다(digest 의 M2 자리와 같은 부류).

        그래서 거절을 "rc 2" 만이 아니라 **"서버를 아예 안 띄웠다"** 로도 잰다.
        `bind` 를 주면 그 예외를 던진다 — 진짜 `bind()` 가 던지는 것과 같은 자리다.
        """
        fake = mock.Mock()
        fake.server_address = ("127.0.0.1", 8000)
        with mock.patch.object(serve, "make_server", side_effect=bind,
                               return_value=fake) as made, \
                mock.patch("sys.stdout", new_callable=io.StringIO), \
                mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            rc = serve.main(["websearch.serve"] + [str(a) for a in argv])
        return rc, err.getvalue(), made

    def test_db_argument_is_required(self):
        rc, err, made = self.call()
        self.assertEqual(rc, 2)
        self.assertIn("usage", err)
        self.assertFalse(made.called)

    def test_second_db_argument_is_refused(self):
        # 조용히 첫째만 쓰면 둘째 DB 를 보고 있다고 믿는 운영자가 생긴다
        rc, _, made = self.call("a.db", "b.db")
        self.assertEqual(rc, 2)
        self.assertFalse(made.called)

    def test_port_without_a_value(self):
        rc, err, _ = self.call("a.db", "--port")
        self.assertEqual(rc, 2)
        self.assertIn("--port", err)

    def test_non_numeric_port(self):
        rc, _, made = self.call("a.db", "--port", "abc")
        self.assertEqual(rc, 2)
        self.assertFalse(made.called)

    def test_port_above_the_maximum_is_refused_not_a_traceback(self):
        """`bind()` 는 65535 를 넘으면 `OverflowError` 를 던진다 — 실측했다.

        범위를 안 보면 그 예외가 그대로 사용자에게 간다. 트레이스백은 무엇을
        고쳐야 하는지 안 알려 준다(`indexer-cli-guard` 와 같은 관용구).
        """
        for bad in ("65536", "99999"):
            with self.subTest(port=bad):
                rc, err, made = self.call("a.db", "--port", bad)
                self.assertEqual(rc, 2)
                self.assertIn("--port", err)
                self.assertFalse(made.called, "bind 가 던질 값을 그대로 넘겼다")

    def test_the_highest_real_port_still_serves(self):
        """65535 는 진짜 포트다 — 상한을 한 칸 잘못 잡으면 여기가 죽는다.

        위 테스트만으로는 `> 65536` 변이가 살아남는다(실측). 경계는 양쪽에서 잰다.
        """
        rc, _, made = self.call("a.db", "--port", "65535")
        self.assertEqual(rc, 0)
        self.assertEqual(made.call_args[0][1], 65535)

    def test_port_zero_means_pick_any_and_is_not_a_rejected_value(self):
        """0 은 `--port` 에서만 진짜 값이다 — "아무 포트나" 라는 뜻이다.

        `--max`·`--workers`·`--deadline` 은 0 을 거절한다(26). 파서는 범위를 안 보므로
        **그 비대칭을 지키는 것은 여기 이 줄뿐**인데 단위 커버가 0 이었다:
        상한을 조이다 `port < 1` 을 같이 넣으면 단위는 전부 초록이고
        `--port 0` 으로 서버를 띄우는 e2e 넷만 죽는다(digest `[4]`).

        위 65535 테스트와 짝이다 — **경계는 양쪽에서 잰다.**
        """
        rc, _, made = self.call("a.db", "--port", "0")
        self.assertEqual(rc, 0)
        self.assertEqual(made.call_args[0][1], 0, "0 을 기본값 8000 으로 바꿔치기했다")

    def test_non_ascii_digits_are_not_a_port(self):
        """`str.isdigit()` 은 `²`·`٨` 에도 참이다 — `domain_key` 가 이미 밟은 자리다.

        `²` 는 `int()` 에서 `ValueError` 로 터지고(트레이스백), `٨٠٨٠` 은 **조용히
        8080 이 된다** — 뒤가 더 나쁘다. 운영자가 친 적 없는 포트로 서버가 뜬다.
        """
        for bad in ("²", "٨٠٨٠"):
            with self.subTest(port=bad):
                rc, _, made = self.call("a.db", "--port", bad)
                self.assertEqual(rc, 2)
                self.assertFalse(made.called, "운영자가 친 적 없는 포트로 서버를 띄웠다")

    def test_the_equals_form_works_and_is_guarded_the_same(self):
        """`crawl --max=3` 은 되는데 `serve --port=8080` 은 rc 2 였다 — 명령마다 계약이 달랐다.

        같은 파서(`flags.number_flag`)를 쓰면 두 형태가 **한 자리에서** 붙고,
        가드도 형태를 안 가린다. 받는 쪽만 보면 `--port=٨٠٨٠` 이 새로 뚫린다.
        """
        rc, _, made = self.call("a.db", "--port=8080")
        self.assertEqual(rc, 0)
        self.assertEqual(made.call_args[0][1], 8080)
        for bad in ("--port=٨٠٨٠", "--port=99999", "--port=abc", "--port="):
            with self.subTest(arg=bad):
                rc, err, made = self.call("a.db", bad)
                self.assertEqual(rc, 2)
                self.assertIn("--port", err)
                self.assertFalse(made.called)

    def test_a_taken_port_really_refuses_to_bind(self):
        """아래 테스트의 전제를 진짜 소켓으로 고정한다 — 가짜가 흉내내는 것이 실재한다."""
        taken = socket.socket()
        self.addCleanup(taken.close)
        taken.bind(("127.0.0.1", 0))
        taken.listen(1)
        with self.assertRaises(OSError):
            serve.make_server("a.db", port=taken.getsockname()[1])

    def test_bind_failure_is_reported_instead_of_crashing(self):
        """포트가 이미 쓰이거나(EADDRINUSE) 특권 포트면(`--port 80`) `bind` 가 던진다.

        둘 다 사용자 입력이 아니라 **환경**이라 rc 는 2 가 아니라 1 이다 — 잡히지 않던
        예외도 어차피 rc 1 이었으니 종료 코드는 그대로고, 바뀌는 것은 트레이스백뿐이다.
        """
        rc, err, _ = self.call("a.db", "--port", "8000",
                               bind=OSError(48, "Address already in use"))
        self.assertEqual(rc, 1)
        self.assertNotIn("Traceback", err)
        self.assertIn("8000", err)


if __name__ == "__main__":
    unittest.main()
