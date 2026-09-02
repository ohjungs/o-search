"""README 가 안내하는 명령이 실재하는지 본다.

**이 파일이 있는 이유는 README 가 없는 모듈을 안내한 채로 푸시됐기 때문이다** —
`python -m websearch.cli crawl ...` 세 줄이 적혀 있었는데 `websearch.cli` 는 없다
(계획 25 리뷰가 `cli.py` 를 `flags.py` 로 개명했고, README 는 안 따라왔다).
사람이 README 를 읽고 첫 명령을 치면 `No module named websearch.cli` 를 본다.

단위 테스트가 소스만 보면 이런 종류는 영원히 안 잡힌다 — 깨진 것이 코드가 아니라
**코드와 문서 사이**라서 그렇다. 그래서 문서를 입력으로 읽는 검사가 여기 하나 있다.

네트워크도 서브프로세스도 안 쓴다. `find_spec` 은 모듈을 임포트하지 않고 찾기만 한다.
"""

import importlib.util
import pathlib
import re
import unittest

TESTS_DIR = pathlib.Path(__file__).resolve().parent
README = TESTS_DIR.parent / "README.md"
PROJECT_DOC = TESTS_DIR.parent / "docs" / "project.md"

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

        actual_unit = unittest.defaultTestLoader.discover(str(TESTS_DIR)).countTestCases()
        actual_e2e = len(list(README.parent.glob("e2e/*.py")))
        self.assertEqual(
            (int(unit.group(1)), int(e2e.group(1))), (actual_unit, actual_e2e),
            "README 의 (단위, e2e) 숫자가 실제와 다르다 — 실제는 (%d, %d)"
            % (actual_unit, actual_e2e))


if __name__ == "__main__":
    unittest.main()
