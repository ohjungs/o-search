"""`e2e/passage_consume.py` — 근거 문단 «소비» 축을 재는 자를 문다.

**이 파일은 실물 DB 를 안 읽는다**(설계 계약 5 · 격리). 보는 것은 순수 함수와 합성
예문뿐이고, 실물 측정은 `e2e/passage_consume.py` 를 맨몸으로 돌려서 한다.

재는 자를 무는 이유는 하나다 — **분자 0 이 「안 이긴다」인지 「못 센다」인지 갈라야
한다.** 2026-10-18 이 두 번 꺼낸 교훈(「재는 자가 죽었는데 초록이다」)과
2026-10-19 가 `nested` 두 방향을 가른 이유가 같은 자리다.
"""

import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
from websearch.indexer import index_pages  # noqa: E402
from websearch.store import Store  # noqa: E402

sys.path.insert(0, os.path.join(_ROOT, "e2e"))
import passage_consume  # noqa: E402
import passage_shapes  # noqa: E402


_BODY = "<p>" + "kimchi stew is delicious " * 4 + "</p>"
# 브라우저는 바깥 `a` 를 닫아 `li` 를 둘로 보는데 제품은 한 블록으로 둔다 — 후보 `[5]`.
# **실물에서 뽑은 모양이다**(갭 ⑧) — `http://www.gnu.org/bulletins/gnustatus-2011-10.html`
# 의 `<li><a name=toc_Health href=#Health>Health (<a href=…>…</a>)</a>` 가 원본이고,
# 2026-10-20 census 가 집은 3문서 중 둘이 이 꼴이다(나머지는 MDN 프랑스어판 TOC).
_NESTED = '<ul><li><a name=t href=#H>Health (<a href=/x>software</a>)</a></li></ul>'


class ShapePositionsTest(unittest.TestCase):
    def test_a_merged_block_is_reported_with_its_product_position(self):
        """모양 블록의 position 은 **제품** 블록 순번이다 — `passages()` 가 그것을 낸다."""
        self.assertEqual(passage_consume.shape_positions(_NESTED + _BODY), [0])

    def test_the_position_is_the_product_one_even_when_the_shape_is_not_first(self):
        self.assertEqual(passage_consume.shape_positions(_BODY + _NESTED), [1])

    def test_a_document_without_nesting_reports_nothing(self):
        """음성 대조 — 중첩이 없으면 0개다. 이것이 없으면 「전부 모양」도 통과한다."""
        plain = '<ul><li><a href=/x>Health</a></li></ul>' + _BODY
        self.assertEqual(passage_consume.shape_positions(plain), [])

    def test_body_only_reports_nothing(self):
        self.assertEqual(passage_consume.shape_positions(_BODY), [])

    def test_a_desync_is_not_silently_zero(self):
        """정렬이 깨지면 **0 이 아니라 `None`** 이다 — 「못 셌다」와 「없다」를 가른다."""
        self.assertIsNone(passage_consume.shape_positions("", _ref=lambda _h: ["끼워넣은 블록"]))


class QueryTermsTest(unittest.TestCase):
    def test_the_longest_words_come_out_in_length_order(self):
        self.assertEqual(
            passage_consume.query_terms("Gama Fontutils Gawk Health", limit=3),
            ["Fontutils", "Health", "Gama"])

    def test_short_words_are_dropped(self):
        """한두 글자는 질의로 쓸 수 없다 — 2-gram 색인에서 아무 문서나 맞춘다."""
        self.assertEqual(passage_consume.query_terms("a of Coreutils", limit=3),
                         ["Coreutils"])

    def test_ties_keep_the_order_they_appeared_in(self):
        """같은 길이면 등장 순서다 — 재추출 없이 같은 질의가 나와야 수가 이어진다."""
        self.assertEqual(passage_consume.query_terms("Gawk Gama", limit=2),
                         ["Gawk", "Gama"])

    def test_an_empty_block_gives_no_query(self):
        self.assertEqual(passage_consume.query_terms("  ", limit=3), [])


class ExitCodeTest(unittest.TestCase):
    def test_the_three_codes_are_the_repo_idiom(self):
        """`0` 쟀다 · `1` 분자가 0 이 아니다 · **`2` 재지 못했다** (설계 계약 4)."""
        self.assertEqual(
            (passage_consume.MEASURED, passage_consume.SHAPE_WINS,
             passage_consume.UNMEASURABLE), (0, 1, 2))



class _Seeded(unittest.TestCase):
    """합성 예문으로 **색인된** 임시 DB 를 세운다 — 실물 DB 는 안 본다(설계 계약 5)."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = os.path.join(self.dir.name, "crawl.db")
        self.fixture = os.path.join(self.dir.name, "consume.jsonl")

    def _seed(self, url, html):
        store = Store(self.db_path)
        store.upsert(url, html, 200)
        index_pages(self.db_path)
        clipped = passage_consume._clipped(html)
        pos = passage_consume.shape_positions(clipped)
        self.assertTrue(pos, "예문에 모양 블록이 없다 — 음성 대조의 대조군이 사라진다")
        with open(self.fixture, "w", encoding="utf-8") as f:
            f.write(json.dumps({"url": url, "sha": passage_shapes._sha(html),
                                "positions": pos}) + "\n")
        return pos

    def _counts(self):
        return passage_consume.consume_counts(self.db_path, self.fixture)


# 모양 블록은 둘 다 같다 — 다른 것은 **본문**이고, 그래서 이 둘이 한 쌍이다.
# `_NESTED` 와 같은 실물 출처다(위 주석).
_SHAPE = '<ul><li><a name=t href=#H>Health (<a href=/x>software</a>)</a></li></ul>'
_WEAK_BODY = "<p>" + "kimchi stew is delicious " * 6 + "</p>"
_STRONG_BODY = "<p>" + "Health software everywhere " * 6 + "</p>"
# 모양 블록이 **둘**인 문서 — 앞엣것의 글자로 질의하면 뒤엣것이 이긴다(백지 패스 [D])
_TWO_SHAPES = (
    '<ul><li><a name=a href=#A>Health (<a href=/x>software</a>)</a></li>'
    '<li><a name=b href=#B>Health software extended '
    '(<a href=/y>software health</a>)</a></li></ul>')


class NegativeControlTest(_Seeded):
    """**분자 0 이 「안 이긴다」인지 「못 센다」인지 가른다.**

    이 쌍이 없으면 「언제나 0 을 내는 자」도 초록이다 — 2026-10-19 가 `nested` 두 방향을
    가른 이유, 2026-10-18 이 「재는 자가 죽었는데 초록이다」를 두 번 꺼낸 이유와 같다.
    """

    def test_the_shape_block_wins_and_is_counted(self):
        """본문이 질의어를 안 담으면 모양 블록이 근거로 나간다 — **분자 1**."""
        self._seed("http://x/shape", _SHAPE + _WEAK_BODY)
        c = self._counts()
        self.assertEqual((c["denom"], c["numer"]), (1, 1), c)

    def test_a_dominant_body_beats_the_shape_block_and_is_not_counted(self):
        """같은 모양인데 본문이 질의어를 더 담으면 **분모 1 · 분자 0** 이다."""
        self._seed("http://x/body", _SHAPE + _STRONG_BODY)
        c = self._counts()
        self.assertEqual((c["denom"], c["numer"]), (1, 0), c)

    def test_a_drifted_fingerprint_is_not_counted_as_zero(self):
        """지문이 어긋나면 분모에도 안 들어간다 — 드리프트가 「안 이긴다」로 안 샌다."""
        self._seed("http://x/shape", _SHAPE + _WEAK_BODY)
        with open(self.fixture, encoding="utf-8") as f:
            row = json.loads(f.read())
        row["sha"] = "0" * len(row["sha"])
        with open(self.fixture, "w", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        c = self._counts()
        self.assertEqual((c["drifted"], c["denom"], c["numer"]), (1, 0, 0), c)


class VerdictTest(_Seeded):
    def test_a_winning_shape_block_makes_the_runner_say_the_candidate_opens(self):
        self._seed("http://x/shape", _SHAPE + _WEAK_BODY)
        self.assertEqual(passage_consume.measure(self.db_path, self.fixture),
                         passage_consume.SHAPE_WINS)

    def test_a_dominant_body_measures_and_closes(self):
        self._seed("http://x/body", _SHAPE + _STRONG_BODY)
        self.assertEqual(passage_consume.measure(self.db_path, self.fixture),
                         passage_consume.MEASURED)

    def test_an_empty_denominator_is_unmeasurable_not_a_pass(self):
        """분모 0 은 **2** 다 — 「안 이긴다」로 읽으면 못 잰 것을 닫은 것이 된다."""
        self._seed("http://x/shape", _SHAPE + _WEAK_BODY)
        self.assertEqual(
            passage_consume.measure(self.db_path, self.fixture, hits=0),
            passage_consume.UNMEASURABLE)


class FtsSafetyTest(unittest.TestCase):
    """질의어가 **FTS5 문법 문자를 안 흘린다** — 흘리면 측정이 터져 수를 아예 못 낸다.

    신뢰 경계다. 블록 글자는 남의 HTML 에서 그대로 온 것이고, 그것이 `search()` 의
    MATCH 식으로 들어간다. 사다리로 타협하지 않는 자리다(`CLAUDE.md` ponytail 단서).
    """

    def test_fts_operators_never_reach_the_query(self):
        poisoned = '"NEAR" AND OR NOT * : ^ ( ) - 김치찌개 recipe'
        for term in passage_consume.query_terms(poisoned, limit=10):
            self.assertRegex(term, r"^[^\W_]+$", term)

    def test_a_block_of_only_punctuation_gives_no_query(self):
        self.assertEqual(passage_consume.query_terms('*"():^-- '), [])

    def test_hangul_blocks_still_give_terms(self):
        """`[^\\W_]` 는 한글을 받는다 — 안 받으면 한국어 문서가 조용히 분모에서 빠진다."""
        self.assertEqual(passage_consume.query_terms("김치찌개 레시피", limit=2),
                         ["김치찌개", "레시피"])


class CensusTest(_Seeded):
    """`census()` — 새 public 함수고 테스트가 0 이었다(갭 ⑥)."""

    def test_it_freezes_the_shape_document_with_its_positions(self):
        Store(self.db_path).upsert("http://x/shape", _SHAPE + _WEAK_BODY, 200)
        out = os.path.join(self.dir.name, "out.jsonl")
        self.assertEqual(passage_consume.census(self.db_path, out, limit=10, offset=0),
                         passage_consume.MEASURED)
        with open(out, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f if l.strip()]
        self.assertEqual([r["url"] for r in rows], ["http://x/shape"])
        self.assertEqual(rows[0]["positions"], [0])

    def test_a_document_without_the_shape_is_not_frozen(self):
        """음성 대조 — 모양이 없으면 모집단에 안 든다."""
        Store(self.db_path).upsert("http://x/plain", _WEAK_BODY, 200)
        out = os.path.join(self.dir.name, "out.jsonl")
        self.assertEqual(passage_consume.census(self.db_path, out, limit=10, offset=0),
                         passage_consume.MEASURED)
        with open(out, encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), "")

    def test_a_missing_db_is_unmeasurable(self):
        self.assertEqual(
            passage_consume.census(os.path.join(self.dir.name, "없다.db"),
                                   os.path.join(self.dir.name, "out.jsonl")),
            passage_consume.UNMEASURABLE)


class FixtureDriftTest(_Seeded):
    """**픽스처가 적어 둔 position 을 아무도 안 보면, 제품 파서가 바뀐 것을
    「모양 문서가 상위에 못 들었다」로 읽는다.**

    지문(`sha`)은 HTML 이 같은 것만 보증한다 — 같은 HTML 에서 제품이 다른 블록 경계를
    내면 지문은 그대로고 position 만 움직인다. 그 자리를 `moved` 가 센다. 이것이
    이 저장소 최다 재발 계열(「절차를 적고 재는 자를 안 만든다」)의 이 파일 판이다.
    """

    def test_a_moved_position_is_counted_not_swallowed(self):
        self._seed("http://x/shape", _SHAPE + _WEAK_BODY)
        with open(self.fixture, encoding="utf-8") as f:
            row = json.loads(f.read())
        row["positions"] = [99]          # 제품 파서가 바뀐 꼴을 흉내낸다
        with open(self.fixture, "w", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        c = self._counts()
        self.assertEqual(c["moved"], 1, c)

    def test_a_moved_position_makes_the_runner_unmeasurable(self):
        """`rc` 가 **2** 다 — 0 이나 1 로 내면 바뀐 제품 위에서 수를 계속 잇는다."""
        self._seed("http://x/shape", _SHAPE + _WEAK_BODY)
        with open(self.fixture, encoding="utf-8") as f:
            row = json.loads(f.read())
        row["positions"] = [99]
        with open(self.fixture, "w", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        self.assertEqual(passage_consume.measure(self.db_path, self.fixture),
                         passage_consume.UNMEASURABLE)

    def test_matching_positions_do_not_trip_it(self):
        """음성 대조 — 맞으면 0 이다. 이것이 없으면 「언제나 문다」도 통과한다."""
        self._seed("http://x/shape", _SHAPE + _WEAK_BODY)
        self.assertEqual(self._counts()["moved"], 0)


class DesyncVerdictTest(_Seeded):
    """정렬 깨짐은 **`rc=2`** 다 — 실물 census 에서 실제로 3건 났던 축이다."""

    def test_a_desynced_document_is_unmeasurable(self):
        # 모양이 **없는** 문서를 모양 문서라고 적어 두면 position 이 안 맞는다 —
        # `moved` 가 먼저 물므로, 정렬 깨짐 자체는 `shape_positions` 가 `None` 을
        # 내는 길로 잰다(단위 `ShapePositionsTest` 가 그 함수를 직접 문다).
        self._seed("http://x/shape", _SHAPE + _WEAK_BODY)
        real = passage_consume.shape_positions
        passage_consume.shape_positions = lambda _h, _ref=None: None
        self.addCleanup(setattr, passage_consume, "shape_positions", real)
        c = self._counts()
        self.assertEqual((c["desync"], c["docs"]), (1, 0), c)
        self.assertEqual(passage_consume.measure(self.db_path, self.fixture),
                         passage_consume.UNMEASURABLE)


# ── 아래는 백지 패스(별도 세션)가 낸 지적을 못으로 박은 것들 ──────────────
# 받은 여섯 건 중 코드에서 실증된 것만 남겼다. A(이 파일의 `__main__` 블록이
# 중간에 있어 직접 실행하면 16건이 조용히 빠진다)는 테스트가 아니라 배치 문제라
# 블록을 파일 끝으로 옮겨 닫았고, 아래 자가 **그 배치를 다시 못으로 박는다.**


class ThisFileRunsWholeTest(unittest.TestCase):
    """**직접 실행 경로에서도 전부 돈다** — 백지 패스 [A] 가 실증한 자리다.

`__main__` 가드(`unittest.main()` 을 부르는 그 두 줄)가 파일 **중간**에 있으면
    `python3 tests/test_passage_consume.py` 가 거기서 `sys.exit` 해 뒤쪽 클래스가
    **정의조차 안 된다**(실측: 26건 중 10건만 돌았고 빠진 16건이 전부 음성 대조였다).
    머지 게이트는 `unittest discover` 라 안전했으므로 **초록인 채로** 그랬다 —
    이 파일이 설교하는 「재는 자가 죽었는데 초록이다」의 재연이다.
    """

    def test_the_main_guard_is_the_last_statement(self):
        # 바늘을 **런타임에 조립한다** — 한 리터럴로 적으면 이 줄 자신이 세어져
        # 자가 자기 문자열을 센다(첫 판이 그래서 거짓 빨강을 냈다). 같은 처방이
        # `docs/design_history_083.md` 계약에 적혀 있다
        needle = 'if __name__ == "__' + 'main__":'
        src = io.open(__file__, encoding="utf-8").read()
        self.assertEqual(src.count(needle), 1, "가드가 하나가 아니다")
        tail = src[src.index(needle):].strip().splitlines()
        self.assertEqual([l.strip() for l in tail], [needle, "unittest.main()"])


class CrashIsNotAVerdictTest(_Seeded):
    """**백지 패스 [B]** — `rc=1` 이 「후보가 열린다」인데 크래시도 1 로 나갔다.

    제품이 「못 쟀다」를 알리려고 전용 예외까지 둔 조건(`StaleIndexError`)이 하필
    「쟀고 후보가 열린다」 코드로 떨어졌다. 트레이스백은 stderr 라 `rc` 만 보는
    눈에는 **수로 보인다.**
    """

    def test_a_db_without_a_pages_table_is_unmeasurable(self):
        junk = os.path.join(self.dir.name, "junk.db")
        sqlite3.connect(junk).execute("CREATE TABLE junk(x)")
        with io.open(self.fixture, "w", encoding="utf-8") as f:
            f.write('{"url":"http://x/","sha":"%s","positions":[0]}\n' % ("0" * 16))
        self.assertEqual(passage_consume.measure(junk, self.fixture),
                         passage_consume.UNMEASURABLE)

    def test_census_into_a_bare_filename_does_not_crash(self):
        """`os.makedirs("")` 가 터져 `rc=1` 이던 자리 — 디렉터리 없는 이름이다."""
        Store(self.db_path).upsert("http://x/plain", _WEAK_BODY, 200)
        cwd = os.getcwd()
        os.chdir(self.dir.name)
        self.addCleanup(os.chdir, cwd)
        self.assertEqual(
            passage_consume.census(self.db_path, "out.jsonl", limit=10, offset=0),
            passage_consume.MEASURED)


class LooseCountTest(_Seeded):
    """**백지 패스 [D]** — 라벨은 「모양 블록이 이기나」인데 센 것은 「**이** 모양
    블록이 이기나」였다.

    같은 문서의 **다른** 모양 블록이 근거로 뽑힌 쌍을 0 으로 센다 — 즉 새는 방향이
    **「닫는다」 쪽**이라 「이 수는 상한이다」라는 주장이 약해진다. 둘을 함께 찍는다.
    """

    def test_another_shape_block_winning_is_counted_as_loose_not_strict(self):
        pos = self._seed("http://x/two", _TWO_SHAPES + _WEAK_BODY)
        self.assertEqual(len(pos), 2, pos)
        c = self._counts()
        self.assertGreater(c["any"], c["numer"], c)
        self.assertEqual(c["any"], c["denom"], c)

    def test_loose_equals_strict_when_there_is_one_shape_block(self):
        """음성 대조 — 모양 블록이 하나면 둘이 같다. 아니면 `any` 가 늘 분모다."""
        self._seed("http://x/shape", _SHAPE + _WEAK_BODY)
        c = self._counts()
        self.assertEqual((c["numer"], c["any"]), (1, 1), c)


class ArgGuardTest(_Seeded):
    """**백지 패스 [E]·[F]** — sqlite 의 `LIMIT -1` 은 **무제한**이다."""

    def test_a_negative_hits_is_refused(self):
        self._seed("http://x/shape", _SHAPE + _WEAK_BODY)
        self.assertEqual(
            passage_consume.main(["--db", self.db_path, "--fixture", self.fixture,
                                  "--hits", "-1"]),
            passage_consume.UNMEASURABLE)

    def test_a_census_window_other_than_the_frozen_one_refuses_the_default_path(self):
        """창을 바꿔 돌리면 **동결 픽스처를 덮지 않는다** — 수가 안 이어진다.

        DB 를 **실제로 만든다** — 첫 판은 안 만들어서 「DB 가 없다」로 `rc=2` 가
        나왔고, 그러면 창 가드를 안 밟고도 통과한다(거짓 초록).
        """
        Store(self.db_path).upsert("http://x/plain", _WEAK_BODY, 200)
        self.assertEqual(
            passage_consume.main(["--census", "--db", self.db_path,
                                  "--limit", "10", "--offset", "0"]),
            passage_consume.UNMEASURABLE)


if __name__ == "__main__":
    unittest.main()
