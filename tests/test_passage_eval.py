"""러너 `e2e/passage_eval.py` 의 종료 코드가 갈리는 지점을 고정한다.

`docs/design_passage-api.md` `## 갈림길 4` — `0` 통과 / `1` 미달(정확도 <90% 또는
p95 >500ms) / `2` 잴 수 없다(사용법·fixture·가드). **1 과 2 가 섞이면 숫자를 믿을 수
없다** — 설정이 틀려 못 잰 것이 «사양 미달» 로 보이면 사람이 엉뚱한 것을 고치러 간다.
이 파일이 재는 것은 정확도가 아니라 **그 갈림**이다.

`test_quality_eval.py` 와 같은 방식이다 — 동결 fixture 를 **최소한만 비틀어** 각
갈림길을 때린다. 여기서 코퍼스를 새로 지으면 그게 또 하나의 코퍼스가 된다.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E2E = os.path.join(_ROOT, "e2e")
RUNNER = os.path.join(E2E, "passage_eval.py")
CORPUS = os.path.join(E2E, "quality", "corpus.json")
QUERIES = os.path.join(E2E, "quality", "queries.json")

# 종료 코드 — 러너 모듈 docstring 의 계약. 숫자를 여기 한 벌만 적는다
PASS, SHORTFALL, UNMEASURABLE = 0, 1, 2


class PassageEvalCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name

    def run_eval(self, corpus=None, queries=None, repeat="1", prelude=""):
        """러너를 **진짜 프로세스로** 돌려 (종료 코드, stdout+stderr).

        종료 코드가 계약이라 in-process 호출로는 잴 수 없다 — `main()` 밖으로 새는
        예외는 반환값이 아니라 파이썬 기본 코드 1 로 나가고, 그게 바로 이 파일이
        지키는 구멍이다. `prelude` 는 그 프로세스 안에서 상수를 비틀 때 쓴다.
        """
        args = [flag for pair in (
            ("--corpus", corpus or CORPUS), ("--queries", queries or QUERIES),
            ("--repeat", repeat)) for flag in pair]
        done = subprocess.run(
            [sys.executable, "-B", "-c",
             "import sys; sys.path.insert(0, %r)\n"
             "import passage_eval\n%s"
             "sys.exit(passage_eval.main(sys.argv[1:]))" % (E2E, prelude),
             *args],
            capture_output=True, text=True, timeout=300)
        return done.returncode, done.stdout + done.stderr

    def write(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return path

    @staticmethod
    def load(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)


class TestVerdict(PassageEvalCase):
    """대조군 — 이게 없으면 아래 가드들은 «항상 2를 낸다» 로도 초록이 된다."""

    def test_frozen_fixture_passes_and_prints_both_numbers(self):
        # `--repeat 1` 은 경계값이기도 하다(가드는 1 미만만 막는다) — 대조군과 겹치므로
        # 한 번만 돈다. 숫자를 못박지 않는다: 검색이 좋아지는 날 빨개지면 안 된다
        rc, out = self.run_eval()
        self.assertEqual(rc, PASS, out)
        self.assertIn("정확도", out)
        self.assertIn("p95", out)
        self.assertIn("통과", out)


class TestUsageErrorsAreNotShortfall(PassageEvalCase):
    """사용법·fixture 오류는 **2** 다 — 1 은 «사양 미달» 에 예약돼 있다.

    `--repeat 0` 은 실제로 `UnboundLocalError` 를 내며 rc 1 로 죽던 자리다
    (계획 48 개발 3/3 실측). 고친 것에는 테스트가 붙는다(`rules/test.md` 2절).
    """

    def test_repeat_zero_is_unmeasurable_not_shortfall(self):
        rc, out = self.run_eval(repeat="0")
        self.assertEqual(rc, UNMEASURABLE, out)
        self.assertNotIn("Traceback", out, "사용법 오류가 트레이스백으로 샜다")

    def test_negative_repeat_is_the_same_door(self):
        # 0 만 막고 음수를 흘리면 `range(-1)` 이 표본 0개짜리 초록을 낸다
        rc, out = self.run_eval(repeat="-1")
        self.assertEqual(rc, UNMEASURABLE, out)

    def test_missing_corpus_path_is_unmeasurable(self):
        rc, out = self.run_eval(corpus=os.path.join(self.tmp, "없는.json"))
        self.assertEqual(rc, UNMEASURABLE, out)
        self.assertNotIn("Traceback", out)

    def test_malformed_queries_json_is_unmeasurable(self):
        path = os.path.join(self.tmp, "깨진.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("{이건 JSON 이 아니다")
        rc, out = self.run_eval(queries=path)
        self.assertEqual(rc, UNMEASURABLE, out)
        self.assertNotIn("Traceback", out)

    def test_corpus_flag_is_actually_read(self):
        """손잡이가 먹는지부터 잰다 — 기본값만 도는 러너면 위 두 테스트가 거짓 초록이다.

        정답으로 걸린 문서를 코퍼스에서 빼면 `fixture_defects` 의 G1 이 그 URL 을
        이름으로 짚는다. 기본 코퍼스를 읽고 있으면 G1 이 안 나온다.
        """
        dropped = self.load(QUERIES)[0]["answer"]
        corpus = [doc for doc in self.load(CORPUS) if doc["url"] != dropped]
        rc, out = self.run_eval(corpus=self.write("corpus.json", corpus))
        self.assertEqual(rc, UNMEASURABLE, out)
        self.assertIn(dropped, out)


class TestConstantDrift(PassageEvalCase):
    """`PAGE_SIZE` ≠ `PASSAGE_LIMIT` 는 **2** 다 — 채택률의 분모가 분자와 다른 집합이 된다.

    `assert` 로 두면 파이썬 기본 종료 코드 **1** 로 죽는다. 그건 «사양 미달» 이라
    이 도구가 재는 두 숫자 중 하나가 떨어졌다는 뜻이 되고, 사람은 설정이 아니라
    검색 품질을 고치러 간다. W 변이가 G7 에서 드러낸 것과 **같은 구멍**이 이 형제
    자리에 남아 있었다 (계획 48 테스트에서 실측하고 닫았다).
    """

    def test_drift_is_unmeasurable_not_shortfall(self):
        rc, out = self.run_eval(
            prelude="passage_eval.serve.PASSAGE_LIMIT = 7\n")
        self.assertEqual(rc, UNMEASURABLE, out)
        self.assertNotIn("Traceback", out, "설정 오류가 트레이스백으로 샜다")
        self.assertIn("PAGE_SIZE", out, "무엇이 갈렸는지 안 적혀 있다")


class TestServerErrorIsNotShortfall(PassageEvalCase):
    """서버가 비2xx 를 내면 **2** 다 — `measure()` 의 `urlopen` 이 던지는 자리다.

    `--repeat`·G7·상수 드리프트가 이미 같은 이유로 2 를 내는데 **HTTP 경로만
    빠져 있었다**(계획 48 리뷰 실측: rc 1 + 트레이스백). 이쪽이 더 나쁘다 —
    사용법 오류는 사람이 곧 알아채지만 서버가 500 을 내서 나온 rc 1 은
    *"문단 품질이 떨어졌다"* 로 읽혀 엉뚱한 것을 고치러 간다.
    """

    def test_server_500_is_unmeasurable_not_shortfall(self):
        rc, out = self.run_eval(prelude=(
            "def _boom(*a, **k):\n"
            "    raise RuntimeError('문단 경로가 터졌다')\n"
            "passage_eval.indexer.passages = _boom\n"))
        self.assertEqual(rc, UNMEASURABLE, out)
        self.assertNotIn("Traceback", out, "HTTP 오류가 트레이스백으로 샜다")


class TestGuards(PassageEvalCase):
    """가드가 이 도구의 이빨이다 — 거짓 초록을 잡는 것은 정확도가 아니라 종료 2 다."""

    def test_g4_and_g6_fire_when_a_document_is_one_block(self):
        """문단이 하나뿐이면 **고른 것이 아니라 문서를 그대로 낸 것**이다.

        본문의 `. ` 를 지우면 `wrap` 이 문장을 못 끊어 문서당 블록이 1개가 된다.
        매치는 그대로라 정확도는 자동으로 100% 가 나온다 — 숫자가 아니라 가드가
        잡아야 하는 자리이고, 그래서 이 fixture 는 **초록으로 새는 모양**이다.
        """
        corpus = self.load(CORPUS)
        for doc in corpus:
            doc["body"] = doc["body"].replace(". ", " ")
        rc, out = self.run_eval(corpus=self.write("corpus.json", corpus))
        self.assertEqual(rc, UNMEASURABLE, out)
        self.assertIn("G4", out)
        self.assertIn("G6", out, "본문 통째를 문단이라고 낸 것도 같이 잡혀야 한다")

    def test_wrap_invariant_is_an_identity_so_g7_cannot_fire(self):
        """G7 은 **닿을 수 없는 가드**다 — 그 사실을 여기 고정한다.

        `" ".join(wrap(b))` 는 `". ".join(b.split(". "))` 를 그대로 재구성한다.
        대수적 항등식이라 어떤 본문에도 참이고, 그래서 러너 설명이 말하는
        "`wrap` 의 단언이 매 실행 확인한다" 는 **아무것도 확인하지 않는다**.
        지우지 않는 이유는 값이 0이라서다. 이 테스트는 그 판단의 근거를 남긴다 —
        `wrap` 이 언젠가 문장 부호를 더 다루게 되면 여기가 먼저 빨개진다.
        """
        sys.path.insert(0, E2E)
        from passage_eval import wrap  # noqa: E402 — 러너의 것을 그대로 쓴다
        for body in ("A. B", "A.  B", "A. ", ". B", "", ".", "A", "A. B. C",
                     "A.. B", "A.\n B", "A .  . B"):
            with self.subTest(body=body):
                self.assertEqual(" ".join(wrap(body)), body)


if __name__ == "__main__":
    unittest.main()
