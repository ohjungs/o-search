import os
import sqlite3
import tempfile
import threading
import time
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

    def test_busy_timeout_is_raised_above_the_sqlite_default(self):
        """상한 값 자체를 고정한다 — 아래 대기 테스트로는 이게 안 잡힌다.

        sqlite3 기본 `busy_timeout` 은 **0이 아니라 5000ms** 라, 짧게 붙드는 테스트는
        `timeout=` 을 통째로 지워도 통과한다(백지 리뷰 지적). 30초가 왜 필요한지는
        `docs/history_current.md` 반복 68 의 탐침에 있다 — 6초짜리라 스위트에 안 넣었고,
        대신 그 계약을 여기서 한 줄로 고정한다.
        """
        actual = self.store._db.execute("PRAGMA busy_timeout").fetchone()[0]
        self.assertGreater(actual, 5000, "기본값 5000ms 를 넘겨야 색인 중 커밋을 견딘다")

    def test_upsert_waits_out_a_writer_instead_of_dying(self):
        """쓰기끼리 부딪히면 **기다린다**. WAL 도 쓰기끼리는 배타적이라 이건 timeout 몫이다.

        붙드는 시간(0.3초)이 짧아 **상한 값은 못 고정한다** — 위 테스트가 그쪽을 맡는다.
        여기서 고정하는 건 "빨리 실패하지 않고 기다린다" 하나다.
        """
        holding = threading.Event()

        def hold():  # 커넥션은 만든 스레드가 끝까지 소유한다
            other = sqlite3.connect(self.path, timeout=30)
            other.execute("BEGIN IMMEDIATE")  # 쓰기 락
            other.execute("INSERT INTO pages(url, status) VALUES ('http://h/', 200)")
            holding.set()
            time.sleep(0.3)
            other.commit()
            other.close()

        writer = threading.Thread(target=hold)
        writer.start()
        self.addCleanup(writer.join)
        holding.wait(timeout=5)
        self.store.upsert("http://b.com/", "v1", 200)  # timeout 이 0이면 여기서 죽는다
        self.assertTrue(self.store.has("http://b.com/"))

    def test_reader_still_sees_committed_rows(self):
        """죽지 않는 것만으로는 부족하다 — 다른 프로세스가 결과를 읽을 수 있어야 한다."""
        self.store.upsert("http://c.com/", "v1", 200)
        rows = self._other_connection().execute("SELECT count(*) FROM pages").fetchone()
        self.assertEqual(rows[0], 2)  # setUp 의 a.com + 이 테스트의 c.com
