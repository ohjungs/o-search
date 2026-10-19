"""`e2e/passage_consume.py` — 근거 문단 «소비» 축을 재는 자를 문다.

**이 파일은 실물 DB 를 안 읽는다**(설계 계약 5 · 격리). 보는 것은 순수 함수와 합성
예문뿐이고, 실물 측정은 `e2e/passage_consume.py` 를 맨몸으로 돌려서 한다.

재는 자를 무는 이유는 하나다 — **분자 0 이 「안 이긴다」인지 「못 센다」인지 갈라야
한다.** 2026-10-18 이 두 번 꺼낸 교훈(「재는 자가 죽었는데 초록이다」)과
2026-10-19 가 `nested` 두 방향을 가른 이유가 같은 자리다.
"""

import json
import os
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


if __name__ == "__main__":
    unittest.main()


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
