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
# 브라우저는 바깥 `a` 를 닫아 `li` 를 둘로 보는데 제품은 한 블록으로 둔다 — 후보 `[5]`
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


# 모양 블록은 둘 다 같다 — 다른 것은 **본문**이고, 그래서 이 둘이 한 쌍이다
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
