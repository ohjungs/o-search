import os
import sqlite3
import tempfile
import unittest

from websearch import indexer
from websearch.indexer import index_pages, search
from websearch.store import Store


class TestIndexPages(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = os.path.join(self.dir.name, "crawl.db")

    def _seed(self, rows):
        store = Store(self.db_path)
        for url, html in rows:
            store.upsert(url, html, 200)

    def _docs(self):
        db = sqlite3.connect(self.db_path)
        self.addCleanup(db.close)
        return db.execute("SELECT url, title, body FROM docs ORDER BY url").fetchall()

    def test_indexes_all_new_pages(self):
        self._seed([
            ("http://a.test/", "<title>가</title><p>첫 문서</p>"),
            ("http://b.test/", "<title>나</title><p>둘째 문서</p>"),
        ])
        self.assertEqual(index_pages(self.db_path), 2)
        self.assertEqual(
            self._docs(),
            [("http://a.test/", "가", "첫 문서"), ("http://b.test/", "나", "둘째 문서")],
        )

    def test_second_run_is_incremental(self):
        self._seed([("http://a.test/", "<title>가</title><p>첫 문서</p>")])
        self.assertEqual(index_pages(self.db_path), 1)
        self.assertEqual(index_pages(self.db_path), 0)
        self.assertEqual(len(self._docs()), 1)

    def test_only_new_pages_indexed_on_rerun(self):
        self._seed([("http://a.test/", "<title>가</title><p>첫</p>")])
        index_pages(self.db_path)
        self._seed([("http://b.test/", "<title>나</title><p>둘째</p>")])
        self.assertEqual(index_pages(self.db_path), 1)
        self.assertEqual(len(self._docs()), 2)

    def test_html_markup_not_stored(self):
        self._seed([("http://a.test/", "<title>t</title><script>var x=1;</script><p>보이는 글</p>")])
        index_pages(self.db_path)
        body = self._docs()[0][2]
        self.assertEqual(body, "보이는 글")

    def test_null_html_skipped(self):
        self._seed([("http://a.test/", None), ("http://b.test/", "<p>있음</p>")])
        self.assertEqual(index_pages(self.db_path), 1)
        self.assertEqual([row[0] for row in self._docs()], ["http://b.test/"])

    def test_missing_db_raises(self):
        with self.assertRaises(FileNotFoundError):
            index_pages(os.path.join(self.dir.name, "없는.db"))


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = os.path.join(self.dir.name, "crawl.db")

    def _seed_and_index(self, rows):
        store = Store(self.db_path)
        for url, html in rows:
            store.upsert(url, html, 200)
        index_pages(self.db_path)

    def test_korean_two_char_query_matches_inflected_word(self):
        # 설계에서 unicode61 + prefix 를 고른 이유가 이것이다 (trigram 은 여기서 실패했다)
        self._seed_and_index([("http://a.test/", "<title>요리</title><p>어제 김치를 담갔다</p>")])
        hits = search(self.db_path, "김치")
        self.assertEqual([h[0] for h in hits], ["http://a.test/"])

    def test_result_shape_is_url_title_snippet(self):
        self._seed_and_index([("http://a.test/", "<title>요리</title><p>김치찌개 만드는 법</p>")])
        url, title, snippet = search(self.db_path, "김치")[0]
        self.assertEqual(url, "http://a.test/")
        self.assertEqual(title, "요리")
        self.assertIn("김치찌개", snippet)

    def test_english_is_case_insensitive(self):
        self._seed_and_index([("http://a.test/", "<title>Guide</title><p>Python Tutorial</p>")])
        self.assertEqual(len(search(self.db_path, "python")), 1)

    def test_title_is_searchable(self):
        # 계약: MATCH 는 title·body 두 열을 모두 본다. body 만 보도록 바뀌면 여기서 깨진다
        self._seed_and_index([("http://a.test/", "<title>김치 백과</title><body></body>")])
        self.assertEqual([h[0] for h in search(self.db_path, "백과")], ["http://a.test/"])

    def test_bm25_ranks_denser_match_first(self):
        # 컨셉 우선순위 2위가 검색 품질이다 — 정렬이 관련도순인지 단언으로 못박는다
        self._seed_and_index([
            ("http://dense.test/", "<p>김치 김치 김치 담그기</p>"),
            ("http://sparse.test/",
             "<p>오늘 저녁은 김치 한 조각과 밥 그리고 국 그리고 나물 그리고 생선 그리고 과일</p>"),
        ])
        self.assertEqual(
            [h[0] for h in search(self.db_path, "김치")],
            ["http://dense.test/", "http://sparse.test/"],
        )

    def test_no_match_returns_empty_list(self):
        self._seed_and_index([("http://a.test/", "<p>김치</p>")])
        self.assertEqual(search(self.db_path, "우주선"), [])

    def test_limit_is_respected(self):
        self._seed_and_index([
            ("http://%d.test/" % i, "<p>김치 문서 %d</p>" % i) for i in range(5)
        ])
        self.assertEqual(len(search(self.db_path, "김치", limit=2)), 2)

    def test_all_terms_required(self):
        self._seed_and_index([
            ("http://a.test/", "<p>김치 담그기</p>"),
            ("http://b.test/", "<p>김치 볶음밥</p>"),
        ])
        hits = search(self.db_path, "김치 볶음")
        self.assertEqual([h[0] for h in hits], ["http://b.test/"])

    def test_fts5_syntax_chars_do_not_raise(self):
        self._seed_and_index([("http://a.test/", "<p>김치 담그기</p>")])
        for query in ['NEAR(a b)', '"', 'foo(bar', 'a OR b', '김치* AND', '-김치', '']:
            self.assertIsInstance(search(self.db_path, query), list)

    def test_search_on_unindexed_db_returns_empty(self):
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        self.assertEqual(search(self.db_path, "김치"), [])

    def test_missing_db_raises(self):
        with self.assertRaises(FileNotFoundError):
            search(os.path.join(self.dir.name, "없는.db"), "김치")


class TestCli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = os.path.join(self.dir.name, "crawl.db")

    def test_no_args_is_usage_error(self):
        self.assertEqual(indexer.main(["prog"]), 2)

    def test_missing_db_is_error_not_traceback(self):
        self.assertEqual(indexer.main(["prog", os.path.join(self.dir.name, "없는.db")]), 2)

    def test_query_without_value_is_error(self):
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        self.assertEqual(indexer.main(["prog", self.db_path, "--query"]), 2)

    def test_index_then_query(self):
        Store(self.db_path).upsert("http://a.test/", "<title>요리</title><p>김치</p>", 200)
        self.assertEqual(indexer.main(["prog", self.db_path]), 0)
        self.assertEqual(indexer.main(["prog", self.db_path, "--query", "김치"]), 0)
