"""임포트를 훑어 **표준 라이브러리 밖**을 신고한다 — 컨셉 «의존성 0» 을 재는 자.

`docs/specs/concept.md` 경량 3·5 가 「신규 의존성은 사유 한 줄 없이 추가하지 않는다 ·
의존성 0 을 유지한다」고 못박아 뒀는데 **그것을 재는 코드가 이 저장소에 0건이었다**
(2026-09-16 계획 103). 오늘 위반은 진짜로 0 이다 — 그래서 이 파일은 고치는 자가 아니라
**굳히는 자**다. 위험은 어제가 아니라 내일이고, 모양은 하나다:

    `import requests` 한 줄이 들어오는 날 **아무것도 빨개지지 않는다.**

**그 한 줄이 왜 안 보이나가 이 파일의 설계를 전부 정한다.** 그 패키지가 깔린 기계에서는
전수가 초록이고, 안 깔린 기계에서는 빨간데 그 빨감은 「내 기계 문제」로 읽힌다. 그래서
판정 규칙 다섯째 줄이 **「`find_spec` 이 `None` 인 것도 위반」**이다 — 못 찾은 것을
건너뛰면 **안 깔린 기계에서 초록**이 되어 원래 증상이 그대로 돌아온다.
**모르면 통과가 아니라 모르면 실패다.**

판정은 이름 하나를 놓고 위에서부터 본다(`docs/design_dep-zero.md`):

1. 상대 임포트(`from . import x`) — 자기 패키지다.
2. 저장소 안에 그 이름의 파일·디렉터리가 있다 — **순수 파일 시스템**이라
   `PYTHONPATH` 가 있든 없든 답이 같다. 전수는 `PYTHONPATH=src` 로 도는데
   그러면 `websearch` 의 `origin` 이 stdlib 밖이라, 이 줄이 없으면 **자기 패키지를
   의존성으로 신고한다.**
3. `sys.builtin_module_names` — `sys`·`time`·`itertools` 는 `origin` 이 경로가 아니라
   `'built-in'` 이다.
4. `sysconfig` 의 stdlib 경로 밑 — 거꾸로 `zlib` 은 빌트인이 **아닌데**
   `lib-dynload/*.so` 로 그 밑이다. **3 과 4 는 서로를 안 덮어 합집합이어야 한다.**
5. 그 밖 전부 위반.

**허용 목록을 안 쓴다.** 손으로 민 목록은 새 stdlib 모듈을 쓰는 날 **옳은 변경을
빨갛게** 만들고, 파이썬 3.10(`sys.stdlib_module_names`)으로 올리는 날 두 벌이 된다 —
`test_e2e_fd.py` 가 「개수를 요구하면 옳게 고친 파일이 빨개진다」로 겪은 실패 모양이다.

**점 있는 이름은 반드시 첫 마디로 자른다.** `find_spec("concurrent.futures")` 는 부모
패키지를 **진짜로 임포트한다** — 최상위 이름만 넘기면 실행되지 않는다(`turtle` 로 확인:
`origin` 은 나오는데 `sys.modules` 에는 안 들어간다). 남의 코드를 이 그물이 실행하는
일은 없어야 한다.

ponytail: `ast` 가 보는 것만 본다 — `__import__("requests")` 나
`importlib.import_module` 로 감춘 것은 안 쫓는다. 잡는 것은 「어느 날 평범한 임포트 한 줄」
이라는 실제 재발 경로 하나고, 문자열을 쫓기 시작하면 이 자가 린터가 된다. 감춰서
넣는 쪽은 이 자가 아니라 리뷰가 막는다.
"""

import ast
import importlib.util
import os
import pathlib
import sys
import sysconfig
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
# `scripts/` 는 `.py` 가 0개다(`merge-to-main.sh` 뿐) — `rglob` 이라 생기면 저절로 들어온다.
POPULATION = ("src", "tests", "e2e")
STDLIB_DIRS = tuple(
    os.path.realpath(p)
    for p in {sysconfig.get_paths()["stdlib"], sysconfig.get_paths()["platstdlib"]}
)

# 오늘 실측은 54파일 · 임포트 387자리다. 하한을 두는 이유는 **0 을 세면서 통과하지 않기**
# 위해서다 — 경로 오타나 `rglob` 실패로 아무것도 안 훑고 「위반 0」을 외치는 것이
# 이 저장소의 재발 항목이다(계획 101 이 `\bHTTPServer\(` 로 겪었다).
FILE_FLOOR = 50
IMPORT_FLOOR = 300


def first_party_names():
    """저장소가 스스로 제공하는 최상위 이름들.

    모집단 디렉터리 **바로 밑**만 본다. 저장소 루트까지 훑으면 `docs`·`data` 같은
    이름이 허용 목록에 얹혀, 같은 이름의 패키지를 통과시키는 구멍이 된다.
    """
    names = set()
    for pop in POPULATION:
        for entry in (ROOT / pop).iterdir():
            names.add(entry.stem if entry.suffix == ".py" else entry.name)
    return names


LOCAL = first_party_names()


def is_allowed(name):
    """최상위 이름 하나를 판정한다. **모르면 False** — 위 규칙 5번."""
    if name in LOCAL or name in sys.builtin_module_names:
        return True
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ValueError):
        # 못 찾거나 깨진 것은 「표준이 아니다」로 읽는다. 여기서 True 를 주면
        # 안 깔린 패키지가 초록이 되어 이 파일이 존재하는 이유가 사라진다.
        return False
    if spec is None or not spec.origin:
        return False
    return os.path.realpath(spec.origin).startswith(STDLIB_DIRS)


def imported_names(path):
    """`(줄번호, 최상위 이름)` 을 준다.

    `ast.walk` 라 **함수 안·`try` 안의 임포트까지** 본다 — 최상위만 보면 한 칸
    들여쓰는 것으로 빠져나간다. `try: import X except ImportError:` 도 위반이다:
    선택적 의존성도 의존성이고, 「깔린 기계에서만 다르게 도는 코드」가 컨셉이 막는 것이다.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.lineno, node.module.split(".")[0]


def python_sources():
    """훑을 `.py` 를 이름순으로. 이름순이라 실패 목록이 안 흔들린다."""
    return sorted(p for pop in POPULATION for p in (ROOT / pop).rglob("*.py"))


def scan(paths):
    """`(위반 목록, 판정한 임포트 수)`."""
    offenders = []
    seen = 0
    for path in paths:
        for lineno, name in imported_names(path):
            seen += 1
            if not is_allowed(name):
                offenders.append(f"{path.name}:{lineno} import {name}")
    return offenders, seen


class DependencyZeroTest(unittest.TestCase):
    def test_no_third_party_import(self):
        """`src`·`tests`·`e2e` 어디에도 표준 라이브러리 밖 임포트가 없다."""
        offenders, _ = scan(python_sources())
        self.assertEqual(
            [],
            offenders,
            "컨셉 경량 3·5 는 의존성 0 이다. 추가하려면 계획서에 사유 한 줄이 먼저다: "
            + ", ".join(offenders),
        )

    def test_scan_actually_scanned_something(self):
        """**0 을 세면서 통과하지 않는다** — 훑은 파일 수와 임포트 수에 하한이 있다."""
        paths = python_sources()
        _, seen = scan(paths)
        self.assertGreaterEqual(len(paths), FILE_FLOOR)
        self.assertGreaterEqual(seen, IMPORT_FLOOR)


class JudgeTest(unittest.TestCase):
    """판정 자체가 옳은지 본다. 위반이 0인 트리에서는 이쪽이 유일한 증거다."""

    def test_rejects_third_party(self):
        """깔려 있든 아니든 거부한다 — 이 셋은 이 기계에 없어서 `find_spec` 이 `None` 이다."""
        for name in ("requests", "numpy", "pytest"):
            self.assertFalse(is_allowed(name), name)

    def test_accepts_stdlib_and_first_party(self):
        """`zlib` 은 `.so`, `sys` 는 빌트인, `websearch` 는 저장소 것 — 세 갈래를 다 밟는다."""
        for name in ("json", "zlib", "sys", "urllib", "websearch"):
            self.assertTrue(is_allowed(name), name)

    def test_dotted_name_is_cut_to_first_segment(self):
        """점 있는 이름은 첫 마디만 판정에 넘어간다 — **안 자르면 조용히 초록이다.**

        `find_spec("concurrent.futures")` 는 **유효한 stdlib 스펙을 돌려준다.** 즉 쪼개기를
        빼도 이 트리의 점 있는 96자리는 통과할 수 있고, 대신 `find_spec` 이 부모 패키지를
        **진짜로 임포트한다**(실측: `html.parser` 를 물으면 `html` 과 `html.entities` 가
        `sys.modules` 에 들어온다). 남의 코드를 이 그물이 실행하게 되는 길이라, 통과
        여부가 아니라 **넘어가는 이름 자체**를 못박는다.

        `from . import flags` 는 자기 패키지라 아예 안 나온다(`src/websearch/serve.py:24`).
        """
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp) / "dotted.py"
            fixture.write_text(
                "import concurrent.futures\n"
                "from html.parser import HTMLParser\n"
                "from . import flags\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [(1, "concurrent"), (2, "html")], list(imported_names(fixture))
            )
        # 실물에서도 본다 — 점이 하나라도 새어 나가면 부모를 임포트한 것이다.
        leaked = [
            f"{p.name}:{lineno} {name}"
            for p in python_sources()
            for lineno, name in imported_names(p)
            if "." in name
        ]
        self.assertEqual([], leaked)

    def test_catches_import_inside_function(self):
        """한 칸 들여쓴 임포트도 걸린다. 임시 파일이라 `scan` 을 통째로 밟는다."""
        with tempfile.TemporaryDirectory() as tmp:
            planted = pathlib.Path(tmp) / "planted.py"
            planted.write_text("def f():\n    import requests\n", encoding="utf-8")
            offenders, seen = scan([planted])
        self.assertEqual(["planted.py:2 import requests"], offenders)
        self.assertEqual(1, seen)


if __name__ == "__main__":
    unittest.main()
