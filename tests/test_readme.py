"""README 가 안내하는 명령이 실재하는지 본다.

**이 파일이 있는 이유는 README 가 없는 모듈을 안내한 채로 푸시됐기 때문이다** —
`python -m websearch.cli crawl ...` 세 줄이 적혀 있었는데 `websearch.cli` 는 없다
(계획 25 리뷰가 `cli.py` 를 `flags.py` 로 개명했고, README 는 안 따라왔다).
사람이 README 를 읽고 첫 명령을 치면 `No module named websearch.cli` 를 본다.

단위 테스트가 소스만 보면 이런 종류는 영원히 안 잡힌다 — 깨진 것이 코드가 아니라
**코드와 문서 사이**라서 그렇다. 그래서 문서를 입력으로 읽는 검사가 여기 하나 있다.

네트워크도 서브프로세스도 안 쓴다. `find_spec` 은 모듈을 임포트하지 않고 찾기만 한다.
"""

import decimal
import importlib.util
import pathlib
import re
import sys
import unittest

TESTS_DIR = pathlib.Path(__file__).resolve().parent
README = TESTS_DIR.parent / "README.md"
PROJECT_DOC = TESTS_DIR.parent / "docs" / "project.md"

# 합격선이 사는 e2e 모듈을 이름으로 임포트하려고 넣는다.
# `test_design_check.py`·`test_quality_eval.py`·`test_passage_eval.py` 가 이미 쓰는 관용구다.
sys.path.insert(0, str(TESTS_DIR.parent / "e2e"))

# `python3 -m websearch.crawl` 의 모듈 이름만 뽑는다. `-m` 뒤 한 토큰이라
# 뒤에 붙는 인자(`<db>`·`--port N`)는 안 걸린다.
MODULE = re.compile(r"-m\s+(websearch(?:\.\w+)*)")
# 인터프리터 이름. 저장소의 usage 문자열은 전부 `python3` 이다.
INTERPRETER = re.compile(r"^\s*(?:\w+=\S+\s+)*(python3?)\s+-m\s", re.MULTILINE)
# `## 검증` 이 자랑하는 두 숫자. 손으로 적는 값이라 스위트가 자라면 조용히 낡는다.
UNIT_COUNT = re.compile(r"단위\s*(\d+)\s*건")
E2E_COUNT = re.compile(r"e2e\s*시나리오\s*(\d+)\s*종")
# 저장소가 «이걸 치라»고 적어 둔 러너 명령 줄. README 와 project.md 두 곳에 있다.
RUNNER_LINE = re.compile(r"^.*python3? -m unittest discover.*$", re.MULTILINE)
BUFFERED = re.compile(r"\s-b\b")

# 「잘하고 있나 재는 자」 표(일곱 행)에 실린 **아홉 수치**. 첫 행이 둘, 마지막 행이 둘을 담는다.
# 전부 `e2e/*.py` 상수를 손으로 옮겨 적은 값이라, 어느 한쪽만 고치면 조용히 갈라진다.
# (이름, README 에서 수치만 뽑는 정규식, 모듈, 상수, 문서 단위 → 상수 단위 배율).
#
# **문구가 아니라 수치를 잰다.** 표에 `51200` 을 적으면 README 의 「50KB」가 바뀌어도 안 울고,
# README 문구를 통째로 적으면 문구를 다듬는 날 이 표도 같이 고쳐져 거울이 된다. 그래서
# 정규식은 숫자만 잡고 환산(초→ms, KB→B)은 아래 단언이 직접 곱한다.
QUALITY_BAND = (
    ("상위 N건", r"(\d+)개 중에", "quality_eval", "TOP_N", 1),
    ("검색 합격선 %", r"맞는 게 ([\d.]+)% 이상", "quality_eval", "THRESHOLD", 1),
    ("문단 정확도 %", r"문단의 ([\d.]+)% 이상", "passage_eval", "ACCURACY", 1),
    # 「95번은 N초」가 두 행에 있어 행 머리(첫 칸)로 가른다.
    ("검색 예산 초", r"\| 빠른가 \|[^|]*95번은 ([\d.]+)초", "perf_search", "BUDGET_MS", 1000),
    ("문단 예산 초", r"\| 문단도 빠른가 \|[^|]*95번은 ([\d.]+)초",
     "passage_eval", "BUDGET_MS", 1000),
    ("크롤 속도 장/초", r"1초에 ([\d.]+)장 이상", "perf_crawl", "TARGET_RATE", 1),
    ("JS 예산 KB", r"JS ([\d.]+)KB 이하", "design_check", "JS_BUDGET", 1024),
    ("텍스트 대비 배수", r"배경과 ([\d.]+)배 이상", "design_check", "MIN_CONTRAST", 1),
    ("비텍스트 대비 배수", r"은 ([\d.]+)배\)", "design_check", "MIN_CONTRAST_NONTEXT", 1),
)


class ReadmeCommandsTest(unittest.TestCase):
    def setUp(self):
        self.text = README.read_text(encoding="utf-8")

    def test_readme_exists(self):
        # 경로를 잘못 잡으면 아래 테스트들이 빈 목록 위에서 조용히 통과한다.
        self.assertTrue(README.is_file(), "README.md 를 못 찾았다: %s" % README)

    def test_every_module_readme_names_is_importable(self):
        names = sorted(set(MODULE.findall(self.text)))
        # 하나도 못 뽑았으면 정규식이 죽은 것이지 README 가 깨끗한 것이 아니다.
        self.assertTrue(names, "README 에서 `-m websearch.<모듈>` 을 하나도 못 뽑았다")
        missing = [n for n in names if importlib.util.find_spec(n) is None]
        self.assertEqual(
            [], missing,
            "README 가 없는 모듈을 안내한다: %s (있는 것: %s)" % (missing, names))

    def test_readme_uses_python3(self):
        # `python` 은 이 저장소가 도는 환경에 없다 — README 를 그대로 치면
        # `command not found: python` 이다. usage 문자열도 전부 `python3` 이다.
        found = INTERPRETER.findall(self.text)
        self.assertTrue(found, "README 에서 `pythonN -m ...` 줄을 하나도 못 뽑았다")
        self.assertEqual(
            [], [i for i in found if i != "python3"],
            "README 가 `python` 을 쓴다 — `python3` 이어야 한다: %s" % found)
    def test_guided_runner_commands_buffer_output(self):
        # 판정 줄을 파이프로 가린 것이 30회 재발했고, 방아쇠는 언제나 «출력이 길다»
        # 하나였다. `-b` 는 통과한 테스트의 stdout/stderr 를 삼켜 그 이유를 없앤다
        # (초록 실행에서 화면 약 90줄 → 5줄, `OK` 가 마지막 줄이 된다).
        # 안내 문서 **두 곳**이 함께 걸린다 — 한쪽만 고치면 다른 쪽을 읽은 사람이
        # 그대로 90줄을 보고 다시 `| tail` 을 붙인다.
        for path in (README, PROJECT_DOC):
            lines = RUNNER_LINE.findall(path.read_text(encoding="utf-8"))
            self.assertTrue(
                lines, "%s 에서 `-m unittest discover` 줄을 하나도 못 뽑았다" % path.name)
            self.assertEqual(
                [], [l for l in lines if not BUFFERED.search(l)],
                "%s 의 러너 명령에 `-b` 가 없다 — 통과 테스트의 출력이 판정을 밀어낸다: %s"
                % (path.name, lines))

    def test_verification_counts_match_reality(self):
        # README 가 적어 둔 두 숫자를 README 가 안내한 명령으로 직접 센다.
        # 419 라고 적힌 채 428 건이던 것이 이 검사가 생긴 이유다.
        unit = UNIT_COUNT.search(self.text)
        e2e = E2E_COUNT.search(self.text)
        self.assertTrue(unit and e2e, "README `## 검증` 에서 숫자를 못 뽑았다")

        # 새 인스턴스로 센다. `defaultTestLoader` 는 모듈 수준 싱글턴이라 `-m unittest -k`
        # 가 거기에 `testNamePatterns` 를 심어 두고, 그러면 이 검사가 «저장소 전체의 단위
        # 수»가 아니라 «필터를 통과한 수»를 센다(실측: 605 vs 5). 그 값으로 실패 메시지가
        # 「실제는 (5, 21)」이라 말해 README 를 틀리게 고치도록 유도하는 것이 함정이었다.
        actual_unit = unittest.TestLoader().discover(str(TESTS_DIR)).countTestCases()
        actual_e2e = len(list(README.parent.glob("e2e/*.py")))
        self.assertEqual(
            (int(unit.group(1)), int(e2e.group(1))), (actual_unit, actual_e2e),
            "README 의 (단위, e2e) 숫자가 실제와 다르다 — 실제는 (%d, %d)"
            % (actual_unit, actual_e2e))


class QualityBandTest(unittest.TestCase):
    """README 의 합격선 아홉이 `e2e/*.py` 의 실제 상수와 같은지 본다.

    표의 세 번째 칸이 「무엇으로 재나」로 측정기 파일을 가리키는데, **가리키는 파일과
    적힌 수치가 갈라져도 아무도 안 울었다.** 상수 쪽은 넷(TOP_N·THRESHOLD·MIN_CONTRAST·
    MIN_CONTRAST_NONTEXT)만 경계 판정이 물고 있었고, 문서 쪽은 아홉이 다 열려 있었다 —
    README 의 「80% 이상」을 「55% 이상」으로 고쳐도 전수가 초록이었다.

    여기 있는 것이 그 대조다. 어느 한쪽만 고치면 빨개진다.
    """

    def test_readme_bands_match_e2e_constants(self):
        text = README.read_text(encoding="utf-8")
        for label, pattern, module, const, scale in QUALITY_BAND:
            with self.subTest(band=label):
                found = re.findall(pattern, text)
                # 정규식이 죽으면(README 문구가 바뀌면) 대조가 빈손 위에서 조용히 통과한다.
                # 둘 이상 잡혀도 어느 것을 잰 것인지 알 수 없으니 똑같이 실패다.
                self.assertEqual(
                    1, len(found),
                    "README 에서 「%s」 수치를 정확히 하나 못 뽑았다: %r (정규식 %s)"
                    % (label, found, pattern))
                actual = getattr(importlib.import_module(module), const)
                # 부동소수를 피해 Decimal 로 환산한다 — `0.3 * 1000 != 300` 이 되지 않게.
                self.assertEqual(
                    decimal.Decimal(found[0]) * scale, actual,
                    "README 「%s」=%s (×%s) 가 %s.%s=%s 와 다르다"
                    % (label, found[0], scale, module, const, actual))


if __name__ == "__main__":
    unittest.main()
