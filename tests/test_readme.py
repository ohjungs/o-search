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

README = pathlib.Path(__file__).resolve().parent.parent / "README.md"

# `python3 -m websearch.crawl` 의 모듈 이름만 뽑는다. `-m` 뒤 한 토큰이라
# 뒤에 붙는 인자(`<db>`·`--port N`)는 안 걸린다.
MODULE = re.compile(r"-m\s+(websearch(?:\.\w+)*)")
# 인터프리터 이름. 저장소의 usage 문자열은 전부 `python3` 이다.
INTERPRETER = re.compile(r"^\s*(?:\w+=\S+\s+)*(python3?)\s+-m\s", re.MULTILINE)


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


if __name__ == "__main__":
    unittest.main()
