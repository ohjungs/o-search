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

    def test_one_page_with_an_unknown_marked_section_does_not_abort_the_run(self):
        # 갭 탐색(테스트 3) — 단언 자리는 **가장 깊은 모양**이다. `extract` 단위가
        # 예외를 막아도, 값이 걸린 곳은 여기다: `index_pages()` 는 문서마다 try 가
        # 없고 `commit()` 이 루프 **끝**에 있어, 페이지 한 장이 터지면 그 실행이 넣던
        # 색인이 통째로 사라진다. 크롤 HTML 은 신뢰 경계라 «남이 쓴 여덟 글자»다
        self._seed_and_index([
            ("http://bad.test/", "<title>깨진 선언</title><p>배추김치를 담근다<![foo]>"),
            ("http://ok.test/", "<title>정상</title><p>김치찌개는 배추로 만든다.</p>"),
        ])
        self.assertEqual(sorted(h[0] for h in search(self.db_path, "김치")),
                         ["http://bad.test/", "http://ok.test/"])
        # 근거 문단 경로도 같은 파서를 지난다 — `/passages` 가 500 이 되던 자리
        self.assertEqual(indexer.passages(self.db_path, "배추김치")[0][3], "배추김치를 담근다")

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
    # 표는 **19행**이고 그중 넷은 지금 규칙이 못 맞춘다 — 아래 `_UNMATCHED_SHAPES`.
    # 동점 규칙 셋을 이 19행으로 재서 골랐다 (2026-09-02 개발 10 실측):
    #   점수만 11/19 · **동점에 길이 15/19(고름)** · 동점에 태그가 `p` 인가 12/19
    # 열한 행만 볼 때는 이름표가 11/11 로 이겼는데(개발 9), 그 열한 행은 정답이 늘
    # `<p>` 라 눈금이 한 방향뿐이었다. 방향을 짝지은 여덟을 더하니 이름표는 1/8 이다
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
        # 리뷰 6 — 위 여덟 행은 **정답이 늘 `<p>` 이고 경쟁자는 한 번도 `<p>` 가 아니다**.
        # 그 표 위에서는 「태그가 `p` 인가」가 8/8 을 받지만, 그것은 자에 눈금이 한
        # 방향뿐이라 그렇다. 아래 일곱이 반대쪽이다 — 정답이 `<div>`·`<li>`·`<td>`·
        # `<section>` 이거나 **보일러플레이트가 `<p>`** 인 모양.
        # 일곱 전부 **진짜 동점**(두 블록의 점수가 같다)이라 동점 규칙만이 답을 가른다
        ("본문이 <div> · 푸터가 <p>",  # 뒤 + 짧다 · 이름표는 보일러플레이트 쪽이 `p`
         "<article><div>김치찌개는 배추와 고춧가루로 끓인다.</div></article>"
         "<footer><p>ⓒ 2026 김치찌개 백과</p></footer>",
         "김치찌개는 배추와 고춧가루로 끓인다."),
        ("본문 앞의 짧은 광고 <p>",  # `<p>` 대 `<p>` — 실물에서 가장 흔한 동점 모양
         "<p>광고 김치찌개 특가</p>"
         "<article><p>김치찌개는 배추로 만드는 한국의 대표 음식이다.</p></article>",
         "김치찌개는 배추로 만드는 한국의 대표 음식이다."),
        ("빵부스러기 <p> · 답은 <li>",
         "<p>홈 &gt; 요리 &gt; 김치찌개</p>"
         "<ul><li>김치찌개 끓이는 순서를 아래에 적는다</li><li>계란말이</li></ul>",
         "김치찌개 끓이는 순서를 아래에 적는다"),
        ("표가 본문 · 앞에 짧은 안내 <p>",
         "<p>김치찌개 안내</p>"
         "<table><tr><td>김치찌개 한 그릇은 오천원이고 공기밥은 따로다</td></tr></table>",
         "김치찌개 한 그릇은 오천원이고 공기밥은 따로다"),
        ("답은 <section> · 뒤에 관련글 <p>",
         "<section>김치찌개를 끓이려면 먼저 배추를 잘게 썬다</section>"
         "<p>관련 글: 김치찌개</p>",
         "김치찌개를 끓이려면 먼저 배추를 잘게 썬다"),
        ("본문 <p> · 뒤에 짧은 푸터 <p>",  # 짝 — 여기서는 이름표도 순서도 맞는다
         "<article><p>김치찌개는 배추로 만드는 한국의 대표 음식이다.</p></article>"
         "<p>ⓒ 김치찌개 백과</p>",
         "김치찌개는 배추로 만드는 한국의 대표 음식이다."),
        ("답이 <div> 로 먼저 · 뒤에 관련글 <p>",
         "<div>김치찌개는 배추로 만든다는 것이 정설이다.</div><p>관련 글: 김치찌개</p>",
         "김치찌개는 배추로 만든다는 것이 정설이다."),
    ]

    # **못 맞추는 넷** (name, html, 사람이 인용할 문단, **오늘 나오는 오답**).
    # 「길이」는 보일러플레이트가 **본문보다 길면** 진다 — 방향이 하나뿐이라 그렇다.
    # 이름표로 바꾸면 이 넷 중 셋은 살지만 위 열다섯 중 넷이 죽어 12/19 로 더 나쁘다.
    # 어느 손잡이도 19행을 못 맞춘다 — 그러니 **행을 지우거나 정답을 낮추지 않고**
    # 오늘의 오답을 적어 둔다. 규칙이 나아지면 여기가 빨개진다
    _UNMATCHED_SHAPES = [
        ("본문 뒤에 오는 긴 푸터",  # 뒤 + 길다
         "<article><p>김치찌개 만드는 순서를 아래에 적는다.</p></article>"
         "<footer>ⓒ 2026 김치찌개 백과 — 모든 권리 보유. 무단 전재와 재배포를 금합니다.</footer>",
         "김치찌개 만드는 순서를 아래에 적는다.",
         "ⓒ 2026 김치찌개 백과 — 모든 권리 보유. 무단 전재와 재배포를 금합니다."),
        ("본문 앞에 오는 긴 사이드바",  # 앞 + 길다 · 태그는 `<div>` 라 이름표도 안 가른다
         "<div>김치찌개 관련 글 모음과 인기 검색어 목록을 여기 모아 둔다</div>"
         "<article><p>김치찌개는 배추로 만든다.</p></article>",
         "김치찌개는 배추로 만든다.",
         "김치찌개 관련 글 모음과 인기 검색어 목록을 여기 모아 둔다"),
        ("긴 내비 링크 + 문단 안에 낀 <script>",  # 리뷰 5 가 든 합성 — 앞 + 길다
         "<nav><a href=/>김치찌개 레시피 모음 페이지 바로가기</a></nav>"
         "<article><p>김치찌개는<script>ad()</script>배추로 만든다.</p></article>",
         "김치찌개는 배추로 만든다.",
         "김치찌개 레시피 모음 페이지 바로가기"),
        ("답은 짧은 <blockquote> · 뒤에 긴 저작권 <p>",  # 리뷰 6 의 여덟 중 유일한 실패
         "<section><blockquote>김치찌개는 겨울의 음식이다</blockquote></section>"
         "<p>이 글의 무단 전재를 금합니다. 김치찌개 관련 문의는 편집부로 연락 바랍니다.</p>",
         "김치찌개는 겨울의 음식이다",
         "이 글의 무단 전재를 금합니다. 김치찌개 관련 문의는 편집부로 연락 바랍니다."),
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

    def test_shapes_the_tie_rule_cannot_match_are_recorded_not_hidden(self):
        # 갈림길 6 의 **천장**을 눈에 보이는 자리에 둔다. 표에서 빼면 「길이」가
        # 19행 중 15행짜리 규칙이라는 사실이 사라지고, 다음 반복이 15/15 를 보고
        # 「닫혔다」고 읽는다 — 계획 48 이 네 반복 동안 결함을 못 본 방식 그대로다.
        # 오늘의 **오답을 그대로** 못박아 둔다: 규칙이 나아지면 여기가 빨개져 행이
        # 위 표로 옮겨 가고, 조용히 **다른** 오답으로 바뀌어도 걸린다
        self._seed_and_index([("http://t.test/%d" % i, html)
                              for i, (_, html, _, _) in enumerate(self._UNMATCHED_SHAPES)])
        got = {url: text for url, _t, _p, text
               in indexer.passages(self.db_path, "김치찌개",
                                   limit=len(self._UNMATCHED_SHAPES))}
        for i, (name, _html, want, today) in enumerate(self._UNMATCHED_SHAPES):
            with self.subTest(shape=name):
                # 적어 둔 것이 **오답**이라는 것 자체가 계약이다 — 여기에 정답을
                # 적어 넣어 «못 맞춤» 을 조용히 지우는 변이가 이 줄에서 죽는다
                self.assertNotEqual(want, today)
                self.assertEqual(got.get("http://t.test/%d" % i), today)

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

    def test_hidden_text_never_becomes_the_passage(self):
        # 계획 51 — 숨은 블록은 질의어를 본문보다 촘촘히 담아 밀도 규칙을
        # **확정적으로** 이겼다. 다섯 모양 전부에서 본문 문단이 나와야 하고,
        # 숨은 블록**만** 질의어를 담은 문서는 문단이 **0개**다 — 첫 블록이나
        # 본문 앞부분으로 대신하면 사양 기능 8(근거 정확도)이 첫 줄에서 무너진다.
        # 감점(갈림길 C)으로 바꾸는 변이가 여기서 죽는다: 밀도가 높으면 여전히 이긴다
        shapes = [
            ("template", "<template>%s</template>"),
            ("hidden 속성", "<div hidden>%s</div>"),
            ("aria-hidden", '<div aria-hidden="true">%s</div>'),
            ("display:none", '<div style="display:none">%s</div>'),
            ("font-size:0", '<div style="font-size:0">%s</div>'),
        ]
        hidden = "<p>김치찌개 김치찌개 김치찌개</p>"
        self._seed_and_index(
            [("http://t.test/%d" % i, wrap % hidden + "<p>김치찌개는 배추로 만든다.</p>")
             for i, (_, wrap) in enumerate(shapes)]
            + [("http://only.test/", "<title>요리</title>"
                + shapes[1][1] % hidden + "<p>봄나물 무침</p>"),
               # 리뷰 2 `[R51-3]` 이 **실제 임시 DB 로** 잡은 자리 — 종료 태그가
               # 생략된 `<p hidden>` 안에 커스텀 요소가 끼면 암묵적 닫기가 숨김을
               # 풀어 숨은 텍스트가 **근거 문단이 됐다**. 밀도 규칙은 질의어를 채운
               # 숨은 블록을 확정적으로 고르므로 계약이 바로 깨진다
               ("http://custom.test/",
                "<title>요리</title><p hidden>김치찌개 김치찌개"
                "<my-widget>김치찌개 김치찌개</my-widget>"
                "<p>김치찌개는 배추로 만든다.</p>")])
        got = {url: text for url, _t, _p, text
               in indexer.passages(self.db_path, "김치찌개", limit=len(shapes) + 2)}
        self.assertEqual(got.get("http://custom.test/"), "김치찌개는 배추로 만든다.")
        for i, (name, _wrap) in enumerate(shapes):
            with self.subTest(shape=name):
                self.assertEqual(got.get("http://t.test/%d" % i),
                                 "김치찌개는 배추로 만든다.")
        self.assertNotIn("http://only.test/", got)
        # 색인은 안 건드렸다 — 그 문서는 검색 결과에 **계속 나온다**
        self.assertIn("http://only.test/",
                      [h[0] for h in search(self.db_path, "김치찌개")])

    def test_bigram_match_that_only_crosses_a_block_boundary_is_not_a_passage(self):
        # 색인의 2-gram 은 공백을 전부 지워 문단 경계도 넘는다(`먹는다 물을` → `다물`).
        # 문서는 나오지만 그 이웃을 담은 **블록은 없다** — 그러면 안 낸다
        self._seed_and_index([("http://a.test/", "<p>먹는다</p><p>물을</p>")])
        self.assertEqual([h[0] for h in search(self.db_path, "다물")], ["http://a.test/"])
        self.assertEqual(indexer.passages(self.db_path, "다물"), [])

    def test_a_spacing_variant_document_still_gets_a_passage(self):
        # 갭 탐색(테스트 5) — 변이 «2-gram 바늘 삭제» 가 573건 전부 초록으로
        # 살아남았다. 색인은 한글 2-gram 으로 띄어쓰기 변형을 매치하는데
        # (`김치찌개` ↔ `김치 찌개`), 문단 고르기가 **날 질의어만** 세면 그 문서는
        # 어느 블록도 점수 0 이라 **근거 없이 통째로 빠진다** — 검색에는 나오는데
        # 근거는 0건이다(사양 기능 8 · 채택률). 부정 짝(`search` 는 낸다)을 같이 잰다
        self._seed_and_index([
            ("http://a.test/", "<title>요리</title><p>다른 이야기다</p>"
                               "<p>김치 찌개를 끓이는 법을 적는다</p>"),
        ])
        self.assertEqual([h[0] for h in search(self.db_path, "김치찌개")],
                         ["http://a.test/"])
        self.assertEqual(indexer.passages(self.db_path, "김치찌개")[0][2:],
                         (1, "김치 찌개를 끓이는 법을 적는다"))

    def test_picks_the_block_with_the_most_hits(self):
        self._seed_and_index([
            ("http://a.test/", "<p>김치 이야기</p><p>김치 담그기와 김치 보관</p><p>끝</p>"),
        ])
        self.assertEqual(indexer.passages(self.db_path, "김치")[0][2:],
                         (1, "김치 담그기와 김치 보관"))

    def test_a_tie_goes_to_the_body_paragraph(self):
        # 갈림길 6 — 보일러플레이트 블록(내비·제목·표 칸)이 **질의어만 담고 문맥은
        # 없는** 근거로 이기던 자리다. 점수가 같으면 **긴 블록**이 근거로 낫다.
        # 이 방향(앞·짧다)만 맞고 반대(뒤·길다)는 `_UNMATCHED_SHAPES` 에 있다
        self._seed_and_index([
            ("http://a.test/", "<nav><a>김치찌개</a></nav>"
                               "<article><p>김치찌개 만드는 순서를 적는다</p></article>"),
        ])
        self.assertEqual(indexer.passages(self.db_path, "김치찌개")[0][2:],
                         (1, "김치찌개 만드는 순서를 적는다"))

    def test_a_tie_between_two_paragraphs_goes_to_the_earlier_one(self):
        # 길이까지 같을 때만 앞이 이긴다 — 부등호가 등호로 바뀌면 뒤가 이긴다.
        # 두 블록을 **같은 길이로** 맞춰야 이 단언이 «앞» 만 재는 것이 된다
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
        # 올려도 예산이 깨지므로 곱해서 본다. 사양 성능 5 예산 500ms 의 **1/3**.
        # **계수 옆에 그 숫자를 낸 입력의 모양을 적는다** — 앞의 0.118 은 «한글·태그
        # 촘촘» 한 벌에서만 재서 3배 틀렸다(계획 48 리뷰 2). 0.44 는 낱말마다
        # `<b>`/`<i>`/`<em>` 이 낀 위키·CMS 출력 모양의 1,000자당 값이다(계획 48 리뷰
        # 2 실측 0.352 · 개발 5 재측 0.327 · **계획 51 리뷰 2 재측 0.439 · 개발 3
        # 재측 0.413** — 낮은 쪽으로 안 내린다).
        # **배정치가 25% → 1/3 로 움직였다**(계획 51 리뷰 2 [R51-4]). 계획 51 이 숨김
        # 판정과 암묵적 닫기를 넣어 계수가 0.352 → 0.44 로 올랐고, 캡도 `PASSAGE_LIMIT`
        # 도 안 건드렸다. 이 선을 25% 로 도로 조이려면 캡을 28,000 으로 내려야 하고
        # 그것은 «긴 문서의 뒷부분 근거» 를 더 자르는 별개 판단이다. 실물 코퍼스 p95 는
        # 1.51 → 1.54ms(예산의 0.3%)라 이 154ms 는 **캡 최악 모양의 상한**이지 실측이 아니다.
        # **«모양» 으로는 재현이 안 돼 이 숫자가 세 번 낡았다 — 축은 태그 밀도다**
        # (테스트 3 재측정): ms/1000자 ≈ 0.0025 × 태그/1000자. 0.44 는 **태그
        # 169개/1000자** 한 점이고 오늘 0.436 이라 여전히 참인데, 같은 말로 태그
        # 200개/1000자 벌을 만들면 0.502(176ms)라 이 배정치를 넘는다. **캡 안 최악은
        # 이 축의 끝**이다 — `<li>가</li>` 0.535 · `<p>가</p>` 0.665 · 안 닫은
        # `<p>가` **0.901**(10건 **315ms · 예산의 63%**)로 위 154ms 의 **2.1배**.
        # 그래서 이 단언의 1/3 은 «여유» 가 아니라 그 **모양 배수를 흡수하는 자리**다 —
        # 1/3 을 지키면 최악 모양이 500ms 안에 든다(154 × 2.1 = 323ms). 계수를 최악
        # 모양으로 갈아 끼우면 캡을 18,000 으로 내려야 초록인데, 그것은 «긴 문서의
        # 뒷부분 근거» 를 반으로 자르는 계획 몫이다(`design_passage-api.md` 갈림길 5).
        from websearch import serve
        worst_ms = indexer.MAX_PASSAGE_HTML / 1000 * 0.44 * serve.PASSAGE_LIMIT
        self.assertLessEqual(worst_ms, 500 / 3, "%.0fms" % worst_ms)

    def test_missing_db_raises(self):
        with self.assertRaises(FileNotFoundError):
            indexer.passages(os.path.join(self.dir.name, "없는.db"), "김치")

    def test_db_without_pages_raises_for_every_query_shape(self):
        # 색인 `docs` 는 살아 있는데 원본 창고가 통째로 없는 DB. 세 질의가 **같은**
        # 예외를 내는 것이 요점이다 — 판정이 `hits` 의 비어 있음에 달리면 같은 DB 가
        # `q=김치찌개` 면 터지고 `q=%01` 이면 조용한 `[]` 로 갈린다(계획 47 과 같은 고장).
        self._seed_and_index([("http://a.test/", "<title>김치</title><p>김치찌개</p>")])
        db = sqlite3.connect(self.db_path)
        self.addCleanup(db.close)
        db.execute("DROP TABLE pages")
        db.commit()
        for query in ("김치찌개", "zzzznope", "\x01"):
            with self.subTest(query=query):
                with self.assertRaises(indexer.NoCrawlDataError):
                    indexer.passages(self.db_path, query)

    def test_db_without_html_column_raises_for_every_query_shape(self):
        # 창고는 있는데 **열 하나가 없는** DB. HTTP 밖에서도 갈림이 닫혔음을 잰다 —
        # 위 테이블 축(`NoCrawlDataError`)과 달리 여기는 sqlite 가 준비 단계에서 내는
        # `OperationalError` 라 `serve` 의 `except Exception` 이 500 으로 옮긴다.
        self._seed_and_index([("http://a.test/", "<title>김치</title><p>김치찌개</p>")])
        db = sqlite3.connect(self.db_path)
        self.addCleanup(db.close)
        db.execute("DROP TABLE pages")
        # `ALTER … DROP COLUMN` 은 sqlite 버전을 타서 새로 만든다.
        db.execute("CREATE TABLE pages (url TEXT PRIMARY KEY, status INTEGER)")
        db.execute("INSERT INTO pages VALUES ('http://a.test/', 200)")
        db.commit()
        for query in ("김치찌개", "zzzznope", "\x01"):
            with self.subTest(query=query):
                with self.assertRaises(sqlite3.OperationalError):
                    indexer.passages(self.db_path, query)

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

    def test_stale_index_wins_over_a_broken_pages_warehouse(self):
        """판정 넷의 우선순위 — **옛 색인이 창고 고장보다 먼저** 이긴다.

        순서를 정하는 것은 `hits = search(...)` 가 두 가드보다 **앞줄**이라는 사실
        하나뿐이다. 그 한 줄을 가드 **뒤**로 내리는 변이는 나머지 전부를 초록으로
        지나가면서(실측: 602건 OK) 옛 색인 + 고장난 창고를 503 이 아니라 500 으로
        바꾼다 — **색인만 다시 돌리면 낫는 DB** 를 «우리가 터졌다» 로 부르게 된다.
        설계 54 3절이 「없는 DB → 옛 색인 → 창고 없음 → 열 없음(500)」을 표로만 쟀고
        코드에는 못이 없던 자리다. 열 축·테이블 축 둘 다 같은 변이로 갈리므로 함께 잰다.
        """
        for label, warehouse in (
                # `html` 열만 없는 창고 · 창고가 통째로 없음. 둘 다 옛 색인에 진다.
                ("html 열 없음", "CREATE TABLE pages (url TEXT PRIMARY KEY, status INTEGER)"),
                ("창고 없음", None)):
            with self.subTest(warehouse=label):
                path = os.path.join(self.dir.name, label + ".db")
                Store(path).upsert("http://a.test/", "<title>김치</title><p>김치찌개</p>", 200)
                db = sqlite3.connect(path)
                self.addCleanup(db.close)
                # 옛 정의로 만든 색인 — `index_pages()` 를 안 부른다(위 테스트와 같은 방법).
                db.execute(TestSchemaDrift.OLD_SCHEMA)
                db.execute("INSERT INTO docs(title, body, url) "
                           "VALUES ('김치', '김치찌개', 'http://a.test/')")
                db.execute("DROP TABLE pages")
                if warehouse:
                    db.execute(warehouse)
                db.commit()
                with self.assertRaises(indexer.StaleIndexError):
                    indexer.passages(path, "김치")

    def test_corrupt_db_is_loud(self):
        self._seed_and_index([("http://a.test/", "<p>김치</p>")])
        with open(self.db_path, "wb") as fh:
            fh.write(b"NOT a sqlite file\n" * 64)
        with self.assertRaises(sqlite3.DatabaseError):
            indexer.passages(self.db_path, "김치")

    def test_unindexed_db_returns_empty(self):
        Store(self.db_path).upsert("http://a.test/", "<p>김치</p>", 200)
        self.assertEqual(indexer.passages(self.db_path, "김치"), [])


class TestPassagesColumnAxisInvariant(unittest.TestCase):
    """자 — 눈금을 우리가 안 적고 **sqlite 에게 묻는다**. 「한 DB 상태 = 한 판정」을
    `pages` 의 **열 축 전체**에서 잰다.

    계획 47(`search()` 안)·53(테이블 축)·54(`html` 열 축)이 같은 원칙을 세 번 닫았고,
    그때마다 자리를 하나씩 손으로 넓혔다. 그래서 **다섯 번째 자리가 생기는 날 그것을
    알아차리는 기계가 저장소에 0개**였다. 이 클래스가 그 기계다 — 눈금이
    `PRAGMA table_info(pages)` 라 열이 늘거나 줄면 케이스도 같이 늘거나 준다.

    재는 것은 세 질의의 **반환값**이 아니라 **판정 이름**이다(예외면 클래스 이름,
    정상 반환이면 `ok`). 질의마다 결과 건수가 다른 것은 검색이 일하는 것이지 고장이
    아니다 — 초안이 반환값을 비교했다가 정상 DB 를 거짓 RED 로 불렀다.

    ponytail: 열 **유무** 축만 잰다 — 타입이 바뀐 열·권한이 막힌 DB·`docs` 가 깨진
    DB 는 다른 경로가 판정한다. 열을 **하나씩만** 뺀다(2^4 조합은 재현 비용만 늘고,
    한 열 축이 닫히면 조합도 같은 줄이 잡는다).
    """

    # 계획 47 이래 같은 셋 — 매치되는 질의 · 매치 없는 질의 · 토큰이 0개인 질의.
    # 세 질의가 `hits` 의 비어 있음에서 갈리므로 갈림을 드러내는 최소 조합이다
    QUERIES = ("김치찌개", "zzzznope", "\x01")
    DOC = ("http://a.test/", "<title>김치</title><p>김치찌개는 배추로 끓인다.</p>")

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def _fresh_db(self, name):
        """제품이 만드는 것과 같은 정상 DB — 색인까지 돌아 있다."""
        path = os.path.join(self.dir.name, name + ".db")
        Store(path).upsert(self.DOC[0], self.DOC[1], 200)
        index_pages(path)
        return path

    def _columns(self, path):
        """(이름, 선언 타입) 목록 — 소스 문자열이 아니라 **실제로 만들어진 표**를 잰다."""
        db = sqlite3.connect(path)
        self.addCleanup(db.close)
        return [(r[1], r[2]) for r in db.execute("PRAGMA table_info(pages)")]

    def _drop_column(self, path, victim, columns):
        # `ALTER … DROP COLUMN` 은 sqlite 버전을 타서 표를 새로 만든다. 열 이름과
        # 선언 타입 둘 다 `PRAGMA` 가 줬으므로 손으로 적는 스키마가 0줄이다
        kept = [(name, decl) for name, decl in columns if name != victim]
        names = ", ".join(name for name, _ in kept)
        db = sqlite3.connect(path)
        self.addCleanup(db.close)
        rows = db.execute("SELECT %s FROM pages" % names).fetchall()
        db.execute("DROP TABLE pages")
        db.execute("CREATE TABLE pages (%s)"
                   % ", ".join("%s %s" % (name, decl) for name, decl in kept))
        db.executemany("INSERT INTO pages(%s) VALUES (%s)"
                       % (names, ", ".join("?" * len(kept))), rows)
        db.commit()

    def _verdict(self, path, query):
        try:
            indexer.passages(path, query)
        except Exception as exc:  # 판정 이름만 본다 — 건수는 검색의 일이다
            return type(exc).__name__
        return "ok"

    def test_every_missing_column_gives_one_verdict_for_every_query_shape(self):
        columns = self._columns(self._fresh_db("눈금"))
        names = [name for name, _ in columns]
        # **자기검사** — 눈금이 0칸이면 루프가 0회 돌고 자는 조용히 초록이 된다.
        # 4는 하한이라 열이 늘어도 안 낡고, `url`·`html` 은 `passages()` 가 실제로
        # 읽는 두 열이다(이 둘이 눈금에서 빠지면 자가 아무것도 안 재게 된다)
        self.assertGreaterEqual(len(columns), 4, names)
        self.assertIn("url", names)
        self.assertIn("html", names)
        for victim in names:
            with self.subTest(missing=victim):
                path = self._fresh_db("없음-" + victim)
                self._drop_column(path, victim, columns)
                verdicts = {q: self._verdict(path, q) for q in self.QUERIES}
                self.assertEqual(
                    len(set(verdicts.values())), 1,
                    "`%s` 열이 없는 같은 DB 가 질의마다 다르게 판정한다: %s"
                    % (victim, verdicts))


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
