"""러너 `e2e/quality_eval.py` 의 종료 코드가 갈리는 지점을 고정한다.

`docs/design_history_006.md` `## 계약` — `0` 두 언어 모두 ≥80% / `1` 미달 /
`2` 코퍼스 결함(가드 G1·G2·G3). **미달과 결함이 섞이면 숫자를 믿을 수 없다.**

fixture 를 통째로 만들지 않고 **동결된 진짜 fixture 를 최소한만 비틀어** 각 갈림길을
때린다 — 손으로 쓴 64문서를 테스트가 다시 흉내 내면 그게 또 하나의 코퍼스가 된다.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "e2e"))

from quality_eval import build_index          # noqa: E402  러너의 색인 경로를 그대로 쓴다
from websearch.indexer import search as idx_search  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER = os.path.join(_ROOT, "e2e", "quality_eval.py")
CORPUS = os.path.join(_ROOT, "e2e", "quality", "corpus.json")
QUERIES = os.path.join(_ROOT, "e2e", "quality", "queries.json")

# 실측 기준선(`tokenizer` 계획, 2026-08-27): ko 20/20 · en 19/20.
# 그전 기준선은 ko 17 · en 18 이었고, 미포함 5건은 전부 토크나이저 실패였다
# (복합어 `보관법`·`일출봉`, 띄어쓰기 `올레길`, 굴절 `tuples`·`loaf`).
# 앞의 넷을 한글 2-gram 열과 `porter` 로 닫았다. 남은 하나는 영어 **불규칙** 복수라
# 사전 없이 못 고친다 (`docs/design_tokenizer.md` `## 범위 밖`).
KO_BASELINE = 20
EN_BASELINE = 19

# 다른 토픽 문서라 어떤 kimchi 질의어도 들어 있지 않다 → 정답으로 걸면 반드시 미포함.
# 코퍼스에는 실재하므로 G1 은 통과한다 — 여기서 재는 것은 **품질 미달**이다.
OFF_TOPIC = "http://q.test/ko/jeju/16"

# `레시피` 는 16건이 매치되고 이 문서가 **15위**다 — 매치는 됐지만 상위 10 밖이다.
# 상위 10 이라는 자름선 자체를 여기서만 잰다 (`OFF_TOPIC` 은 아예 매치되지 않아
# `순위 밖` 으로 빠지므로 11위와 10위를 가르지 못한다).
# (질의어, 정답으로 걸 문서, 매치 수, 순위)
RANKED_OUT = ("레시피", "http://q.test/ko/kimchi/11", 16, 15)

# 오탐 기준선 (평균, 최소, 최대). 매치를 넓히면 여기가 먼저 움직인다.
# `unicode61` 때는 평균 13.8 · 최소 11 · 최대 28 이었다 — 2-gram 을 붙인 뒤와 대조한다.
MATCH_BASELINE = ("14.0", 11, 28)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class QualityEvalCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name

    def run_eval(self, corpus=None, queries=None):
        """러너를 돌려 (종료 코드, stdout+stderr). 인자는 비틀어 쓸 객체."""
        args = [sys.executable, RUNNER]
        for flag, data, default in (
            ("--corpus", corpus, CORPUS),
            ("--queries", queries, QUERIES),
        ):
            path = default
            if isinstance(data, str):   # 경로를 그대로 준다 (없는 파일·깨진 JSON 용)
                path = data
            elif data is not None:
                path = os.path.join(self.tmp, flag[2:] + ".json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            args += [flag, path]
        done = subprocess.run(args, capture_output=True, text=True, timeout=120)
        return done.returncode, done.stdout + done.stderr

    @staticmethod
    def hits(out, name):
        """출력에서 `한국어 17/20 (85%)` 의 17 을 뽑는다."""
        line = [ln for ln in out.splitlines() if ln.startswith(name + " ")][0]
        return int(line.split()[1].split("/")[0])

    def misdirect(self, count):
        """ko 정답 `count` 개를 틀린 문서로 돌린 질의 셋. 첫 하나는 순위 밖 문서로.

        정답을 옮길 뿐 코퍼스도 질의어도 그대로라 매치 수가 변하지 않는다 —
        G2 를 건드리지 않고 **포함률만** 떨어뜨린다.
        """
        queries = _load(QUERIES)
        moved = 0
        for query in queries:
            if moved >= count or query["lang"] != "ko":
                continue
            if query["q"] == RANKED_OUT[0]:
                query["answer"] = RANKED_OUT[1]
            elif query["answer"] != OFF_TOPIC:
                query["answer"] = OFF_TOPIC
            else:
                continue
            moved += 1
        self.assertEqual(moved, count)
        return queries


class TestVerdict(QualityEvalCase):
    def test_frozen_fixture_passes(self):
        """**기준선 이상**을 단언한다 — `== 85%` 로 못박으면 검색이 좋아지는 날 빨개진다.

        회귀는 잡고 개선은 막지 않는 방향 단언이다. 경계(정확히 80%)와 미달은
        `misdirect()` 를 쓰는 아래 두 테스트가 정확한 숫자로 이미 고정한다.
        """
        code, out = self.run_eval()
        self.assertEqual(code, 0, out)
        self.assertGreaterEqual(self.hits(out, "한국어"), KO_BASELINE, out)
        self.assertGreaterEqual(self.hits(out, "영어"), EN_BASELINE, out)

    def test_rank_histogram_says_what_the_percentage_hides(self):
        """포함률 옆에 순위 분포를 찍는다 — 창(상위 10)이 판정을 갈랐는지가 보인다.

        이 fixture 는 매치되면 1위, 아니면 미검출인 이진 상태라 `recall@1` 과
        `recall@10` 이 같다. 백분율만 보면 그 사실이 숨는다 (2026-08-26 리뷰).
        """
        code, out = self.run_eval()
        self.assertEqual(code, 0, out)
        self.assertIn("순위 분포", out)
        self.assertIn("1위 39", out)
        self.assertIn("미검출 1", out)
        # 2~10위가 0건이면 창이 아무 판정도 가르지 않았다는 뜻이다 — 말로 적는다
        self.assertIn("창이 판정을 가른 질의 0건", out)

    def test_match_count_summary_is_reported(self):
        """포함률은 **정답이 들어왔는가**만 센다 — 무엇이 함께 딸려 왔는지는 못 잰다.

        매치를 넓히는 변경(`tokenizer` 계획)은 정의상 오탐을 늘릴 수 있다.
        그것을 재는 숫자가 없으면 "정답 4건 더 찾았다"만 보고 닫게 된다.
        판정은 바꾸지 않는 진단 한 줄이다.
        """
        code, out = self.run_eval()
        self.assertEqual(code, 0, out)
        self.assertIn("매치 수: 평균 %s · 최소 %d · 최대 %d"
                      % (MATCH_BASELINE[0], MATCH_BASELINE[1], MATCH_BASELINE[2]), out)

    def test_unmatched_answer_is_not_called_out_of_rank(self):
        """`순위 밖` 은 "밀렸다" 로 읽힌다. 아예 매치가 안 된 것과 구분해 적는다."""
        code, out = self.run_eval()
        self.assertIn("[en] loaf → http://q.test/en/sourdough/05 (매치 12건, 미검출)", out)
        self.assertNotIn("순위 밖", out)

    def test_exactly_80_percent_passes(self):
        # 경계는 통과 쪽이다 — `concept.md:22` 가 "80% 이상"이다
        code, out = self.run_eval(queries=self.misdirect(KO_BASELINE - 16))
        self.assertEqual(code, 0, out)
        self.assertIn("한국어 16/20 (80%)", out)
        # **매치는 됐지만 상위 10 밖**이면 미포함이다. 순위를 숫자로 알려준다
        self.assertIn("[ko] %s → %s (매치 %d건, 순위 %d)" % RANKED_OUT, out)

    def test_below_80_percent_fails_with_1(self):
        code, out = self.run_eval(queries=self.misdirect(KO_BASELINE - 15))
        self.assertEqual(code, 1, out)
        self.assertIn("한국어 15/20 (75%)", out)
        # 미스는 어느 질의가 왜 틀렸는지까지 나와야 다음 반복이 원인을 본다
        self.assertIn("[ko] 레시피", out)


class TestMeasurementContract(QualityEvalCase):
    """측정이 **조용히 다른 것을 재는** 두 경로를 막는다 (2026-08-26 리뷰)."""

    def test_angle_bracket_in_body_does_not_swallow_text(self):
        """fixture 본문의 `<` 는 태그 시작으로 읽힌다 — 뒤쪽 본문이 통째로 사라진다.

        실측: `조건 a<b 이고 김치찌개레시피 다` 를 감싸면 `<b ...>` 가 열린 것으로
        보고 `>` 가 나올 때까지 삼켜, 뒤 단어가 색인에 아예 안 들어간다.
        코퍼스는 HTML 이 아니라 **텍스트**이므로(`## 계약`) 감싸는 쪽인 러너가
        이스케이프한다. 안 하면 매치 수와 순위가 조용히 달라진다 (2026-08-26 리뷰).
        """
        db = os.path.join(self.tmp, "escape.db")
        build_index(db, [{"url": "http://q.test/ko/kimchi/17", "lang": "ko",
                          "title": "꺾쇠 시험",
                          "body": "조건 a<b 이고 김치찌개레시피 다"}])
        self.assertTrue(idx_search(db, "김치찌개레시피", limit=10))

    def test_first_ten_of_limit_100_equal_a_limit_10_search(self):
        """`measure()` 가 `limit=100` 한 번으로 상위 10 을 대신하는 근거를 못박는다.

        `indexer.search` 의 `ORDER BY bm25(docs), rowid` 가 전순서라서 성립한다.
        그 정렬이 바뀌면 이 측정 전체가 조용히 어긋나므로 여기서 계약으로 잡는다.
        """
        db = os.path.join(self.tmp, "crawl.db")
        build_index(db, _load(CORPUS))
        for term in ("레시피", "제주도", "sourdough"):
            self.assertEqual(idx_search(db, term, limit=10),
                             idx_search(db, term, limit=100)[:10], term)


class TestGuards(QualityEvalCase):
    """가드는 전부 종료 코드 2 다 — 품질 미달(1)과 섞이면 숫자의 의미가 사라진다."""

    def test_g1_answer_not_in_corpus(self):
        queries = _load(QUERIES)
        queries[0]["answer"] = "http://q.test/ko/kimchi/99"
        code, out = self.run_eval(queries=queries)
        self.assertEqual(code, 2, out)
        self.assertIn("G1", out)
        self.assertIn("http://q.test/ko/kimchi/99", out)

    def test_g2_no_match_at_all_is_unmeasurable(self):
        # limit=10 이라 매치가 10건 이하면 정답은 구조적으로 늘 상위 10 안이다
        queries = _load(QUERIES)
        queries[0]["q"] = "코퍼스에없는어휘"
        code, out = self.run_eval(queries=queries)
        self.assertEqual(code, 2, out)
        self.assertIn("G2", out)
        self.assertIn("코퍼스에없는어휘", out)

    def test_g2_fires_at_exactly_10_matches(self):
        """경계는 **가드 쪽**이다 — 10건이면 정답은 이미 구조적으로 상위 10 안이다.

        `레시피` 를 16문서 중 6문서에서 다른 말로 바꿔 매치를 정확히 10건으로 만든다.
        11건이면 통과, 10건이면 측정 불능 — 이 한 건 차이가 이 설계의 핵심이다.
        """
        term, answer, matches, _rank = RANKED_OUT
        corpus = _load(CORPUS)
        stripped = 0
        for doc in corpus:
            if stripped >= matches - 10 or doc["url"] == answer:
                continue
            if term in doc["title"] + doc["body"]:
                doc["title"] = doc["title"].replace(term, "조리법")
                doc["body"] = doc["body"].replace(term, "조리법")
                stripped += 1
        self.assertEqual(stripped, matches - 10)
        code, out = self.run_eval(corpus=corpus)
        self.assertEqual(code, 2, out)
        self.assertIn("G2 매치가 10건뿐이다", out)
        self.assertIn(term, out)

    def test_g3_query_count_not_20_per_language(self):
        code, out = self.run_eval(queries=_load(QUERIES)[:-1])
        self.assertEqual(code, 2, out)
        self.assertIn("G3", out)

    def test_guard_beats_quality_verdict(self):
        # 미달과 결함이 동시에 있으면 **결함이 이긴다** — 못 재는 것을 미달로 보고하지 않는다
        queries = self.misdirect(KO_BASELINE - 15)
        queries[0]["answer"] = "http://q.test/ko/kimchi/99"
        code, out = self.run_eval(queries=queries)
        self.assertEqual(code, 2, out)
        self.assertIn("G1", out)
        self.assertNotIn("한국어 15/20", out)


class TestUnreadableFixture(QualityEvalCase):
    """읽을 수 없는 fixture 는 **사용법 오류(2)** 다 — 품질 미달(1)이 아니다.

    계약(`design_history_006.md` `## 계약`)이 `2` 를 "코퍼스 결함·사용법" 으로
    묶어둔 이유가 여기 있다. 경로를 잘못 치면 트레이스백과 함께 파이썬 기본 종료
    코드 `1` 이 나가는데, 그 `1` 은 **"검색 품질이 80% 에 못 미친다"** 라는 뜻으로
    이미 예약돼 있다. 스크립트를 CI 가 돌리면 오타가 품질 회귀로 보고된다.
    """

    def test_missing_file_is_usage_error_not_shortfall(self):
        code, out = self.run_eval(corpus=os.path.join(self.tmp, "없는파일.json"))
        self.assertEqual(code, 2, out)
        self.assertNotIn("Traceback", out)
        self.assertIn("없는파일.json", out)

    def test_malformed_json_is_usage_error_not_shortfall(self):
        path = os.path.join(self.tmp, "깨진.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write('[{"url": ')
        code, out = self.run_eval(queries=path)
        self.assertEqual(code, 2, out)
        self.assertNotIn("Traceback", out)
        self.assertIn("깨진.json", out)


if __name__ == "__main__":
    unittest.main()
