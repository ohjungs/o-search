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


def build_db(path):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE pages (url TEXT PRIMARY KEY, html TEXT, status INTEGER)")
    for url, html in PAGES.items():
        db.execute("INSERT INTO pages VALUES (?, ?, 200)", (url, html))
    db.commit()
    db.close()
    indexer.index_pages(path)


class ServeTestCase(unittest.TestCase):
    """임시 DB 로 서버를 띄우고 실제 HTTP 로 때린다. 포트는 0 — 충돌하지 않는다."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = os.path.join(self._tmp.name, "crawl.db")
        build_db(self.db)
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


if __name__ == "__main__":
    unittest.main()
