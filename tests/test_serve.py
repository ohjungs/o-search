"""GET /search 가 검색 결과를 JSON 으로 내는지. 서버를 실제로 띄워 확인한다."""
import json
import os
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

from websearch import indexer, serve

PAGES = {
    "http://a.test/1": "<html><title>김치찌개 만들기</title><body>"
                       "<p>김치찌개 는 김치 로 끓인다. 김치 김치 김치</p></body></html>",
    "http://a.test/2": "<html><title>김치 담그기</title><body>"
                       "<p>배추를 절여 김치 를 담근다</p></body></html>",
    "http://a.test/3": "<html><title>Search engine</title><body>"
                       "<p>An engine that indexes documents</p></body></html>",
}


# 20건 = 정확히 2페이지. has_next 를 limit+1 로 판정하므로 경계는 "딱 떨어지는" 마지막 페이지다
MANY_PAGES = {
    "http://p.test/%02d" % i: "<html><title>김치 %02d</title><body>"
                              "<p>김치 를 담근다</p></body></html>" % i
    for i in range(20)
}


def build_db(path, pages):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE pages (url TEXT PRIMARY KEY, html TEXT, status INTEGER)")
    for url, html in pages.items():
        db.execute("INSERT INTO pages VALUES (?, ?, 200)", (url, html))
    db.commit()
    db.close()
    indexer.index_pages(path)


class ServeTestCase(unittest.TestCase):
    """임시 DB 로 서버를 띄우고 실제 HTTP 로 때린다. 포트는 0 — 충돌하지 않는다."""

    pages = PAGES

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = os.path.join(self._tmp.name, "crawl.db")
        build_db(self.db, self.pages)
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


if __name__ == "__main__":
    unittest.main()
