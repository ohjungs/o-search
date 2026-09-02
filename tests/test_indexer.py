import contextlib
import io
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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

    def test_db_without_pages_raises_instead_of_leaking_sqlite_error(self):
        # 크롤한 적 없는 DB(또는 남의 DB)를 준 경우. sqlite3.OperationalError 가
        # 그대로 새면 CLI 가 트레이스백을 낸다 — digest 반복 실패 항목.
        other = os.path.join(self.dir.name, "남의.db")
        sqlite3.connect(other).execute("CREATE TABLE junk(x)")
        with self.assertRaises(indexer.NoCrawlDataError):
            index_pages(other)

    def test_empty_pages_table_is_zero_not_an_error(self):
        # 대조군 — "크롤 데이터가 없다" 와 "크롤했는데 0건" 은 다른 상태다.
        Store(self.db_path)  # pages 를 만들기만 하고 아무것도 안 넣는다
        self.assertEqual(index_pages(self.db_path), 0)

    def test_noindex_page_is_not_indexed(self):
        # 크롤 윤리: 색인 거부를 선언한 문서는 색인에 들어가지 않는다
        self._seed([
            ("http://a.test/", '<meta name="robots" content="noindex"><p>거부</p>'),
            ("http://b.test/", "<p>허용</p>"),
        ])
        self.assertEqual(index_pages(self.db_path), 1)
        self.assertEqual([row[0] for row in self._docs()], ["http://b.test/"])

    def test_already_indexed_page_that_declares_noindex_is_removed(self):
        self._seed([("http://a.test/", "<p>허용 pyeongsan</p>")])
        self.assertEqual(index_pages(self.db_path), 1)
        # 뒤늦게 noindex 를 달았다 (재크롤로 pages.html 이 갱신된 상황)
        Store(self.db_path).upsert(
            "http://a.test/", '<meta name="robots" content="none"><p>허용 pyeongsan</p>', 200
        )
        self.assertEqual(index_pages(self.db_path), 0)
        self.assertEqual(self._docs(), [])
        self.assertEqual(search(self.db_path, "pyeongsan"), [])

    def test_removal_pass_survives_null_html_and_missing_page(self):
        # 갭 탐색: 제거 경로가 크롤 실패 행(html NULL)과 pages 에서 사라진 색인 행을 만난다
        self._seed([("http://a.test/", None), ("http://b.test/", "<p>robots 낱말만 있는 본문</p>")])
        self.assertEqual(index_pages(self.db_path), 1)
        db = sqlite3.connect(self.db_path)
        db.execute("INSERT INTO docs(title, body, url) VALUES ('유령','x','http://ghost/')")
        db.commit()
        db.close()
        self.assertEqual(index_pages(self.db_path), 0)
        self.assertEqual([row[0] for row in self._docs()], ["http://b.test/", "http://ghost/"])

    def test_rerun_keeps_allowed_pages_indexed_once(self):
        # 제거 경로가 멀쩡한 문서를 건드리지 않는지 — 회귀 방지
        self._seed([
            ("http://a.test/", "<p>허용</p>"),
            ("http://b.test/", '<meta name="robots" content="noindex"><p>거부</p>'),
        ])
        index_pages(self.db_path)
        self.assertEqual(index_pages(self.db_path), 0)
        self.assertEqual([row[0] for row in self._docs()], ["http://a.test/"])

    def test_interrupted_incremental_run_indexes_nothing(self):
        # 재구축이 아닌 평소 경로. main 의 안내 "색인은 바뀌지 않았다" 는 이쪽에서도
        # 참이어야 한다 — 오늘은 암묵 트랜잭션 덕에 참이고, 중간 commit 이 하나라도
        # 끼면 거짓이 된다. 둘째 문서에서 끊어 "부분만 남는다" 를 재게 만든다.
        self._seed([("http://a.test/", "<title>가</title><p>첫</p>")])
        self.assertEqual(index_pages(self.db_path), 1)
        self._seed([("http://b.test/", "<title>나</title><p>둘째</p>"),
                    ("http://c.test/", "<title>다</title><p>셋째</p>")])
        with mock.patch.object(indexer.extract, "extract_text",
                               side_effect=[("나", "둘째"), KeyboardInterrupt]):
            with self.assertRaises(KeyboardInterrupt):
                index_pages(self.db_path)
        self.assertEqual([row[0] for row in self._docs()], ["http://a.test/"])


class TestSchemaDrift(unittest.TestCase):
    """`SCHEMA` 는 CREATE ... IF NOT EXISTS 다 — 정의를 바꿔도 옛 DB 는 옛 정의로 남는다.

    그 조용한 불일치를 감지해 `docs` 를 재구축하는 경로. `docs` 는 `pages` 에서
    파생된 색인이라 버리고 다시 만들어도 원본이 사라지지 않는다.
    """

    OLD_SCHEMA = ("CREATE VIRTUAL TABLE docs "
                  "USING fts5(title, body, url UNINDEXED, tokenize='unicode61')")

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = os.path.join(self.dir.name, "crawl.db")

    def _connect(self):
        db = sqlite3.connect(self.db_path)
        self.addCleanup(db.close)
        return db

    def _docs_sql(self):
        return self._connect().execute(
            "SELECT sql FROM sqlite_master WHERE name = 'docs'").fetchone()[0]

    def _seed_old_index(self, rows):
        """옛 정의로 만든 docs 에 색인까지 끝난 DB — 코드만 새것으로 갈아탄 상황."""
        store = Store(self.db_path)
        for url, html in rows:
            store.upsert(url, html, 200)
        db = self._connect()
        db.execute(self.OLD_SCHEMA)
        for url, html in rows:
            db.execute("INSERT INTO docs(title, body, url) VALUES (?, ?, ?)",
                       ("제목", html, url))
        db.commit()

    def test_drifted_docs_table_is_rebuilt_to_current_schema(self):
        self._seed_old_index([("http://a.test/", "<title>김치</title><p>김치찌개</p>")])
        self.assertNotEqual(self._docs_sql(), indexer.SCHEMA.replace(" IF NOT EXISTS", ""))
        index_pages(self.db_path)
        self.assertEqual(self._docs_sql(),
                         indexer.SCHEMA.replace(" IF NOT EXISTS", ""))

    def test_rebuild_reindexes_every_page_and_search_works(self):
        self._seed_old_index([
            ("http://a.test/", "<title>김치</title><p>김치찌개 끓이기</p>"),
            ("http://b.test/", "<title>제주</title><p>올레 길 걷기</p>"),
        ])
        self.assertEqual(index_pages(self.db_path), 2)  # 전량 재색인
        db = self._connect()
        self.assertEqual(db.execute("SELECT count(*) FROM docs").fetchone()[0], 2)
        self.assertEqual([h[0] for h in search(self.db_path, "김치찌개")], ["http://a.test/"])

    def test_rebuild_does_not_touch_pages(self):
        # 긍정 짝 — "docs 가 재구축됐다" 만 보면 pages 가 날아가도 통과한다
        rows = [("http://a.test/", "<title>가</title><p>첫</p>"),
                ("http://b.test/", "<title>나</title><p>둘째</p>")]
        self._seed_old_index(rows)
        before = self._connect().execute(
            "SELECT url, html FROM pages ORDER BY url").fetchall()
        index_pages(self.db_path)
        after = self._connect().execute(
            "SELECT url, html FROM pages ORDER BY url").fetchall()
        self.assertEqual(after, before)
        self.assertEqual(len(after), 2)

    def test_current_schema_is_left_alone(self):
        # 드리프트가 없는데 재구축하면 매 실행이 전량 재색인이 된다
        Store(self.db_path).upsert("http://a.test/", "<title>가</title><p>첫</p>", 200)
        self.assertEqual(index_pages(self.db_path), 1)
        self.assertEqual(index_pages(self.db_path), 0)

    def test_rebuild_is_not_reported_as_noindex_removal(self):
        # 재구축은 옛 색인을 버리고 다시 채운다 — 뺀 문서가 하나도 없다. 그런데도
        # "제외" 로 찍히면 정말 뺐을 때 울리라고 둔 경보가 갈아탄 사람 전원에게 거짓으로 운다
        self._seed_old_index([("http://a.test/", "<title>가</title><p>첫</p>"),
                              ("http://b.test/", "<title>나</title><p>둘째</p>")])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(indexer.main(["prog", self.db_path]), 0)
        self.assertNotIn("색인 제외", buf.getvalue())
        self.assertIn("2 문서 색인", buf.getvalue())  # 긍정 짝 — 침묵도 통과하지 않는다

    def test_search_on_drifted_index_fails_loudly(self):
        # 조용히 빈 목록을 내면 "결과 0건" 과 구분되지 않는다 — 색인 전과는 다른 상황이다
        self._seed_old_index([("http://a.test/", "<title>김치</title><p>김치찌개</p>")])
        with self.assertRaises(indexer.StaleIndexError):
            search(self.db_path, "김치")

    def test_drifted_index_is_loud_for_a_tokenless_query_too(self):
        # DB 상태 판정이 **질의 내용**에 달리면 안 된다. 조기 반환이 `_connect` 앞에
        # 있으면 `%01` 같은 무토큰 질의만 옛 색인을 그대로 지나쳐 `[]`→200 으로 샌다
        self._seed_old_index([("http://a.test/", "<title>김치</title><p>김치찌개</p>")])
        with self.assertRaises(indexer.StaleIndexError):
            search(self.db_path, "\x01")

    def test_cli_query_on_drifted_index_is_an_error_not_a_traceback(self):
        # 리뷰 발견: 바로 옆에서 FileNotFoundError 는 정성껏 처리하는데 이쪽만
        # 트레이스백 + rc=1 로 나간다. 복구법(색인 다시 돌리기)이 화면에 안 보인다
        self._seed_old_index([("http://a.test/", "<title>김치</title><p>김치찌개</p>")])
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            self.assertEqual(indexer.main(["prog", self.db_path, "--query", "김치"]), 1)
        self.assertIn("색인", buf.getvalue())  # 긍정 짝 — 침묵도 통과하지 않는다

    def test_interrupted_rebuild_leaves_the_old_index_intact(self):
        # 재구축은 DROP → CREATE → 전량 INSERT 다. sqlite3 는 DDL 을 암묵 트랜잭션에
        # 넣지 않으므로 명시로 열지 않으면 중단 시 DROP/CREATE 만 커밋되고 INSERT 만
        # 롤백된다 — 옛 색인이 사라지고 0행이 남아 검색이 전부 "결과 없음" 이 된다.
        # 크롤 데이터가 없는 것과 구별되지 않는 성공이라 조용하다.
        rows = [("http://a.test/", "<title>가</title><p>첫</p>"),
                ("http://b.test/", "<title>나</title><p>둘째</p>")]
        self._seed_old_index(rows)
        old_sql = self._docs_sql()
        with mock.patch.object(indexer.extract, "extract_text",
                               side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                index_pages(self.db_path)
        self.assertEqual(
            self._connect().execute("SELECT count(*) FROM docs").fetchone()[0], 2)
        # 정의도 옛것 그대로여야 한다 — 그래야 다음 실행이 다시 재구축한다
        self.assertEqual(self._docs_sql(), old_sql)


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

    def test_offset_skips_earlier_hits(self):
        # 페이지네이션의 토대 — limit 만으로는 2페이지를 낼 수 없다
        self._seed_and_index([("http://a.test/%d" % i, "<title>김치 %d</title><p>김치</p>" % i)
                              for i in range(5)])
        every = search(self.db_path, "김치", limit=5)
        self.assertEqual(len(every), 5)
        self.assertEqual(search(self.db_path, "김치", limit=2, offset=2), every[2:4])

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

    def test_null_byte_in_query_does_not_raise(self):
        # 리뷰 발견: NUL 이 FTS5 문자열을 조기 종료시켜 OperationalError 가 새어나왔다.
        # 오늘은 argv 로 도달 불가지만 search() 는 공개 API 다 (search-api 계획에서 HTTP 로 들어온다)
        self._seed_and_index([("http://a.test/", "<p>김치</p>")])
        self.assertEqual([h[0] for h in search(self.db_path, "김치\x00")], ["http://a.test/"])
        self.assertEqual(search(self.db_path, "\x00"), [])

    def test_snippet_comes_from_matching_column(self):
        # 리뷰 발견: body 열 고정이라 제목만 매치되면 질의어가 없는 스니펫이 나왔다
        self._seed_and_index([
            ("http://a.test/", "<title>김치 담그는 법</title><p>봄에는 나물이 좋다</p>"),
        ])
        self.assertIn("김치", search(self.db_path, "김치")[0][2])

    def test_search_on_unindexed_db_returns_empty(self):
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        self.assertEqual(search(self.db_path, "김치"), [])

    def test_missing_db_raises(self):
        with self.assertRaises(FileNotFoundError):
            search(os.path.join(self.dir.name, "없는.db"), "김치")

    def test_corrupt_db_is_loud_for_a_tokenless_query_too(self):
        # 짝: 위 무토큰 단언들(`\x00` → `[]`)은 **정상** 색인에서만 참이다. 고장난 DB 를
        # 무토큰 질의로 물으면 조용한 `[]` 가 아니라 소리가 나야 한다 — 안 그러면
        # 「고장은 500」이라는 계약이 질의어 하나로 우회된다
        self._seed_and_index([("http://a.test/", "<p>김치</p>")])
        with open(self.db_path, "wb") as fh:
            fh.write(b"NOT a sqlite file\n" * 64)
        with self.assertRaises(sqlite3.DatabaseError):
            search(self.db_path, "\x01")


class TestPassages(unittest.TestCase):
    """근거 문단 — `search()` 의 문서 순 그대로, 문서당 최대 1문단.

    문단 경계는 색인에 없고 `pages.html` 에만 있다. 그래서 색인 경로는 지나가지
    않는다 — DB 상태 판정(503·500·옛 색인)은 `search()` 것을 그대로 물려받는다.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = os.path.join(self.dir.name, "crawl.db")

    def _seed_and_index(self, rows):
        store = Store(self.db_path)
        for url, html in rows:
            store.upsert(url, html, 200)
        index_pages(self.db_path)

    # 갈림길 6 의 **잴 자** — 마크업 모양마다 «사람이 인용할 문단» 을 적어 둔다.
    # 이 표가 없어서 계획 48 이 네 반복 동안 결함을 못 봤다: 코퍼스
    # (`e2e/quality/corpus.json` 64건)가 평문이라 `passage_eval.build_index` 가
    # 문장마다 `<p>` 하나로 감싸고, 그 위에서 잰 정확도 100%·채택률 99.5% 는
    # **한 문장짜리 `<p>` 축만** 잰 값이다(`<br>` 0건 · `nav`/`ul`/`h*` 0건).
    # 세 안을 이 표로 재서 골랐다 (2026-09-02 개발 8 실측):
    #   현행 3/8 · 동점에 길이 6/8 · `br` 만 경계에서 빼기 5/8 ·
    #   블록 최소 길이 20자 4/8(**한 문장 `<p>` 를 통째로 버린다**) · 고른 둘 **8/8**
    _SHAPES = [
        ("문장 <p> — 코퍼스가 아는 유일한 모양",
         "<p>김치찌개는 한국의 대표적인 찌개다.</p><p>배추와 고춧가루를 넣는다.</p>",
         "김치찌개는 한국의 대표적인 찌개다."),
        ("nav 보일러플레이트",
         "<nav><a href=/>김치찌개</a></nav>"
         "<article><p>김치찌개 만드는 순서를 아래에 적는다.</p></article>",
         "김치찌개 만드는 순서를 아래에 적는다."),
        ("제목이 질의어 그 자체",
         "<h2>김치찌개</h2><p>배추를 절이고 양념을 버무려 김치찌개를 끓인다.</p>",
         "배추를 절이고 양념을 버무려 김치찌개를 끓인다."),
        ("<br> 로 줄만 나눈 문단",
         "<p>오늘은<br>김치찌개<br>내일은 된장찌개를 끓인다</p>",
         "오늘은 김치찌개 내일은 된장찌개를 끓인다"),
        ("<br> 문단이 둘 중 하나",
         "<p>재료를 준비한다<br>김치찌개 육수는 멸치로 낸다<br>끝</p><p>다른 요리 이야기</p>",
         "재료를 준비한다 김치찌개 육수는 멸치로 낸다 끝"),
        ("목록 항목이 진짜 답인 문서",  # 짧은 블록을 하한으로 막으면 이것이 죽는다
         "<p>오늘 만들 것을 적어 둔다.</p>"
         "<ul><li>된장찌개</li><li>김치찌개</li><li>계란말이</li></ul>",
         "김치찌개"),
        ("낱말마다 인라인 마크업",
         "<p>다른 이야기</p><p><b>김치</b><i>찌개</i>는 <em>겨울</em>에 특히 잘 어울린다.</p>",
         "김치찌개는 겨울에 특히 잘 어울린다."),
        ("표 칸이 질의어 그 자체",
         "<table><tr><td>메뉴</td><td>김치찌개</td></tr></table>"
         "<p>김치찌개 한 그릇은 오천원이다.</p>",
         "김치찌개 한 그릇은 오천원이다."),
        # 리뷰 5 — 위 여덟 행은 보일러플레이트를 **전부 본문 앞에, 본문보다 짧게** 뒀다.
        # 「길이」가 이득이 되는 방향만 표에 있으면 자가 한쪽으로만 눈금이 있는 것이고,
        # 그 자는 무엇을 재도 「길이」에 8/8 을 준다. 아래 셋이 방향을 짝짓는다
        ("본문 뒤에 오는 긴 푸터",  # 뒤 + 김
         "<article><p>김치찌개 만드는 순서를 아래에 적는다.</p></article>"
         "<footer>ⓒ 2026 김치찌개 백과 — 모든 권리 보유. 무단 전재와 재배포를 금합니다.</footer>",
         "김치찌개 만드는 순서를 아래에 적는다."),
        ("본문 앞에 오는 긴 사이드바",  # 앞 + 긴 · 태그는 `<div>` 라 보일러플레이트 이름표도 없다
         "<div>김치찌개 관련 글 모음과 인기 검색어 목록을 여기 모아 둔다</div>"
         "<article><p>김치찌개는 배추로 만든다.</p></article>",
         "김치찌개는 배추로 만든다."),
        ("긴 내비 링크 + 문단 안에 낀 <script>",  # 리뷰 5 가 든 합성 — 앞 + 긴
         "<nav><a href=/>김치찌개 레시피 모음 페이지 바로가기</a></nav>"
         "<article><p>김치찌개는<script>ad()</script>배추로 만든다.</p></article>",
         "김치찌개는 배추로 만든다."),
    ]

    def test_markup_shapes_yield_the_paragraph_a_reader_would_cite(self):
        self._seed_and_index([("http://t.test/%d" % i, html)
                              for i, (_, html, _) in enumerate(self._SHAPES)])
        # limit 을 표 길이에 묶는다 — 행을 더했는데 기본값 10 에 잘리면 그 행은
        # 재지 않은 채 조용히 통과한다
        got = {url: text for url, _t, _p, text
               in indexer.passages(self.db_path, "김치찌개", limit=len(self._SHAPES))}
        for i, (name, _html, want) in enumerate(self._SHAPES):
            with self.subTest(shape=name):
                self.assertEqual(got.get("http://t.test/%d" % i), want)

    def test_result_shape_is_url_title_position_text(self):
        self._seed_and_index([
            ("http://a.test/", "<title>요리</title><p>봄나물 무침</p><p>김치찌개 만드는 법</p>"),
        ])
        self.assertEqual(indexer.passages(self.db_path, "김치"),
                         [("http://a.test/", "요리", 1, "김치찌개 만드는 법")])

    def test_document_with_no_matching_block_is_not_returned(self):
        # 변이 M4(매치 없는 문서에 첫 블록을 대신 낸다)가 여기서 죽는다. 제목만
        # 매치된 문서는 `search()` 에 나오지만 **근거 문단이 없다** — 없는 근거를
        # 지어내면 사양 기능 8(정확도)이 첫 줄에서 무너진다
        self._seed_and_index([
            ("http://a.test/", "<title>김치 백과</title><p>봄에는 나물이 좋다</p>"),
            ("http://b.test/", "<title>요리</title><p>김치를 담갔다</p>"),
        ])
        hits = indexer.passages(self.db_path, "김치")
        self.assertEqual([h[0] for h in hits], ["http://b.test/"])  # 긍정 짝 — 빈 목록도 아니다

    def test_bigram_match_that_only_crosses_a_block_boundary_is_not_a_passage(self):
        # 색인의 2-gram 은 공백을 전부 지워 문단 경계도 넘는다(`먹는다 물을` → `다물`).
        # 문서는 나오지만 그 이웃을 담은 **블록은 없다** — 그러면 안 낸다
        self._seed_and_index([("http://a.test/", "<p>먹는다</p><p>물을</p>")])
        self.assertEqual([h[0] for h in search(self.db_path, "다물")], ["http://a.test/"])
        self.assertEqual(indexer.passages(self.db_path, "다물"), [])

    def test_picks_the_block_with_the_most_hits(self):
        self._seed_and_index([
            ("http://a.test/", "<p>김치 이야기</p><p>김치 담그기와 김치 보관</p><p>끝</p>"),
        ])
        self.assertEqual(indexer.passages(self.db_path, "김치")[0][2:],
                         (1, "김치 담그기와 김치 보관"))

    def test_a_tie_goes_to_the_body_paragraph(self):
        # 갈림길 6 — 보일러플레이트 블록(내비·제목·표 칸·푸터)이 **질의어만 담고
        # 문맥은 없는** 근거로 이기던 자리다. 점수가 같으면 `<p>` 가 근거로 낫다.
        # 길이로 갈랐더니 **짧은 내비는 이기고 긴 푸터·사이드바에는 졌다**(리뷰 5)
        self._seed_and_index([
            ("http://a.test/", "<nav><a>김치찌개</a></nav>"
                               "<article><p>김치찌개 만드는 순서를 적는다</p></article>"),
        ])
        self.assertEqual(indexer.passages(self.db_path, "김치찌개")[0][2:],
                         (1, "김치찌개 만드는 순서를 적는다"))

    def test_a_tie_between_two_paragraphs_goes_to_the_earlier_one(self):
        # 이름표까지 같을 때만 앞이 이긴다 — 부등호가 등호로 바뀌면 뒤가 이긴다.
        # 두 블록을 **같은 태그로** 맞춰야 이 단언이 «앞» 만 재는 것이 된다
        self._seed_and_index([("http://a.test/", "<p>김치 하나</p><p>김치 둘다</p>")])
        self.assertEqual(indexer.passages(self.db_path, "김치")[0][2:], (0, "김치 하나"))

    def test_position_counts_only_non_empty_blocks(self):
        # 변이 M5(빈 블록 포함으로 센다)가 여기서 죽는다. `position` 은
        # `extract_blocks()` 결과의 순번이어야 소비자가 같은 문단을 다시 찾는다
        self._seed_and_index([
            ("http://a.test/", "<p>가</p><p></p><p>   </p><p>김치찌개</p>"),
        ])
        self.assertEqual(indexer.passages(self.db_path, "김치")[0][2], 1)

    def test_document_order_follows_search(self):
        self._seed_and_index([
            ("http://a.test/", "<title>가</title><p>김치 한 번</p>"),
            ("http://b.test/", "<title>나</title><p>김치 김치 김치 세 번</p>"),
        ])
        self.assertEqual([h[0] for h in indexer.passages(self.db_path, "김치")],
                         [h[0] for h in search(self.db_path, "김치")])

    def test_english_match_is_case_insensitive(self):
        self._seed_and_index([("http://a.test/", "<p>intro</p><p>Python Tutorial</p>")])
        self.assertEqual(indexer.passages(self.db_path, "python")[0][3], "Python Tutorial")

    def test_limit_is_respected(self):
        self._seed_and_index([
            ("http://%d.test/" % i, "<p>머리말</p><p>김치 %d</p>" % i) for i in range(5)
        ])
        self.assertEqual(len(indexer.passages(self.db_path, "김치", limit=2)), 2)

    def test_no_match_returns_empty_list(self):
        self._seed_and_index([("http://a.test/", "<p>봄나물</p>")])
        self.assertEqual(indexer.passages(self.db_path, "김치"), [])

    def test_page_whose_html_vanished_is_skipped_not_a_traceback(self):
        # `docs` 는 `pages` 에서 파생된다 — 원본이 없어진 문서는 근거를 못 만든다
        self._seed_and_index([
            ("http://a.test/", "<p>김치 하나</p>"),
            ("http://b.test/", "<p>김치 둘</p>"),
        ])
        db = sqlite3.connect(self.db_path)
        self.addCleanup(db.close)
        db.execute("DELETE FROM pages WHERE url = 'http://a.test/'")
        db.commit()
        self.assertEqual([h[0] for h in indexer.passages(self.db_path, "김치")],
                         ["http://b.test/"])

    def test_html_beyond_the_cap_is_not_reparsed(self):
        # 자원 상한 — 요청 하나가 문서 10건을 **통째로 다시 파싱**한다. 안 자르면
        # 큰 문서 열 건이 500ms 예산을 넘긴다(실측: 2.5M자 302ms ×10 = 3.0초).
        # **천장은 «잘린 뒤의 문단은 못 찾는다»** 다 — 색인은 찾는데 근거는 못 낸다.
        # 여기 고정해 두지 않으면 상한을 지우거나 넓히는 변이가 안 죽는다
        self._seed_and_index([
            ("http://a.test/",
             "<title>요리</title><p>" + "봄" * indexer.MAX_PASSAGE_HTML
             + "</p><p>김치찌개</p>"),
        ])
        self.assertEqual([h[0] for h in search(self.db_path, "김치")],
                         ["http://a.test/"])  # 색인은 통짜 본문을 보므로 문서는 나온다
        self.assertEqual(indexer.passages(self.db_path, "김치"), [])

    def test_block_ending_exactly_at_the_cap_is_still_a_passage(self):
        # 경계 — 캡 **직전까지는 온전히** 읽는다. 한 글자 좁히는 변이가 여기서 죽는다
        # (마지막 글자가 정확히 캡의 끝자리라 `[:cap - 1]` 이면 '김치찌' 가 된다)
        tail = "<p>김치찌개"  # 닫는 태그가 없다 — 캡의 끝이 곧 문자열의 끝이다
        head = "<p>" + "봄" * (indexer.MAX_PASSAGE_HTML - len(tail) - 7) + "</p>"
        html = head + tail
        self.assertEqual(len(html), indexer.MAX_PASSAGE_HTML)  # 자를 것이 한 글자도 없다
        self._seed_and_index([("http://a.test/", html)])
        self.assertEqual(indexer.passages(self.db_path, "김치")[0][3], "김치찌개")

    def test_cut_inside_a_tag_does_not_leak_markup_into_the_passage(self):
        # 갭 탐색 — HTML 모양 축. 위 두 캡 테스트는 잘린 자리가 **평문 한가운데**
        # (`"봄" * cap`)라 「마크업 한가운데서 잘린다」를 아무도 안 밟았다.
        # `html.parser` 는 EOF 에 남은 미완성 태그를 **데이터로 흘린다** — 긴 속성값
        # (위키·CMS 의 `href`)이 캡에 걸리면 근거 문단이 `... <a href="xxx` 로 끝난다.
        # 소비자는 기계다: 출처가 붙은 텍스트를 달라고 했는데 마크업 조각을 받는다
        cap = indexer.MAX_PASSAGE_HTML
        filler = "<p>" + "봄" * (cap - 40) + "</p>"
        html = filler + '<p>김치찌개 <a href="' + "x" * 200 + '">링크</a></p>'
        self.assertEqual(html[cap - 1], "x")  # 캡이 속성값 한가운데 떨어진다
        self._seed_and_index([("http://a.test/", html)])
        text = indexer.passages(self.db_path, "김치")[0][3]
        self.assertNotIn("<", text)
        self.assertEqual(text, "김치찌개")

    def test_a_cut_whose_last_bracket_is_the_first_character_keeps_the_document(self):
        # 되감기의 뿌리 — 「`<` 가 있나」가 아니라 「그 `<` 가 안 닫혔나」다.
        # 문서 전체가 문단 하나면 캡 안의 마지막 `<` 는 **맨 앞의 `<p>`** 이고,
        # `html[:0]` 은 문서를 통째로 지운다 — 근거를 못 내는 게 아니라 문서가
        # `/passages` 에서 사라진다(잃는 원문 최대 캡 전부).
        # `<` 의 위치 축(맨앞·중간·없음) 중 «맨앞» 이다
        html = "<p>김치찌개 " + "가" * (indexer.MAX_PASSAGE_HTML + 5000) + "</p>"
        self._seed_and_index([("http://a.test/", html)])
        hits = indexer.passages(self.db_path, "김치")
        self.assertEqual([h[0] for h in hits], ["http://a.test/"])
        self.assertTrue(hits[0][3].startswith("김치찌개 가"), hits[0][3][:20])

    def test_markup_broken_in_the_source_leaks_even_under_the_cap(self):
        # 형제 경로 — 컷은 되감기가 필요한 **한 가지 원인일 뿐**이다. 원문 자체가
        # 안 닫힌 채로 크롤된 문서(잘린 응답·손으로 쓴 HTML)는 캡보다 짧아서
        # 캡 조건에 걸린 되감기를 지나지 않고, `html.parser` 는 EOF 의 미완성
        # 태그를 그대로 데이터로 흘린다. 소비자는 다시 마크업 조각을 받는다
        html = '<p>김치찌개 <a href="' + "x" * 200
        self.assertLess(len(html), indexer.MAX_PASSAGE_HTML)  # 캡 경로를 안 지난다
        self._seed_and_index([("http://a.test/", html)])
        text = indexer.passages(self.db_path, "김치")[0][3]
        self.assertNotIn("<", text)
        self.assertEqual(text, "김치찌개")

    def test_a_document_without_any_tag_keeps_its_last_character(self):
        # `<` 위치 축의 «없음». 되감기를 «`<` 가 `>` 보다 앞서지 않으면» 처럼
        # 등호를 넣어 쓰면 태그 0개 문서에서 둘 다 -1 이라 `html[:-1]` 이 되고
        # 마지막 글자가 조용히 사라진다 — 무조건 되감는 변이도 여기서 죽는다
        self._seed_and_index([("http://a.test/", "김치찌개 만드는 법")])
        self.assertEqual(indexer.passages(self.db_path, "김치")[0][3], "김치찌개 만드는 법")

    def test_an_unclosed_comment_holding_a_bracket_does_not_become_the_passage(self):
        # 갭 탐색(테스트 4) — 위 세 단언이 쓰는 입력의 모양이 **하나뿐이었다**:
        # 안 닫힌 `<` 뒤에 `>` 가 한 개도 없다. 그래서 되감기를 「마지막 `<` 가
        # 마지막 `>` 보다 뒤냐」로 물어도 다 걸렸다. 안 닫힌 것이 **자기 안에 `>` 를
        # 담을 수 있는 구성물**(주석)이면 비교가 뒤집혀 되감기가 아예 안 걸리고,
        # `html.parser` 는 EOF 의 미완성 주석을 데이터로 흘린다 — 화면에 안 보이는
        # 주석 내용이 근거 문단이 된다(사양 기능 8: 문단은 원문에서 읽히는 텍스트다)
        html = "<p>김치찌개 <!-- TODO: <a href=x> 옛 링크"
        self.assertLess(html.rfind("<"), html.rfind(">"))  # 되감기 조건을 안 지난다
        self._seed_and_index([("http://a.test/", html)])
        text = indexer.passages(self.db_path, "김치")[0][3]
        self.assertNotIn("<", text)
        self.assertEqual(text, "김치찌개")

    def test_an_unclosed_tag_whose_attribute_holds_a_bracket_does_not_leak(self):
        # 같은 뒤집힘을 **태그**로 밟는다. 위 주석 단언과 갈라 두는 이유는 고칠 자리가
        # 갈리기 때문이다 — 주석만 아는 수리(`<!--` 를 따로 찾는다)는 이쪽을 안 닫는다.
        # `title="a > b"`·`onclick="if(a>b)"` 는 위키·CMS 출력에 그대로 있다
        html = '<p>김치찌개 <a title="a > b" href="' + "x" * 200
        self.assertLess(html.rfind("<"), html.rfind(">"))  # 되감기 조건을 안 지난다
        self._seed_and_index([("http://a.test/", html)])
        text = indexer.passages(self.db_path, "김치")[0][3]
        self.assertNotIn("<", text)
        self.assertEqual(text, "김치찌개")

    def test_a_document_ending_in_a_truncated_entity_keeps_its_passage(self):
        # 위 둘을 닫는 가장 짧은 수리는 **파서에 묻는 것**이다(`feed()` 가 못 삼키고
        # 남긴 꼬리를 `close()` 전에 버린다). 그 수리는 잘린 엔티티도 함께 버리는데,
        # `convert_charrefs` 는 엔티티가 끝날 때까지 **앞의 텍스트까지** 붙들고 있어
        # 문단이 통째로 사라진다(실측: `<p>김치찌개 &am` → `[]`). 리뷰 3 이 잡은
        # «문서가 통째로 사라진다» 가 수리를 타고 되돌아오는 문이라 여기서 막는다 —
        # 잘린 엔티티는 평문이고, 평문은 마크업으로 안 샌다(`indexer.py` 주석의 계약)
        self._seed_and_index([("http://a.test/", "<p>김치찌개 &am")])
        self.assertEqual(indexer.passages(self.db_path, "김치")[0][3], "김치찌개 &am")

    def test_cap_and_passage_limit_together_stay_inside_the_budget(self):
        # **값** 가드다 — 위 둘은 fixture 를 상수에서 만들어 값과 함께 늘어나므로
        # "10만 → 100만" 변이를 못 잡는다(실측: 안 죽었다). 여기서 죽는다.
        # 손잡이는 둘이고 다른 파일에 산다 — 캡을 그대로 두고 `PASSAGE_LIMIT` 만
        # 올려도 예산이 깨지므로 곱해서 본다. 사양 성능 5 예산 500ms 의 25%.
        # **계수 옆에 그 숫자를 낸 입력의 모양을 적는다** — 앞의 0.118 은 «한글·태그
        # 촘촘» 한 벌에서만 재서 3배 틀렸다(계획 48 리뷰 2). 0.352 는 낱말마다
        # `<b>`/`<i>`/`<em>` 이 낀 위키·CMS 출력 모양의 1,000자당 값이다(리뷰 2 실측
        # 0.352 · 개발 5 재측 0.327 — 낮은 쪽으로 안 내린다).
        # **이것도 최악의 상한은 아니다**: `<p>가</p>` 만 반복하는 합성 문서가 0.489
        # (35,000자 ×10건 = 171ms). 골라 만든 모양이라 계수로 안 썼다 — 실물 크롤에서
        # 이 축이 보이면 계수가 아니라 파서를 고친다(`design_passage-api.md` 갈림길 5).
        from websearch import serve
        worst_ms = indexer.MAX_PASSAGE_HTML / 1000 * 0.352 * serve.PASSAGE_LIMIT
        self.assertLessEqual(worst_ms, 500 * 0.25, "%.0fms" % worst_ms)

    def test_missing_db_raises(self):
        with self.assertRaises(FileNotFoundError):
            indexer.passages(os.path.join(self.dir.name, "없는.db"), "김치")

    def test_stale_index_raises(self):
        # 503 경로 — 조용한 빈 목록은 "결과 0건" 과 구분되지 않는다.
        # `search()` 를 부르는 한 공짜로 물려받는다(자체 질의를 짜면 잃는다)
        store = Store(self.db_path)
        store.upsert("http://a.test/", "<title>김치</title><p>김치찌개</p>", 200)
        db = sqlite3.connect(self.db_path)
        self.addCleanup(db.close)
        db.execute(TestSchemaDrift.OLD_SCHEMA)
        db.execute("INSERT INTO docs(title, body, url) VALUES ('김치', '김치찌개', 'http://a.test/')")
        db.commit()
        with self.assertRaises(indexer.StaleIndexError):
            indexer.passages(self.db_path, "김치")

    def test_corrupt_db_is_loud(self):
        self._seed_and_index([("http://a.test/", "<p>김치</p>")])
        with open(self.db_path, "wb") as fh:
            fh.write(b"NOT a sqlite file\n" * 64)
        with self.assertRaises(sqlite3.DatabaseError):
            indexer.passages(self.db_path, "김치")

    def test_unindexed_db_returns_empty(self):
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        self.assertEqual(indexer.passages(self.db_path, "김치"), [])


class TestDbOpenIsAtomic(unittest.TestCase):
    """DB 를 여는 자리 하나 — `exists` 와 `connect` 사이에 창이 있으면 안 된다.

    창에 지면 나오는 것은 오답 하나가 아니라 **크기 0 의 빈 DB 파일**이다. 그것이
    남으면 그 뒤로 `os.path.exists` 가 참이라 503 이 영영 안 난다 — 흔적이 영구적이다.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = os.path.join(self.dir.name, "crawl.db")
        Store(self.db_path).upsert("http://a.test/", "<title>요리</title><p>김치</p>", 200)

    def _race(self):
        """`connect` 직전에 파일을 지운다 — 창이 열려 있으면 여기서 실제로 진다.

        WAL 사이드카까지 지우는 것은 `rm crawl.db*` 와 같다. 본 파일만 지우면 남은
        `-wal` 이 무슨 일을 하는지가 변수로 끼어들어 재는 것이 흐려진다.
        """
        real = sqlite3.connect

        def hook(path, **kw):
            for suffix in ("", "-wal", "-shm"):
                if os.path.exists(self.db_path + suffix):
                    os.remove(self.db_path + suffix)
            return real(path, **kw)

        return mock.patch.object(indexer.sqlite3, "connect", hook)

    def test_search_losing_the_race_raises_instead_of_returning_empty(self):
        index_pages(self.db_path)
        with self._race():
            with self.assertRaises(FileNotFoundError):
                search(self.db_path, "김치")
        self.assertFalse(os.path.exists(self.db_path), "빈 DB 파일이 남았다")

    def test_doc_count_losing_the_race_makes_no_file(self):
        index_pages(self.db_path)
        with self._race():
            self.assertEqual(indexer._doc_count(self.db_path), 0)
        self.assertFalse(os.path.exists(self.db_path), "빈 DB 파일이 남았다")

    def test_index_pages_losing_the_race_raises_instead_of_making_a_db(self):
        with self._race():
            with self.assertRaises(FileNotFoundError):
                index_pages(self.db_path)
        self.assertFalse(os.path.exists(self.db_path), "빈 DB 파일이 남았다")

    def test_doc_count_on_a_missing_db_is_zero_and_makes_no_file(self):
        # `_doc_count` 독스트링의 "DB 파일을 만들지 않는다" 를 재는 유일한 단언이다
        missing = os.path.join(self.dir.name, "없는.db")
        self.assertEqual(indexer._doc_count(missing), 0)
        self.assertFalse(os.path.exists(missing))

    def test_present_but_unopenable_path_is_not_reported_as_missing(self):
        # 권한·디렉터리는 기다린다고 낫지 않는다 — 503(FileNotFoundError)이 아니라
        # 원문 그대로의 OperationalError 여야 `serve` 가 500 으로 옮긴다 (계획 46 의 표)
        blocked = os.path.join(self.dir.name, "dir.db")
        os.mkdir(blocked)
        with self.assertRaises(sqlite3.OperationalError):
            search(blocked, "김치")
        with self.assertRaises(sqlite3.OperationalError):
            indexer._doc_count(blocked)

    def test_uri_metacharacters_in_path_open_the_real_file(self):
        # 경로를 URI 에 날것으로 끼우면 `#` 뒤가 잘려 **다른 파일**이 조용히 열린다.
        # 게다가 `?mode=rw` 도 함께 잘려나가 고치려던 버그가 그대로 부활한다.
        odd = os.path.join(self.dir.name, "a b#c?d.db")
        Store(odd).upsert("http://b.test/", "<title>요리</title><p>김치</p>", 200)
        index_pages(odd)
        self.assertEqual(len(search(odd, "김치")), 1)
        self.assertFalse(os.path.exists(os.path.join(self.dir.name, "a b")),
                         "`#` 앞에서 잘린 경로에 다른 DB 가 생겼다")

    def test_an_empty_db_path_is_missing_not_a_silent_temp_db(self):
        """리뷰 실측: `file:?mode=rw` 는 «없는 파일» 이 아니라 **이름 없는 임시 DB** 다.

        SQLite 가 빈 경로를 특례로 받아 조용히 성공하므로 `docs` 가 없는 새 DB 가 열리고
        `search` 는 `[]` 를 낸다 — `DB_PATH` 가 안 채워진 서버가 **503 대신 200 + 결과
        0건**을 내는 자리다. `os.path.exists("")` 로 먼저 보던 예전 코드에는 없던 구멍이라
        `_connect` 가 URI 를 지으면서 새로 생겼다. 세 호출부가 다 이 자리를 지난다.
        """
        with self.assertRaises(FileNotFoundError):
            search("", "김치")
        with self.assertRaises(FileNotFoundError):
            index_pages("")
        self.assertEqual(indexer._doc_count(""), 0)

    def test_a_relative_db_path_still_opens(self):
        """README 의 세 명령이 전부 `data/crawl.db` — **상대 경로**다(README.md:16-18,25).

        그런데 `_connect` 를 재는 단언은 위 여섯을 포함해 전부 `tempfile` 의 **절대 경로**
        하나에 걸려 있었다 — 재는 입력이 한 축뿐이라 다른 축이 통째로 우회한다.
        URI 를 `file:` 가 아니라 `file://` + 경로로 적는 변이(가장 자연스러운 형태다)는
        절대 경로에서는 멀쩡히 돌고 상대 경로에서만 죽는다. 실측: 단위 **504건 전부 초록**
        인 채 `python3 -m websearch.indexer data/crawl.db --query 김치` 가
        `invalid uri authority: data` 로 rc 1 을 냈다.
        """
        index_pages(self.db_path)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.dir.name)
        self.assertEqual(len(search("crawl.db", "김치")), 1)


class TestHangulBigrams(unittest.TestCase):
    """`_bigrams` — 한글 런의 문자 2-gram. 복합어 안쪽과 띄어쓰기 변형을 매치시키는 재료."""

    def test_bigrams_of_one_run(self):
        self.assertEqual(indexer._bigrams("일출봉"), "일출 출봉")

    def test_space_between_hangul_is_removed(self):
        # 띄어쓰기 변형의 핵심 — '올레 길' 과 '올레길' 이 같은 2-gram 을 낸다
        self.assertEqual(indexer._bigrams("올레 길"), indexer._bigrams("올레길"))
        self.assertEqual(indexer._bigrams("올레 길"), "올레 레길")

    def test_non_hangul_is_ignored(self):
        self.assertEqual(indexer._bigrams("Python tuple 3.9"), "")

    def test_hangul_runs_do_not_bridge_over_other_scripts(self):
        # '가나 abc 다라' 가 '나다' 를 만들면 없는 이웃을 지어내는 것이다
        self.assertEqual(indexer._bigrams("가나 abc 다라"), "가나 다라")

    def test_single_char_run_yields_nothing(self):
        self.assertEqual(indexer._bigrams("밥"), "")


class TestTokenizerMatching(unittest.TestCase):
    """`docs/design_tokenizer.md` 가 고른 안이 실제로 무엇을 매치시키는가."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = os.path.join(self.dir.name, "crawl.db")

    def _seed_and_index(self, rows):
        store = Store(self.db_path)
        for url, html in rows:
            store.upsert(url, html, 200)
        index_pages(self.db_path)

    def test_korean_compound_tail_matches(self):
        # 정답 문서에 '보관법' 이라는 낱말은 없다 — 복합어 뒷부분이다
        self._seed_and_index([
            ("http://a.test/", "<title>김치찌개보관법 냉장 사흘</title><p>완전히 식힌 뒤 넣는다</p>"),
        ])
        self.assertEqual([h[0] for h in search(self.db_path, "보관법")], ["http://a.test/"])

    def test_korean_compound_inner_matches(self):
        self._seed_and_index([
            ("http://a.test/", "<title>성산일출봉 새벽 해돋이</title><p>다섯 시에 문을 연다</p>"),
        ])
        self.assertEqual([h[0] for h in search(self.db_path, "일출봉")], ["http://a.test/"])

    def test_spacing_variant_matches_both_directions(self):
        self._seed_and_index([
            ("http://spaced.test/", "<title>올레 길 7코스</title><p>표지 리본을 따라간다</p>"),
            ("http://joined.test/", "<title>올레길 안내소</title><p>지도를 나눠 준다</p>"),
        ])
        for query in ("올레길", "올레 길"):
            self.assertEqual(
                sorted(h[0] for h in search(self.db_path, query)),
                ["http://joined.test/", "http://spaced.test/"],
                query,
            )

    def test_compound_tail_matches_regardless_of_word_order(self):
        # 리뷰 발견: 질의를 통째로 이어 붙여 하나의 인접 구절로 만들면 2-gram 분기가
        # **어절이 그 순서로 붙어 있을 때만** 산다. 어순만 바꾸면 0건이 됐다
        self._seed_and_index([
            ("http://a.test/", "<title>김치찌개보관법 냉장 사흘</title><p>완전히 식힌 뒤</p>"),
        ])
        for query in ("보관법 냉장", "냉장 보관법"):
            self.assertEqual([h[0] for h in search(self.db_path, query)],
                             ["http://a.test/"], query)

    def test_compound_tail_matches_beside_another_word(self):
        self._seed_and_index([
            ("http://a.test/", "<title>올레 길 7코스 안내</title><p>제주를 걷는다</p>"),
        ])
        # '7코스' 는 한글이 아닌 문자를 품는다 — 옛 재작성은 질의 전체가 한글일 때만
        # 2-gram 분기를 켰으므로 숫자 하나에 분기가 통째로 꺼졌다
        for query in ("올레길 안내", "7코스 올레길"):
            self.assertEqual([h[0] for h in search(self.db_path, query)],
                             ["http://a.test/"], query)

    def test_english_inflection_matches(self):
        self._seed_and_index([
            ("http://a.test/", "<title>Lists and the tuple type</title>"
                               "<p>A tuple cannot be changed after it is made.</p>"),
        ])
        self.assertEqual([h[0] for h in search(self.db_path, "tuples")], ["http://a.test/"])

    def test_snippet_shows_source_text_not_bigrams(self):
        # bigram 열이 snippet(-1) 에 뽑히면 화면에 '김치 치찌 찌개' 가 나온다.
        # 부정 단언만 두면 스니펫이 빈 문자열이어도 통과하므로 긍정 짝을 함께 건다
        self._seed_and_index([
            ("http://a.test/", "<title>김치찌개보관법 냉장 사흘이 한계다</title>"
                               "<p>완전히 식힌 뒤 뚜껑을 덮어 넣는다</p>"),
        ])
        url, title, snippet = search(self.db_path, "보관법")[0]
        self.assertNotIn("치찌 찌개", snippet)
        # 긍정 짝 — 스니펫이 빈 문자열이어도 위 부정 단언은 참이다.
        # 2-gram 으로만 매치된 문서라 제목·본문 어느 쪽도 매치되지 않았고,
        # 계약대로 본문 앞부분이 나온다. 질의어는 title 로 이미 보인다
        self.assertIn("완전히 식힌 뒤", snippet)
        self.assertEqual(title, "김치찌개보관법 냉장 사흘이 한계다")

    def test_snippet_is_not_empty_when_document_has_no_body(self):
        # 리뷰 발견: 2-gram 으로만 매치된 문서는 본문 스니펫을 쓰는데, 본문이 없는
        # 문서(링크 페이지·짧은 글)는 빈 문자열이 그대로 화면에 나간다
        self._seed_and_index([("http://a.test/", "<title>김치찌개보관법 냉장 사흘</title>")])
        self.assertIn("김치찌개보관법", search(self.db_path, "보관법")[0][2])

    def test_snippet_still_comes_from_title_when_only_title_matches(self):
        # 계약 유지 — TestSearch.test_snippet_comes_from_matching_column 과 같은 계약
        self._seed_and_index([
            ("http://a.test/", "<title>김치 담그는 법</title><p>봄에는 나물이 좋다</p>"),
        ])
        self.assertIn("김치", search(self.db_path, "김치")[0][2])

    def test_mixed_script_query_still_requires_every_term(self):
        # bigram 분기를 조건 없이 OR 로 붙이면 '김치' 만 있는 문서가 딸려 들어온다
        self._seed_and_index([
            ("http://both.test/", "<title>김치</title><p>Learning Python for beginners</p>"),
            ("http://ko.test/", "<title>김치</title><p>배추와 고춧가루</p>"),
        ])
        self.assertEqual([h[0] for h in search(self.db_path, "김치 python")],
                         ["http://both.test/"])

    def test_korean_two_word_query_still_requires_every_term(self):
        self._seed_and_index([
            ("http://a.test/", "<title>김치 담그기</title><p>배추를 절인다</p>"),
            ("http://b.test/", "<title>김치 볶음밥</title><p>밥을 넣고 볶는다</p>"),
        ])
        self.assertEqual([h[0] for h in search(self.db_path, "김치 볶음")], ["http://b.test/"])

    def test_bigram_column_is_not_returned_as_a_field(self):
        # 공개 계약: (url, title, snippet) 셋뿐이다 — 열이 늘어도 새어 나오지 않는다
        self._seed_and_index([("http://a.test/", "<title>김치</title><p>맛있다</p>")])
        self.assertEqual(len(search(self.db_path, "김치")[0]), 3)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = os.path.join(self.dir.name, "crawl.db")

    def test_no_args_is_usage_error(self):
        self.assertEqual(indexer.main(["prog"]), 2)

    def test_missing_db_is_error_not_traceback(self):
        # 환경이 안 된 것이지 명령줄이 틀린 게 아니다 → rc 1 (계약은 README)
        self.assertEqual(indexer.main(["prog", os.path.join(self.dir.name, "없는.db")]), 1)

    def test_db_without_pages_is_error_not_traceback(self):
        other = os.path.join(self.dir.name, "남의.db")
        sqlite3.connect(other).execute("CREATE TABLE junk(x)")
        self.assertEqual(indexer.main(["prog", other]), 1)

    def test_query_without_value_is_error(self):
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        self.assertEqual(indexer.main(["prog", self.db_path, "--query"]), 2)

    def test_no_hits_says_so(self):
        # 리뷰 발견: 침묵 + exit 0 이면 "결과 없음" 과 "명령이 깨짐" 을 구분할 수 없다
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        indexer.main(["prog", self.db_path])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(indexer.main(["prog", self.db_path, "--query", "우주선"]), 0)
        self.assertNotEqual(buf.getvalue().strip(), "")

    def test_removal_is_reported_not_silent(self):
        # 리뷰 발견: 문서를 뺀 실행도 "0 문서 색인" 으로만 찍혀 아무 일도 없던 것과 구분이 안 된다
        store = Store(self.db_path)
        store.upsert("http://a.test/", "<p>김치</p>", 200)
        indexer.main(["prog", self.db_path])
        store.upsert("http://a.test/", '<meta name="robots" content="noindex"><p>김치</p>', 200)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(indexer.main(["prog", self.db_path]), 0)
        self.assertIn("1", buf.getvalue().split("\n")[-2])
        self.assertIn("noindex", buf.getvalue())

    def test_interrupt_is_a_one_line_message_and_rc_130(self):
        # 계획 37 스텝 2: Ctrl-C 는 트레이스백이 아니라 rc 130 과 한 줄 안내다.
        # 스텝 1(재구축을 한 트랜잭션으로) 뒤라야 "색인은 바뀌지 않았다" 가 두 갈래 다 참이다
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        buf = io.StringIO()
        with mock.patch.object(indexer, "index_pages", side_effect=KeyboardInterrupt), \
                contextlib.redirect_stderr(buf):
            self.assertEqual(indexer.main(["prog", self.db_path]), 130)
        out = buf.getvalue()
        self.assertNotIn("Traceback", out)
        self.assertIn("중단", out)
        self.assertIn("바뀌지 않았다", out)  # 안내가 무엇이 참인지 말한다
        self.assertEqual(len(out.strip().split("\n")), 1)  # 한 줄

    def test_interrupt_branch_does_not_swallow_other_base_exceptions(self):
        # 대조군: 잡는 것은 KeyboardInterrupt **만** 이다. BaseException 으로 넓히면
        # SystemExit 까지 삼켜 다른 계약이 된다 (계획 27 M4 의 교훈)
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        with mock.patch.object(indexer, "index_pages", side_effect=SystemExit(3)):
            with self.assertRaises(SystemExit):
                indexer.main(["prog", self.db_path])

    def test_index_waits_out_a_write_lock_instead_of_dying(self):
        # 계획 39 스텝 1: crawl 이 쓰기 락을 쥔 채여도 색인은 죽지 않고 기다린다.
        # sqlite3 기본 timeout 은 5초라 8초 락에서 트레이스백이 났다 — store.py:22 가
        # 이미 고른 30초를 indexer 의 연결도 그대로 쓴다
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        holder = subprocess.Popen(
            [sys.executable, "-c",
             "import sqlite3, sys, time\n"
             "db = sqlite3.connect(sys.argv[1])\n"
             "db.execute('BEGIN IMMEDIATE')\n"
             "print('locked', flush=True)\n"
             "time.sleep(8)\n",
             self.db_path],
            stdout=subprocess.PIPE, text=True)
        with holder:
            holder.stdout.readline()  # 락을 실제로 쥔 것을 보고 나서 색인한다
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(indexer.main(["prog", self.db_path]), 0)

    def test_lock_past_timeout_is_a_message_and_rc_1(self):
        # 계획 39 스텝 2: 30초를 기다려도 안 풀린 락은 트레이스백이 아니라 rc 1 과 복구법이다.
        # 실측 35초 락으로 잰 갈래를 단위에서는 같은 예외로 세운다(35초를 매번 기다릴 수 없다)
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        buf = io.StringIO()
        with mock.patch.object(indexer, "index_pages",
                               side_effect=sqlite3.OperationalError("database is locked")), \
                contextlib.redirect_stderr(buf):
            self.assertEqual(indexer.main(["prog", self.db_path]), 1)
        out = buf.getvalue()
        self.assertNotIn("Traceback", out)
        self.assertIn("잠겨", out)  # 락이라고 말한다
        self.assertIn("다시 돌린다", out)  # 복구법을 말한다

    def test_not_a_database_is_a_message_and_rc_1(self):
        # 형제 구멍(계획 39 3절 D): 진짜 DB 가 아닌 파일도 트레이스백으로 새면 안 된다.
        # 락이 아니므로 락 안내를 내면 오진이다 — 원문을 그대로 보인다
        bogus = os.path.join(self.dir.name, "가짜.db")
        with open(bogus, "wb") as f:
            f.write(b"not a database at all" * 100)
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            self.assertEqual(indexer.main(["prog", bogus]), 1)
        out = buf.getvalue()
        self.assertNotIn("Traceback", out)
        self.assertNotIn("잠겨", out)
        self.assertIn("not a database", out)  # 원문이 남는다

    def test_query_on_a_not_a_database_file_is_a_message_and_rc_1(self):
        # 갭 탐색: 새 갈래를 **색인 경로에서만** 쟀다. `--query` 도 같은 세 연결 중
        # 하나(`search`)를 쓰므로 계약이 같아야 한다. 갈래를 티켓이 말한 경로로만
        # 좁히면(`query is None` 안으로 넣으면) 이 진입점만 조용히 트레이스백이 된다
        bogus = os.path.join(self.dir.name, "가짜.db")
        with open(bogus, "wb") as f:
            f.write(b"not a database at all" * 100)
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            self.assertEqual(indexer.main(["prog", bogus, "--query", "김치"]), 1)
        out = buf.getvalue()
        self.assertNotIn("Traceback", out)
        self.assertIn("not a database", out)
        self.assertEqual(len(out.strip().split("\n")), 1)  # 한 줄

    def test_every_connection_waits_the_same_thirty_seconds(self):
        # 리뷰 변이 M6: `_doc_count`·`search` 의 `timeout=30` 을 지워도 461건이 전부
        # 초록이었다 — 락 테스트는 `index_pages` 경로만 지난다. 그 둘은 읽기 전용이고
        # WAL 에서 읽기는 락에 안 막히므로(실측 0.02초) 행동으로는 못 잰다.
        # 그래서 값을 고정한다 — 안 그러면 지워져도 아무도 안 운다(`digest.md` `[7]`)
        Store(self.db_path).upsert("http://a.test/", "<title>요리</title><p>김치</p>", 200)
        seen = []
        real = sqlite3.connect
        with mock.patch.object(indexer.sqlite3, "connect",
                               lambda path, **kw: (seen.append(kw.get("timeout")),
                                                   real(path, **kw))[1]), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(indexer.main(["prog", self.db_path]), 0)  # _doc_count·index_pages
            self.assertEqual(indexer.main(["prog", self.db_path, "--query", "김치"]), 0)  # search
        self.assertGreaterEqual(len(seen), 3)  # 세 연결을 전부 지났다
        self.assertEqual(set(seen), {30}, "store.py:22 와 같은 30초가 아닌 연결이 있다")

    def test_index_then_query(self):
        Store(self.db_path).upsert("http://a.test/", "<title>요리</title><p>김치</p>", 200)
        self.assertEqual(indexer.main(["prog", self.db_path]), 0)
        self.assertEqual(indexer.main(["prog", self.db_path, "--query", "김치"]), 0)
