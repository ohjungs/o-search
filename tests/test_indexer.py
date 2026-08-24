import os
import sqlite3
import tempfile
import unittest

from websearch.indexer import index_pages
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
