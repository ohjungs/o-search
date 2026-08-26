import os
import sqlite3
import tempfile
import unittest

from websearch.store import Store


class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")

    def test_upsert_then_has(self):
        self.assertFalse(self.store.has("http://a.com/"))
        self.store.upsert("http://a.com/", "<html/>", 200)
        self.assertTrue(self.store.has("http://a.com/"))

    def test_upsert_twice_updates_not_duplicates(self):
        self.store.upsert("http://a.com/", "v1", 200)
        self.store.upsert("http://a.com/", "v2", 200)
        self.assertEqual(self.store.count(), 1)
        self.assertEqual(self.store.get_html("http://a.com/"), "v2")

    def test_creates_missing_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            Store(os.path.join(tmp, "sub", "x.db")).upsert("http://a.com/", "h", 200)

    def test_failed_fetch_stored_without_html(self):
        self.store.upsert("http://a.com/gone", None, 404)
        self.assertTrue(self.store.has("http://a.com/gone"))
        self.assertIsNone(self.store.get_html("http://a.com/gone"))


class TestConcurrentAccess(unittest.TestCase):
    """다른 연결이 같은 DB 를 붙들고 있어도 저장은 죽지 않는다.

    사용자가 실제 웹 크롤 1,700문서에서 밟은 크래시다 — `indexer` 가 같은 파일을
    읽는 동안 `crawl` 의 upsert 가 `sqlite3.OperationalError: database is locked`
    로 프로세스를 통째로 죽였다. 수집한 1,700문서가 거기서 끊겼다.
    """

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, "crawl.db")
        self.store = Store(self.path)
        self.store.upsert("http://a.com/", "v1", 200)

    def _other_connection(self):
        other = sqlite3.connect(self.path)
        self.addCleanup(other.close)
        return other

    def test_upsert_survives_a_reader_holding_a_transaction(self):
        """indexer 가 페이지를 읽는 중 — 저널 모드에서 이게 쓰기를 막는다."""
        reader = self._other_connection()
        reader.execute("BEGIN")
        reader.execute("SELECT url FROM pages").fetchall()  # 읽기 트랜잭션을 연 채로 둔다
        self.store.upsert("http://b.com/", "v1", 200)
        self.assertTrue(self.store.has("http://b.com/"))

    def test_reader_still_sees_committed_rows(self):
        """죽지 않는 것만으로는 부족하다 — 다른 프로세스가 결과를 읽을 수 있어야 한다."""
        self.store.upsert("http://c.com/", "v1", 200)
        rows = self._other_connection().execute("SELECT count(*) FROM pages").fetchone()
        self.assertEqual(rows[0], 2)  # setUp 의 a.com + 이 테스트의 c.com
