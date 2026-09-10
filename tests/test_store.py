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

    def test_stored_html_is_compressed(self):
        """원본 HTML 이 DB 에서 자리를 덜 차지한다.

        실물 400문서에서 `pages` 가 DB 의 **78.6%**(78.6MB · 문서당 191KB)였고,
        컨셉 1단계(10만 문서)로 환산하면 25GB 라 단일 머신 전제가 깨진다
        (`docs/specs/concept.md` 경량 1). 되풀이되는 마크업이라 zlib 이 6.2배를
        접는다 — 저장된 바이트가 원문보다 작다는 것이 그 계약이다.
        """
        html = "<div class='x'>가나다</div>" * 400
        self.store.upsert("http://a.com/big", html, 200)
        stored = self.store._db.execute(
            "SELECT html FROM pages WHERE url=?", ("http://a.com/big",)
        ).fetchone()[0]
        self.assertIsInstance(stored, bytes, "압축분은 BLOB 로 들어간다")
        self.assertLess(len(stored), len(html.encode("utf-8")) // 2)
        # 접었어도 읽는 쪽은 원문 그대로 받는다.
        self.assertEqual(self.store.get_html("http://a.com/big"), html)

    def test_rows_written_before_compression_still_read(self):
        """옛 DB 를 그대로 읽는다 — 그래서 마이그레이션이 필요 없다.

        압축 이전 행은 `html` 이 TEXT 다. 읽기가 두 꼴을 다 받으면 기존 100MB
        코퍼스를 버리지도 변환하지도 않고, 재크롤이 자연히 갈아 끼운다.
        """
        self.store._db.execute(
            "INSERT INTO pages(url, html, status) VALUES (?, ?, ?)",
            ("http://a.com/old", "<p>옛 원문</p>", 200),
        )
        self.assertEqual(self.store.get_html("http://a.com/old"), "<p>옛 원문</p>")


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


class TestFreshness(unittest.TestCase):
    """「저장돼 있나」가 아니라 「아직 신선한가」 — 사양 기능 5 의 30일이 여기 산다.

    **시각 비교를 SQLite 에 맡긴 것이 계약이다** (`docs/design_history_066.md` 계약 1).
    `upsert` 가 `datetime('now')`(UTC)로 박으므로 읽는 쪽이 파이썬 시계를 쓰면
    타임존·해상도가 어긋나 비교가 조용히 틀린다 — 계획 78 이 그 자리에서 실제로
    한 번 빨개졌다.
    """

    def setUp(self):
        self.store = Store(":memory:")

    def _aged(self, url, days, status=200):
        """그 URL 을 `days` 일 전에 받아 둔 상태로 만든다."""
        self.store.upsert(url, "<html/>" if status < 400 else None, status)
        self.store._db.execute("UPDATE pages SET fetched_at=datetime('now', ?) WHERE url=?",
                               ("-%d days" % days, url))
        self.store._db.commit()

    def test_never_fetched_url_is_not_fresh(self):
        # `has` 가 False 이던 자리와 같은 답이어야 한다 — 안 그러면 시드부터 안 나간다
        self.assertFalse(self.store.is_fresh("http://a.com/"))

    def test_just_fetched_is_fresh(self):
        self.store.upsert("http://a.com/", "<html/>", 200)
        self.assertTrue(self.store.is_fresh("http://a.com/"))

    def test_success_goes_stale_after_thirty_days(self):
        self._aged("http://a.com/old", 31)
        self._aged("http://a.com/new", 29)
        self.assertFalse(self.store.is_fresh("http://a.com/old"))
        self.assertTrue(self.store.is_fresh("http://a.com/new"))

    def test_failure_goes_stale_at_half_that(self):
        self._aged("http://a.com/gone", 16, status=404)
        self._aged("http://a.com/gone2", 14, status=404)
        self.assertFalse(self.store.is_fresh("http://a.com/gone"))
        self.assertTrue(self.store.is_fresh("http://a.com/gone2"))

    def test_the_two_periods_are_actually_different(self):
        """같은 20일인데 성공은 신선하고 실패는 낡았다 — 주기가 둘인 계약이다.

        실패를 성공과 같은 30일로 두면 일시 장애가 그만큼 오래 결손으로 남고,
        같은 빈도로 두면 죽은 URL 을 영원히 같은 속도로 두드린다
        (`plan_recrawl.md` 2절 정책 1).
        """
        self._aged("http://a.com/ok", 20, status=200)
        self._aged("http://a.com/err", 20, status=500)
        self.assertTrue(self.store.is_fresh("http://a.com/ok"))
        self.assertFalse(self.store.is_fresh("http://a.com/err"))

    def test_redirect_range_counts_as_failure_period(self):
        # 2xx 만 성공이다 — 3xx 는 `fetcher` 가 따라가므로 저장될 일이 드물지만,
        # 저장됐다면 그것은 「본문을 못 받았다」다
        self._aged("http://a.com/moved", 20, status=301)
        self.assertFalse(self.store.is_fresh("http://a.com/moved"))


class RejectedIsNotAFetchTest(unittest.TestCase):
    """**429 행은 「받은 적 없다」로 읽힌다.**

    계획 84 가 429 를 **더 이상 저장하지 않게** 했지만, 그 전에 박힌 행이 실물 DB 에
    **3,686개** 있다(2026-09-09 1만 크롤 · 위키미디어 6도메인). 그 행들은 지금
    `status != 2xx` 라 `RETRY_DAYS`(15일) 동안 신선한 것으로 읽혀 **재시도에서 빠진다** —
    받은 적 없는 문서를 15일간 「받았다」로 취급하는 것이다.

    **지우지 않고 읽는 쪽을 고친다.** 데이터 삭제는 야간 금지이고 계획 80 이 정한
    「`pages` 는 묘비로 남긴다」와 충돌한다. 그리고 429 는 묘비가 아니다 — 묘비는
    404·410 처럼 「그 자리에 문서가 없다」는 사실이고, 429 는 「지금은 안 된다」는
    **그 시각의 사정**이다. 사실이 아니라 사정을 15일간 붙들 이유가 없다.
    """

    def setUp(self):
        self.store = Store(":memory:")

    def _rejected(self, url):
        self.store._db.execute(
            "INSERT INTO pages(url, html, status) VALUES (?, NULL, 429)", (url,))
        self.store._db.commit()

    def test_a_429_row_is_never_fresh(self):
        self._rejected("http://a.com/x")
        self.assertFalse(self.store.is_fresh("http://a.com/x"),
                         "방금 거절당한 URL 이 신선하다고 읽힌다 — 15일간 재시도에서 빠진다")

    def test_a_404_row_is_still_a_tombstone(self):
        """**묘비는 그대로다.** 404 는 「그 자리에 문서가 없다」는 사실이라 15일을 지킨다.

        이 단언이 없으면 「실패는 전부 다시 받는다」로 넓어져 없는 URL 을 15일마다가
        아니라 매 실행 두드리게 된다 — 고치려던 것과 반대 방향의 윤리 문제다.
        """
        self.store._db.execute(
            "INSERT INTO pages(url, html, status) VALUES (?, NULL, 404)", ("http://a.com/g",))
        self.store._db.commit()
        self.assertTrue(self.store.is_fresh("http://a.com/g"),
                        "404 묘비까지 매번 다시 받는다")

    def test_a_200_row_is_unaffected(self):
        self.store.upsert("http://a.com/ok", "<p>x</p>", 200)
        self.assertTrue(self.store.is_fresh("http://a.com/ok"))


class UnfinishedUrlsTest(unittest.TestCase):
    """**받다 만 URL 을 되찾는다.** 계획 87 이 「86 은 충분하지 않다」를 실물로 잡은 자리다.

    429 행을 「안 신선」으로 읽게 만들어도(계획 86) 그 URL 이 **큐에 들어올 길이 없으면**
    아무 일도 안 일어난다 — 프런티어가 메모리라 매 실행 시드에서 다시 자라는데, 부모가
    신선하면 팝 지점에서 스킵돼 링크 추출조차 없어 자식이 큐에 못 들어온다.
    실물 3,807개가 그 상태였다.

    **새 표를 안 만든다.** 그 URL 들은 이미 `pages` 에 있고, 「다시 받아야 하나」의
    판정자도 이미 있다(`is_fresh`). 없던 것은 **그 판정을 거꾸로 물어보는 길**뿐이다.
    """

    def setUp(self):
        self.store = Store(":memory:")

    def test_a_rejected_url_is_unfinished(self):
        self.store._db.execute(
            "INSERT INTO pages(url, html, status) VALUES (?, NULL, 429)", ("http://a.com/x",))
        self.store._db.commit()
        self.assertIn("http://a.com/x", self.store.unfinished())

    def test_a_fresh_page_is_not_unfinished(self):
        self.store.upsert("http://a.com/ok", "<p>x</p>", 200)
        self.assertNotIn("http://a.com/ok", self.store.unfinished())

    def test_a_tombstone_is_not_unfinished_while_it_is_still_fresh(self):
        """404 묘비는 `RETRY_DAYS` 동안 조용하다 — 되찾기가 그것을 뒤집지 않는다."""
        self.store._db.execute(
            "INSERT INTO pages(url, html, status) VALUES (?, NULL, 404)", ("http://a.com/g",))
        self.store._db.commit()
        self.assertNotIn("http://a.com/g", self.store.unfinished())

    def test_the_limit_is_honoured(self):
        """**상한이 있다.** 미완이 10만이면 프런티어를 그것으로 채우는 것이 크롤이 아니다."""
        for i in range(5):
            self.store._db.execute(
                "INSERT INTO pages(url, html, status) VALUES (?, NULL, 429)", ("http://a.com/%d" % i,))
        self.store._db.commit()
        self.assertEqual(len(self.store.unfinished(limit=2)), 2)


class DiscoveredSurvivesRestartTest(unittest.TestCase):
    """**발견만 하고 못 받은 URL 이 종료를 넘어 산다.**

    계획 87 이 실물에서 잡고 88 이 절반을 닫았다 — 88 은 `pages` 에 **이미 있는** 미완
    URL 을 되찾았지만, 큐에만 있다가 종료된 URL 은 `pages` 에 한 번도 안 들어가므로
    여전히 잃는다(88 e2e 3절이 「진짜 영속화의 몫」으로 적어 뒀다).

    실물에서 이것이 규모를 막는다: 프런티어가 메모리라 매 실행이 시드에서 다시 자라고,
    `--max` 로 끊긴 크롤이 **다음 실행에 그 지점을 이어받지 못한다.** 컨셉 1단계
    (10만 문서)는 한 번에 도는 크기가 아니다.

    **`pages` 에 안 박는 이유**는 그 표가 「받아 본 것」이기 때문이다 — 발견은 수집이
    아니다. 안 받은 URL 을 `pages` 에 넣으면 계획 84·86 이 429 에서 닫은 그 거짓
    (「안 받은 것을 받았다고 적는다」)을 다시 여는 것이다.
    """

    def setUp(self):
        self.store = Store(":memory:")

    def test_a_discovered_url_is_unfinished(self):
        self.store.remember(["http://a.com/x"])
        self.assertIn("http://a.com/x", self.store.unfinished())

    def test_fetching_it_takes_it_out_of_the_queue(self):
        self.store.remember(["http://a.com/x"])
        self.store.upsert("http://a.com/x", "<p>x</p>", 200)
        self.assertNotIn("http://a.com/x", self.store.unfinished())

    def test_remembering_twice_is_harmless(self):
        self.store.remember(["http://a.com/x"])
        self.store.remember(["http://a.com/x"])
        self.assertEqual(self.store.unfinished().count("http://a.com/x"), 1)

    def test_a_rejected_url_stays_in_the_queue(self):
        """429 를 받은 URL 은 발견 큐에도 남는다 — 받은 적이 없기 때문이다."""
        self.store.remember(["http://a.com/x"])
        self.store._db.execute(
            "INSERT INTO pages(url, html, status) VALUES (?, NULL, 429)", ("http://a.com/x",))
        self.store._db.commit()
        self.assertIn("http://a.com/x", self.store.unfinished())
