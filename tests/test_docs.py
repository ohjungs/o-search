"""루프가 매번 읽는 기록 문서의 머리가 제자리에 있는지 본다.

**이 파일이 있는 이유는 `docs/digest.md` 의 H1 이 리스트 항목 안으로 빨려 들어간 채
4일·25커밋을 갔기 때문이다** — `b11fd40` 의 append 편집이 머리 두 줄을
`  - [원문] # 아카이브 요약` 아래로 끌고 들어갔고, 파일 첫 줄이
`- ~~[5]~~ **닫혔다 …` 가 됐다. 계획 탐색(discover)은 이 파일을 통째로 읽어 다음
할 일을 고른다. 머리가 깨지면 닫힌 항목이 열린 것처럼 보이고, 실제로 계획 38 의
탐색이 그렇게 오염됐다(닫힌 `[5]` 를 열린 항목으로 셌다).

깨진 것이 코드가 아니라 **기록 문서 자신의 구조**라 소스만 보는 단위 테스트로는
영원히 안 잡힌다. 세 파일 모두 append 대상이라 같은 사고가 그대로 재발한다 —
그래서 `digest.md` 만이 아니라 셋을 함께 본다.
`status.md` 는 프런트매터(`---`)로 시작하므로 대상이 아니다.

제목 문구는 안 본다 — 이름을 바꾸는 것은 정당한 편집이고, 사고가 깨뜨린 것은
문구가 아니라 **머리가 1번 줄에 있다는 구조**다.

두 번째 검사(`DocCitationTest`)는 같은 셋을 **가리키는 쪽**에서 본다 — 머리가
멀쩡해도 줄번호 인용은 append 한 번에 남의 항목을 가리킨다. 이 파일은 그래서
`docs/` 의 구조와 상호참조를 함께 보는 자리다.
"""

import pathlib
import re
import unittest

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"
# append 편집이 머리를 삼킬 수 있는 기록 문서 — 셋 다 H1 로 시작한다.
APPEND_TARGETS = ("digest.md", "index.md", "history_current.md")
# 그 셋을 줄번호로 가리킨 인용 — append 한 번에 다른 항목을 가리키게 된다.
# 두 표기를 함께 본다: `digest.md:156` 과 `` `digest.md` 156행 ``. 콜론 꼴만 막으면
# 한국어 꼴이 그대로 탈출구가 된다(반복 210 이 실제로 그리로 옮겨 적었다).
# 자리표시자(`digest.md:<줄번호>`)는 숫자가 아니라 꺾쇠라 걸리지 않는다.
# `행` 앞의 공백은 일부러 허용하지 않는다 — "`index.md` 41 행" 은 줄이 아니라
# 계획 41 의 행을 뜻하는 다른 표현이다.
# 이름과 숫자의 **인접**을 요구하면 마크다운 표 칸 구분자 하나로 빠져나간다
# (`` | `docs/digest.md` | 80행 ... | ``) — 닫는 백틱 뒤 분리자를 3자까지 받는다.
# 위·아래 두 리터럴 표는 `CitationPatternTest` 가 코드 안에 고정해 둔 것이다.
CITATION = re.compile(
    r"(?:%s)(?::[0-9]|`?[^0-9]{0,3}[0-9]+행)"
    % "|".join(re.escape(n) for n in APPEND_TARGETS))
# 회전이 닫아 둔 아카이브는 수정·삭제 금지 문서라 검사 대상이 아니다.
ARCHIVE = re.compile(r"^(?:history|plan_history|design_history)_[0-9]+\.md$")


class DocHeadTest(unittest.TestCase):
    def test_append_targets_start_with_h1(self):
        for name in APPEND_TARGETS:
            with self.subTest(doc=name):
                path = DOCS / name
                # 경로를 잘못 잡으면 아래 단언이 빈 문자열 위에서 조용히 통과한다.
                self.assertTrue(path.is_file(), "기록 문서를 못 찾았다: %s" % path)
                first = path.read_text(encoding="utf-8").split("\n", 1)[0]
                self.assertRegex(
                    first, r"^# \S",
                    "%s 의 첫 줄이 H1 이 아니다 — 머리가 본문에 빨려 들어갔다: %r"
                    % (name, first))


class CitationPatternTest(unittest.TestCase):
    """`CITATION` 자신을 리터럴로 붙든다 — 아래 검사는 자기를 못 잰다.

    문서를 다 고쳐 놓으면 `DocCitationTest` 의 hits 는 정규식이 넓든 좁든 0 이라
    **좁아지는 변이가 전부 초록으로 산다**(2026-09-01 계획 42 리뷰 실측: 축소 변이
    4종 전원 생존). 린트형 검사는 데이터가 초록일 때 자기 자신을 못 잰다 —
    그래서 검사 대상을 문서가 아니라 **코드 안에 고정**한다.
    """

    # 막아야 하는 세 표기 + 대상 셋을 각각 한 줄씩. 이름 하나를 빼는 변이도 여기서 죽는다.
    CAUGHT = (
        "근거 `digest.md:156` 의 `[6]`",                    # 콜론 꼴
        "`index.md` 22행을 이름 인용으로 고쳤다",           # 한국어 `N행` 꼴 (인접)
        "| `docs/digest.md` | 80행의 인용 형태 교정 |",     # 표 칸 구분자로 갈린 꼴
        "`history_current.md` 12행",                        # 셋째 대상
    )
    # 잡으면 안 되는 꼴 — 오탐 0 을 코드가 지킨다(주석만으로는 다음 편집이 지운다).
    NOT_CAUGHT = (
        "`index.md` 41 행",                # 줄 41 이 아니라 계획 41 의 행 — 공백이 가른다
        "`digest.md` 200줄 · 49항목",
        "`index.md` 15~17번",
        "자리표시자 `digest.md:<156>`",
    )

    def test_pattern_catches_line_number_citations(self):
        for line in self.CAUGHT:
            with self.subTest(line=line):
                self.assertRegex(line, CITATION, "금지 표기를 못 잡는다 — 검사가 좁아졌다")

    def test_pattern_leaves_line_number_lookalikes(self):
        for line in self.NOT_CAUGHT:
            with self.subTest(line=line):
                self.assertNotRegex(line, CITATION, "줄번호가 아닌 것을 잡는다 — 오탐")


class DocCitationTest(unittest.TestCase):
    def test_live_docs_cite_append_targets_by_name(self):
        hits = []
        scanned = []
        for path in sorted(DOCS.glob("*.md")):
            if ARCHIVE.match(path.name):
                continue
            scanned.append(path.name)
            for no, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
                if CITATION.search(line):
                    hits.append("  %s %d행: %s" % (path.name, no, line.strip()))
        # 경로를 잘못 잡으면 순회가 0회 돌고 아래 단언이 빈 목록 위에서 조용히 통과한다.
        for name in APPEND_TARGETS:
            self.assertIn(name, scanned, "검사가 %s 를 안 훑었다 — 경로가 틀렸다: %s"
                          % (name, DOCS))
        self.assertEqual(
            [], hits,
            "append 전용 문서를 줄번호로 가리킨 인용 — 줄이 아니라 항목 이름으로 "
            "가리킨다:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
