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
# 반복 번호가 사는 두 자리. `| 반복 수 |`·`| 반복 상한 |`·`| 평균 반복 |` 은 이웃이라
# 정확한 형태만 문다. `night_iterations:` 도 `iteration:` 의 이웃이다.
# 아래 `IterationPatternTest` 가 이 둘을 합성 표로 고정한다.
ITER_ROW = re.compile(r"^\| 반복 \| ([0-9]+) \|", re.M)
ITER_LINE = re.compile(r"^iteration: ([0-9]+)$", re.M)
# 기록 문서의 머리. 첫 줄 하나에만 대므로 `re.M` 은 없다 — `^` 는 문자열 머리다.
# `\S` 가 `#제목`·`# `(제목 없는 H1)를 가른다. 아래 `DocHeadPatternTest` 가 이것을
# 합성 리터럴로 고정한다(실물 문서는 늘 맞는 모양이라 자기를 못 잰다).
DOC_HEAD = re.compile(r"^# \S")
# 스텝 번호가 사는 두 자리. `index.md` 는 행이 수십 개라 **`plan:` 슬러그로 집는다** —
# 상태 칸(`진행`/`완료`)은 안 본다(`docs/design_index-step-sync.md` 「결정」).
# 행 패턴은 슬러그를 `re.escape` 해 끼우므로 상수는 템플릿이다. 이름 뒤 ` | ` 를
# 요구해 **접두 일치를 막는다** — 아니면 `plan_index-step-sync-2` 가 대신 통과한다.
# 아래 `StepPatternTest` 가 이 셋을 합성 표로 고정한다.
STEP_LINE = re.compile(r"^step: ([0-9]+/[0-9]+)$", re.M)
PLAN_SLUG = re.compile(r"^plan: ([A-Za-z0-9_-]+)", re.M)
STEP_ROW = r"^\| plan_%s \| [^|]* \| [^|]* \| ([0-9]+/[0-9]+) \|"
# 후보 절이 계획을 가리키는 포인터. 「… **→ 2026-09-06 계획 68 `slug` 로 열었다**」
# 꼴만 문다. 조사 셋(`로`·`으로`·`를`)은 실물에 다 있고, **슬러그 백틱을 요구하는
# 것이 부정문을 가르는 자리다** — 「계획 49 범위 밖이라 안 열었다」에는 백틱 슬러그가
# 없어서 안 물린다(2026-09-07 실측: 후보 두 절의 `열었다` 11자리 중 9자리가 포인터,
# 나머지 둘이 그 부정문이다). 아래 `StrikeGapTest` 가 갈래를 합성 문자열로 밟는다.
STRIKE_POINTER = re.compile(r"계획 [0-9]+ `([A-Za-z0-9_-]+)` (?:로|으로|를) 열었다")
# 같은 계획 행의 **상태 칸**. `STEP_ROW` 는 넷째 칸을 보고 이쪽은 둘째 칸을 본다.
PLAN_ROW = r"^\| plan_%s \| ([^|]*) \|"
# 후보 두 절의 머리. `## 다음 계획 후보` 와 `## 다음 계획 후보 (테스트 phase 갭 …)`.
CANDIDATE_HEAD = "## 다음 계획 후보"
# 오늘 실물의 포인터 수는 **10**이다(개발 phase 가 `[4]` 줄에 포인터를 채워 9에서
# 하나 늘었다). 추출기가 0을 내면 판정이 조용한 초록이 되므로 하한을 못으로 박는다.
# 후보가 닫히며 포인터는 늘기만 하니 하한은 안전하다. **값 축에 딱 붙이지 않았다** —
# 붙이면 문구가 하나 달라지는 날도 물지만 후보 절을 정리하는 날 거짓 RED 다.
# 그 갈림은 `digest` 후보에 등재해 두었다(계획 70 리뷰).
STRIKE_POINTER_FLOOR = 9

# 같은 계획 행의 **다섯째 칸(e2e)**. `STEP_ROW` 는 넷째, `PLAN_ROW` 는 둘째를 보고
# 이것은 다섯째를 본다. 슬러그로 집지 않고 **행 전부를 훑는다** — 재는 대상이
# 「지금 진행 중인 계획」이 아니라 「이미 닫힌 47행의 부기」라서다.
# 무는 것: (슬러그, 상태 칸, e2e 칸).
VERDICT_ROW = re.compile(
    r"^\| plan_([A-Za-z0-9_-]+) \| ([^|]*) \| [^|]* \| [^|]* \| ([^|]*) \|", re.M)
# 위 정규식이 다섯째 칸까지 못 읽은 행을 세려고 머리만 따로 문다. 열 모양이 바뀌면
# `VERDICT_ROW` 는 그 행을 **조용히 건너뛴다** — 침묵 대신 신고하게 만드는 자리다.
VERDICT_ROW_HEAD = re.compile(r"^\| plan_", re.M)
# e2e 칸이 판정이 아니라 **날짜뿐**인 꼴. 어휘(`통과`)를 요구하지 않는 것이 설계다 —
# 2026-09-07 실측에서 `통과` 를 요구하면 `없음(…)`·`**새 e2e 0개**(…)` 여섯 행이
# 거짓 RED 였다(계획서 2절). 자는 날짜 하나만 거절한다.
VERDICT_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
# 오늘 실물의 계획 행은 **48**이다. 추출기가 0행을 내면 판정이 조용한 초록이 되므로
# 하한을 못으로 박는다(계획 70 이 `STRIKE_POINTER_FLOOR` 에서 밟은 자리). 행은 늘기만
# 하니 하한은 안전하고, **값 축에 딱 붙이지 않았다** — 붙이면 표를 정리하는 날 거짓 RED 다.
VERDICT_ROW_FLOOR = 45


def done_section(digest_text):
    """`digest.md` 의 `## 완료` 절 본문. 절이 없으면 `None` — 호출부가 실패시킨다.

    범위를 절로 자르는 것이 설계의 결정이다. 파일 전체를 보면 `## 반복 실패` 의
    **구멍을 신고하는 문장 자신**이 신고 대상을 초록으로 만든다.
    """
    lines = digest_text.split("\n")
    if "## 완료" not in lines:
        return None
    head = lines.index("## 완료")
    tail = next((i for i, ln in enumerate(lines[head + 1:], head + 1)
                 if ln.startswith("## ")), len(lines))
    return "\n".join(lines[head:tail])


def indexed(name, section):
    """명부가 이 아카이브를 이름으로 싣고 있나.

    접두어에 가려진 것은 안 친다 — `plan_history_019.md` 는 `history_019.md` 가
    아니다. 명부가 가리키는 것은 아카이브 원본뿐이다.
    """
    return re.search(r"(?<![A-Za-z_])" + re.escape(name), section) is not None


def step_row(slug):
    """`index.md` 에서 이 슬러그의 계획 행을 무는 정규식."""
    return re.compile(STEP_ROW % re.escape(slug), re.M)


def iter_gap(status_text, metrics_text):
    """반복 축이 어긋난 자리를 한 줄로 돌려준다. 어긋남이 없으면 `None`.

    **몸통을 함수로 뺀 이유는 `step_gap` 과 같다** — `IterationSyncTest` 는 실물 두
    문서 위에서만 도는데 그 문서는 늘 맞춰져 있어서, 판정을 무력화하는 변이가 조용히
    산다(2026-09-06 계획 61 착수 실측 — 자기비교·가드 둘 삭제·판정 통째 삭제가
    전수 614건에서 4/4 생존했다). 실물은 `IterationSyncTest` 가, 갈래는 `IterGapTest`
    가 부른다.
    """
    a = ITER_ROW.search(metrics_text)
    if a is None:
        return "metrics.md 에서 `| 반복 | <수> |` 행을 못 찾았다"
    b = ITER_LINE.search(status_text)
    if b is None:
        return "status.md 에서 `iteration: <수>` 줄을 못 찾았다"
    if a.group(1) != b.group(1):
        return ("반복 번호가 어긋났다 — metrics.md `반복` %s ≠ status.md `iteration` %s"
                % (a.group(1), b.group(1)))
    return None


def step_gap(status_text, index_text):
    """스텝 축이 어긋난 자리를 한 줄로 돌려준다. 어긋남이 없으면 `None`.

    **몸통을 함수로 뺀 이유**: `StepSyncTest` 는 실물 문서 위에서만 도는데 그 문서는
    늘 맞춰져 있어서, 검사가 문서에만 붙어 있으면 «비교를 무력화하는 변이»가 전부
    조용히 산다(2026-09-06 계획 60 테스트 phase 실측 — 변이 6종이 전수 609건에서
    6/6 생존했다). `done_section`·`indexed` 가 `ArchiveMatchTest` 를 위해 나온 것과
    같은 이유다. 실물은 `StepSyncTest` 가, 갈래는 `StepGapTest` 가 부른다.
    """
    s = STEP_LINE.search(status_text)
    if s is None:
        return "status.md 에서 `step: <N/M>` 줄을 못 찾았다"
    p = PLAN_SLUG.search(status_text)
    if p is None:
        return "status.md 에서 `plan: <슬러그>` 줄을 못 찾았다"
    slug = p.group(1)
    if slug == "null":
        # 하네스 템플릿의 초기 상태. 대조할 행이 없으니 초기값 자신을 요구한다.
        if s.group(1) != "0/0":
            return ("`plan: null` 인데 `step` 이 %s 다 — 계획 없이 스텝만 흘렀다"
                    % s.group(1))
        return None
    r = step_row(slug).search(index_text)
    if r is None:
        return ("index.md 에서 `| plan_%s |` 행의 스텝 칸을 못 읽었다 — 등재가 빠졌거나"
                " 표의 열 모양이 바뀌었다(스텝을 넷째 칸으로 가정한다)" % slug)
    if r.group(1) != s.group(1):
        return ("스텝이 어긋났다 — index.md `plan_%s` %s ≠ status.md `step` %s"
                % (slug, r.group(1), s.group(1)))
    return None


def candidate_pointers(digest_text):
    """후보 두 절의 목록 줄에서 `(슬러그, 취소선 여부)` 를 뽑는다.

    **절로 자르는 것이 설계의 결정이다**(`done_section` 과 같은 이유) — 파일 전체를
    보면 `## 완료` 절의 서술이 후보 포인터처럼 읽혀 판정이 흐려진다.
    """
    out = []
    in_section = False
    for line in digest_text.split("\n"):
        if line.startswith("## "):
            in_section = line.startswith(CANDIDATE_HEAD)
            continue
        if not in_section or not line.startswith("- "):
            continue
        for slug in STRIKE_POINTER.findall(line):
            out.append((slug, line.startswith("- ~~")))
    return out


def strike_gap(digest_text, index_text):
    """닫힌 후보인데 취소선이 없는 자리를 한 줄로 돌려준다. 없으면 `None`.

    **몸통을 함수로 뺀 이유는 `step_gap`·`iter_gap` 과 같다** — 실물 두 문서는 늘
    맞춰져 있어서 판정을 무력화하는 변이가 조용히 산다. 실물은 `StrikeSyncTest` 가,
    갈래는 `StrikeGapTest` 가 부른다.

    **대조하는 두 쪽이 서로 다른 문서다** — `digest` 후보 줄의 취소선 ↔ `index.md`
    계획 행의 상태 칸. 계획이 `완료` 인데 후보 줄이 살아 있으면 다음 탐색이 닫힌
    항목을 열린 것으로 센다(계획 38 이 실제로 그렇게 오염됐다).
    """
    for slug, struck in candidate_pointers(digest_text):
        row = re.search(PLAN_ROW % re.escape(slug), index_text, re.M)
        if row is None:
            return ("index.md 에서 `| plan_%s |` 행을 못 찾았다 — 후보 줄이 가리키는"
                    " 계획이 등재에 없다" % slug)
        if row.group(1).strip() != "완료":
            continue  # 진행 중인 계획을 가리키는 줄은 아직 열려 있는 것이 맞다.
        if not struck:
            return ("닫힌 후보에 취소선이 없다 — index.md `plan_%s` 는 `완료` 인데"
                    " digest 후보 줄이 `- ~~` 로 시작하지 않는다" % slug)
    return None


def verdict_gap(index_text):
    """완료 행의 e2e 칸이 판정이 아닌 자리를 한 줄로 돌려준다. 없으면 `None`.

    **몸통을 함수로 뺀 이유는 `step_gap`·`iter_gap`·`strike_gap` 과 같다** — 실물
    `index.md` 는 고치고 나면 늘 맞아서, 검사가 문서에만 붙어 있으면 판정을 무력화하는
    변이가 조용히 산다(계획 60 실측 6/6 생존 · 계획 61 실측 4/4 생존). 실물은
    `VerdictSyncTest` 가, 갈래는 `VerdictGapTest` 가 부른다.

    **`완료` 행만 본다** — 진행 중인 계획의 e2e 칸은 아직 `—` 인 것이 맞다.
    """
    rows = VERDICT_ROW.findall(index_text)
    heads = VERDICT_ROW_HEAD.findall(index_text)
    if len(rows) != len(heads):
        return ("index.md 의 계획 행 %d개 중 %d개만 다섯째 칸까지 읽혔다 — 표의 열"
                " 모양이 바뀌었다(e2e 를 다섯째 칸으로 가정한다)"
                % (len(heads), len(rows)))
    for slug, status, verdict in rows:
        if status.strip() != "완료":
            continue
        cell = verdict.strip()
        if VERDICT_DATE.fullmatch(cell):
            return ("e2e 칸에 판정이 아니라 날짜가 있다 — index.md `plan_%s` 의 다섯째"
                    " 칸이 `%s` 다. 판정은 docs/e2e/<슬러그>/result.md 에 있다"
                    % (slug, cell))
    return None


class DocHeadTest(unittest.TestCase):
    def test_append_targets_start_with_h1(self):
        for name in APPEND_TARGETS:
            with self.subTest(doc=name):
                path = DOCS / name
                # 경로를 잘못 잡으면 아래 단언이 빈 문자열 위에서 조용히 통과한다.
                self.assertTrue(path.is_file(), "기록 문서를 못 찾았다: %s" % path)
                first = path.read_text(encoding="utf-8").split("\n", 1)[0]
                self.assertRegex(
                    first, DOC_HEAD,
                    "%s 의 첫 줄이 H1 이 아니다 — 머리가 본문에 빨려 들어갔다: %r"
                    % (name, first))


class DocHeadPatternTest(unittest.TestCase):
    """`DOC_HEAD` 자신을 리터럴로 붙든다 — 위 검사는 자기를 못 잰다.

    실물 세 문서가 늘 H1 로 시작해서, 판정을 `^` 로 넓혀도 `DocHeadTest` 는 조용히
    초록이다(2026-09-06 실측: 전수 618건에서 죽은 단언 0). `CitationPatternTest` 가
    같은 자리에서 배운 것이라 관용구를 그대로 베낀다 — 판정 대상을 문서가 아니라
    **코드 안에 고정**한다.
    """

    # 머리로 인정해야 하는 꼴 — 실물을 베끼지 않는 **합성 리터럴**이다.
    # 실물 제목이 바뀌어도 이 셋은 안 움직인다(그것이 두 층을 가른 목적이다).
    # 실물 첫 줄을 재는 것은 위 `DocHeadTest` 몫이다.
    CAUGHT = (
        "# 아카이브 요약",
        "# 계획 색인",
        "# 기록 (현재)",
    )
    # 머리가 아닌 꼴 — 판정을 넓히는 변이는 여기서 죽는다.
    NOT_CAUGHT = (
        "## 완료",              # H2 는 머리가 아니다
        "#제목",                # 공백이 없으면 마크다운 제목이 아니다
        "# ",                   # 제목 없는 H1
        "",                     # 빈 첫 줄
        "- [6] **항목**",       # 이 파일이 존재하게 만든 그 사고의 모양
        "  # 들여쓴 머리",      # 들여쓰면 1번 줄의 머리가 아니다
    )

    def test_pattern_catches_document_heads(self):
        for line in self.CAUGHT:
            with self.subTest(line=line):
                self.assertRegex(line, DOC_HEAD, "머리를 머리로 안 읽는다 — 검사가 좁아졌다")

    def test_pattern_leaves_non_h1_heads(self):
        for line in self.NOT_CAUGHT:
            with self.subTest(line=line):
                self.assertNotRegex(line, DOC_HEAD,
                                    "머리가 아닌 것을 머리로 읽는다 — 판정이 넓어졌다")


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


class SpecCitationTest(unittest.TestCase):
    """`src`·`tests`·`e2e` 가 `concept.md:<N>` 으로 대는 주소가 실재하는 줄인가.

    사양은 사람이 고치는 읽기 전용 문서인데, 줄 하나가 끼거나 빠지면 열여덟 개 주소가
    **조용히** 한 칸씩 밀린다. 값은 다 맞고 주소만 썩는 구조라 소스만 보는 테스트가
    구조적으로 못 본다 — 2026-09-06 실측에서 다섯 자리가 이미 빈 줄을 대고 있었다.
    주소가 서야 그 위에 값 대조(사양 숫자 ↔ 상수)를 얹을 자리가 생긴다.
    """

    # 리터럴 안의 `\.` 때문에 이 줄 자신은 자기 정규식에 안 물린다 — 자기를 세지 않는다.
    CITE = re.compile(r"concept\.md:([0-9]+)(?:-([0-9]+))?")
    ROOTS = ("src", "tests", "e2e")
    # 오늘 18건이다. 정규식이 좁아지면 0건 수집 위에서 조용히 초록이 된다.
    MIN_HITS = 14
    # 인용과 같은 줄, 인용 **뒤**에 따옴표로 옮겨 적은 문구. 앞을 안 보는 것은
    # 인용을 통째로 품은 실패 메시지를 사양 문구로 오인하지 않기 위해서다.
    PHRASE = re.compile(r'"([^"\n]+)"')
    # 인용을 주석으로 단 상수 — 값 표기가 사양 문장 안에 그대로 있어야 한다.
    CONST = re.compile(r"^\s*[A-Z_][A-Z0-9_]*\s*=\s*([^#]+)")
    NUM = re.compile(r"[0-9]+(?:\.[0-9]+)?")
    # 오늘 문구 2 · 값 5. 추출기가 깨지면 0건 대조 위에서 조용히 초록이 된다.
    # 하한이 5 면 **값 축의 크기와 같아** 문구 추출기만 죽는 날(7→5) 그대로 초록이다.
    # 두 축 중 하나가 통째로 죽는 것을 물려면 큰 축보다 하나 위여야 한다.
    MIN_CHECKS = 6

    @staticmethod
    def _has_number(cited, num):
        """숫자 하나가 **온전한 수로** 사양 줄에 있나.

        부분일치는 대조를 통째로 무르게 만든다 — `50` 은 `500ms` 안에도 있어서
        JS 예산 인용을 전혀 다른 항목(근거 문단 p95)에 옮겨도 초록이었다.
        앞뒤로 숫자·소수점이 붙지 않은 자리만 센다.
        """
        return re.search(r"(?<![0-9.])%s(?![0-9])" % re.escape(num),
                         cited) is not None

    @classmethod
    def _anchors(cls, line, pos):
        """인용이 같은 줄에 데리고 있는 앵커 — `(문구들, 값들)`.

        `pos` 는 인용이 끝난 자리다. 문구는 그 뒤 큰따옴표 안, 값은 그 줄이
        상수 대입일 때의 숫자다. 대조 축과 의무 축이 **같은 추출기를 본다** —
        갈라 놓으면 한쪽만 죽는 날 다른 쪽이 조용히 통과한다.
        """
        nums = set()
        const = cls.CONST.match(line)
        if const:
            for tok in cls.NUM.findall(const.group(1)):
                nums.add(tok)
                if "." in tok:                # `5.0` 은 사양에 `5` 로 적힌다
                    nums.add(tok.rstrip("0").rstrip("."))
        return cls.PHRASE.findall(line[pos:]), nums

    def _citations(self):
        """`(경로, 줄번호, 줄, 인용 끝 위치, 시작행, 끝행)` 전수."""
        hits = []
        for root in self.ROOTS:
            for path in sorted((DOCS.parent / root).rglob("*.py")):
                text = path.read_text(encoding="utf-8")
                for no, line in enumerate(text.split("\n"), 1):
                    for m in self.CITE.finditer(line):
                        hits.append((path, no, line, m.end(), int(m.group(1)),
                                     int(m.group(2) or m.group(1))))
        self.assertGreaterEqual(
            len(hits), self.MIN_HITS,
            "인용을 %d건밖에 못 모았다 — 수집 정규식이 깨졌다 (0건 수집 = 거짓 초록)"
            % len(hits))
        return hits

    def test_spec_citations_point_at_real_lines(self):
        spec = DOCS / "specs" / "concept.md"
        lines = spec.read_text(encoding="utf-8").split("\n")
        for path, no, _line, _pos, start, end in self._citations():
            label = "%s:%d" % (path.relative_to(DOCS.parent), no)
            with self.subTest(label):
                self.assertLessEqual(
                    end, len(lines),
                    "%s 가 사양 %d행을 대는데 사양은 %d줄뿐이다"
                    % (label, end, len(lines)))
                self.assertTrue(
                    lines[start - 1].strip(),
                    "%s 가 대는 사양 %d행이 빈 줄이다 — 인용 쪽 주소가 밀렸다"
                    % (label, start))

    def test_spec_quotes_match_cited_lines(self):
        """주소가 실재해도 **다른 항목**을 가리키면 여전히 거짓말이다.

        주소 축(위)은 빈 줄만 문다. 사양은 한 항목이 여러 줄이라 한 칸 밀린
        주소가 멀쩡한 이웃 줄에 착지한다 — 2026-09-06 실측에서 네 자리가
        그랬다(JS 예산은 50행이 아니라 51행, 합격선은 22행이 아니라 23행).
        인용 쪽이 옮겨 적은 문구와 상수 값을 대상 줄에서 되찾아 그 착지를 문다.
        """
        lines = (DOCS / "specs" / "concept.md").read_text(
            encoding="utf-8").split("\n")
        checks = 0
        for path, no, line, pos, start, end in self._citations():
            if end > len(lines):
                continue                      # 주소 축이 이미 문 자리다
            cited = "\n".join(lines[start - 1:end])
            label = "%s:%d" % (path.relative_to(DOCS.parent), no)
            phrases, nums = self._anchors(line, pos)
            for phrase in phrases:
                checks += 1
                with self.subTest(label + " 문구"):
                    self.assertIn(
                        phrase, cited,
                        '%s 가 "%s" 를 사양 %d행에서 옮겼다는데 그 줄엔 없다'
                        % (label, phrase, start))
            if not nums:
                continue
            checks += 1
            with self.subTest(label + " 값"):
                self.assertTrue(
                    any(self._has_number(cited, n) for n in nums),
                    "%s 의 상수 값 %s 이 사양 %d행 어디에도 없다"
                    % (label, sorted(nums), start))
        self.assertGreaterEqual(
            checks, self.MIN_CHECKS,
            "대조를 %d건밖에 못 했다 — 문구·값 추출기가 깨졌다" % checks)

    def test_every_citation_carries_an_anchor(self):
        """앵커 없는 인용은 한 칸 밀려 이웃 항목에 착지해도 조용하다.

        위의 두 자는 **옮겨 적은 것이 있는 인용만** 잰다 — 주소 축은 빈 줄만 물고
        대조 축은 문구·값이 있는 줄만 돈다. 2026-09-06 실측에서 인용 열여덟 중
        **열둘**이 그 밖이었고, `e2e/perf_crawl.py:1` 의 주소를 `:44`→`:45` 로
        민 변이가 전수 초록으로 살아남았다. 앵커를 의무로 만들어 그 밖을 없앤다.
        """
        for path, no, line, pos, _start, _end in self._citations():
            label = "%s:%d" % (path.relative_to(DOCS.parent), no)
            with self.subTest(label):
                phrases, nums = self._anchors(line, pos)
                self.assertTrue(
                    phrases or nums,
                    "%s 에 사양에서 옮겨 적은 것이 없다 — 인용 뒤 같은 줄에 "
                    "큰따옴표로 사양 문구 조각을 적어라" % label)


class IterationSyncTest(unittest.TestCase):
    """`metrics.md` 의 `반복` 과 `status.md` 의 `iteration` 이 같은 수인가.

    사람이 매 반복 끝에 두 곳을 손으로 갱신하는데, 어긋난 채로 간 것이 **4회**
    재발했다(`digest ## 반복 실패`). 어긋나면 다음 반복이 자기 번호를 잘못 적고
    기록이 통째로 밀린다. 규율이 아니라 스위트가 붙든다.

    매치가 `None` 이면 비교 전에 실패한다 — 표 형식이 바뀌면 검사가 `None == None`
    위에서 조용히 통과하는 것이 여기 유일한 눈먼 자리다.
    **판정은 `iter_gap` 이 한다** — 갈래를 실물 없이 밟으려고 뺀 것이고,
    그것을 밟는 것은 `IterGapTest` 다.
    """

    def test_metrics_and_status_agree(self):
        gap = iter_gap((DOCS / "status.md").read_text(encoding="utf-8"),
                       (DOCS / "metrics.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)


class StepSyncTest(unittest.TestCase):
    """`index.md` 의 계획 행 스텝 칸과 `status.md` 의 `step` 이 같은가.

    `IterationSyncTest` 가 닫은 것은 `반복`↔`iteration` 축뿐이라 **스텝 칸은 아무도
    안 붙들었다** — `digest ## 반복 실패` 의 「스텝을 커밋하면서 `index.md` 의 숫자를
    안 올린다」가 **4회** 재발했고, 최근 30커밋 실측에서도 11건이 어긋난 채 갔다.
    어긋나는 방향은 11/11 전부 `index.md` 가 뒤처지는 쪽이다.

    **집는 방법은 `plan:` 슬러그다**(안 D). 상태 칸(`진행`/`완료`)을 보는 안은 계획
    커밋과 index 등재 커밋이 갈린 자리에서 오탐이거나 침묵이었다 —
    슬러그로 집으면 행이 있거나(대조한다) 없거나(그것이 결함이다) 둘 중 하나다.

    셋 다 매치가 `None` 이면 비교 전에 실패한다 — 조용히 지나가는 갈래는 0개다.
    **판정은 `step_gap` 이 한다** — 갈래를 실물 없이 밟으려고 뺀 것이고,
    그것을 밟는 것은 `StepGapTest` 다.
    """

    def test_index_row_and_status_agree(self):
        gap = step_gap((DOCS / "status.md").read_text(encoding="utf-8"),
                       (DOCS / "index.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)


class StepPatternTest(unittest.TestCase):
    """`STEP_LINE`·`PLAN_SLUG`·`STEP_ROW` 자신을 합성 표로 붙든다.

    `StepSyncTest` 는 실물 문서 위에서만 도는데, 문서를 맞춰 놓으면 **넓어지는 변이가
    조용히 산다** — 아무 행이나 잡아도, 접두로 넓혀도 초록이다. `IterationPatternTest`·
    `CitationPatternTest` 가 같은 자리에서 배운 것이라 검사 대상을 코드에 고정한다.

    표는 ① 다른 슬러그 행을 **앞에** ② 접두가 같은 더 긴 슬러그 행을 **앞에** 둔다 —
    넓힌 정규식은 엉뚱한 수를 집는다. ③ 대상 행의 상태 칸은 `완료` 다: 안 D 는 상태를
    안 보므로 그래도 잡혀야 한다. ④ **줄 중간에서 시작하는 잡음 행**을 대상 행 앞에
    둔다 — `^` 를 지운 변이는 이 행의 `8/8` 을 집는다(2026-09-06 실측: 앵커를 지우는
    변이 넷이 전수 620건에서 4/4 생존했다). ①과 ④의 수를 다르게 두는 것이 조건이다:
    같은 수면 「슬러그를 안 본다」와 「`^` 가 죽었다」가 한 값으로 겹쳐 실패 메시지가
    범인을 못 가린다.
    """

    TABLE = "\n".join([
        "| plan_endtag-cut-cover | 완료 | loop/x | 9/9 | 통과 |",
        "| plan_index-step-sync-2 | 진행 | loop/x | 3/7 | 미정 |",
        "| 메모 | 아래는 옛 행 | plan_index-step-sync | 완료 | loop/x | 8/8 | 미정 |",
        "| plan_index-step-sync | 완료 | loop/x | 1/1 | 미정 |",
    ])

    def test_row_is_picked_by_exact_slug(self):
        m = step_row("index-step-sync").search(self.TABLE)
        self.assertIsNotNone(m, "슬러그의 행을 못 찾았다 — 행 패턴이 죽었다")
        self.assertEqual(
            "1/1", m.group(1),
            "남의 행을 물었다 — `9/9` 면 슬러그를 안 보고 앞 행을, `3/7` 이면 "
            "`plan_index-step-sync-2` 를 접두로, `8/8` 이면 `^` 가 죽어 줄 중간의 "
            "잡음 행을 집었다")

    def test_absent_slug_matches_nothing(self):
        # 행이 없으면 `None` 이라야 위 검사가 «등재 누락» 으로 실패할 수 있다.
        self.assertIsNone(step_row("no-such-plan").search(self.TABLE),
                          "없는 슬러그의 행을 잡았다 — 슬러그를 안 보고 있다")

    def test_status_lines_need_the_whole_line(self):
        m = STEP_LINE.search("attempt: 0\nstep: 1/1\niteration: 352")
        self.assertIsNotNone(m, "`step: <N/M>` 줄을 못 찾았다")
        self.assertEqual("1/1", m.group(1))
        self.assertIsNone(STEP_LINE.search("step: 1"),
                          "`N/M` 이 아닌 것을 스텝으로 읽었다")
        # 위 세 줄은 형식만 잰다 — 앵커를 지워도 그대로 초록이라, 앵커를 실제로 재는
        # 것은 아래 둘이다(`IterationPatternTest` 의 `ITER_LINE` 과 같은 관용구).
        self.assertIsNone(STEP_LINE.search("x step: 1/1"),
                          "줄 중간에 붙은 꼴을 물었다 — `^` 가 죽었다")
        self.assertIsNone(STEP_LINE.search("step: 1/1x"),
                          "꼬리가 붙은 꼴을 물었다 — `$` 가 죽었다")
        m = PLAN_SLUG.search("step: 1/1\nplan: index-step-sync 계획 60 (설계 완료)")
        self.assertIsNotNone(m, "`plan: <슬러그>` 줄을 못 찾았다")
        self.assertEqual("index-step-sync", m.group(1),
                         "슬러그 뒤의 설명까지 이름으로 읽었다")
        self.assertEqual("null", PLAN_SLUG.search("plan: null").group(1))
        self.assertIsNone(PLAN_SLUG.search("x plan: a"),
                          "줄 중간에 붙은 꼴을 물었다 — `^` 가 죽었다")


class StepGapTest(unittest.TestCase):
    """`step_gap` 의 갈래를 합성 문자열로 전부 밟는다.

    `StepPatternTest` 가 재는 것은 **정규식 셋**이고, 그 위에 얹힌 **판정**은
    `StepSyncTest` 가 실물 문서로만 불렀다. 문서는 늘 맞춰져 있어서
    2026-09-06 실측에서 판정을 무력화하는 변이 **6종이 전수 609건에서 6/6 생존**했다 —
    ① null 갈래 기대값 비틀기 ② null 갈래 삭제 ③ 대조를 자기비교로 바꾸기
    ④ 「index 에 행이 없다」 가드 삭제 ⑤·⑥ 「status 에 줄이 없다」 가드 삭제.
    `CitationPatternTest`·`ArchiveMatchTest` 가 같은 자리에서 배운 것이고,
    설계서가 적은 「조용히 지나가는 갈래는 0개다」를 실제로 재는 것이 여기다.
    """

    # 접두가 같은 더 긴 슬러그 행을 앞에 둔다 — `StepPatternTest.TABLE` 과 같은 뜻.
    INDEX = "\n".join([
        "| plan_index-step-sync-2 | 진행 | loop/x | 3/7 | 미정 |",
        "| plan_index-step-sync | 진행 | loop/x | 1/1 | 미정 |",
    ])

    @staticmethod
    def status(step, plan):
        return "attempt: 0\nstep: %s\nplan: %s\nctx: 62\n" % (step, plan)

    def test_agreeing_docs_have_no_gap(self):
        self.assertIsNone(
            step_gap(self.status("1/1", "index-step-sync 계획 60"), self.INDEX),
            "맞는 문서를 어긋났다고 신고했다 — 매 반복이 빨개진다")

    def test_step_mismatch_is_reported(self):
        gap = step_gap(self.status("1/1", "index-step-sync"),
                       self.INDEX.replace("| 1/1 |", "| 0/1 |"))
        self.assertIsNotNone(gap, "index 가 0/1 인데 통과시켰다 — 4회 재발한 그 결함이다")
        self.assertIn("0/1", gap, "어느 수가 어긋났는지 안 적었다")

    def test_missing_index_row_is_reported(self):
        gap = step_gap(self.status("1/1", "no-such-plan"), self.INDEX)
        self.assertIsNotNone(gap, "index 에 행이 없는데 통과시켰다 — 등재 누락이 샌다")
        self.assertIn("no-such-plan", gap, "어느 슬러그가 없는지 안 적었다")

    def test_null_plan_requires_the_zero_step(self):
        self.assertIsNone(step_gap(self.status("0/0", "null"), self.INDEX),
                          "`plan: null` + `step: 0/0` 은 하네스 템플릿의 정상 상태다")
        gap = step_gap(self.status("1/1", "null"), self.INDEX)
        self.assertIsNotNone(gap, "`plan: null` 인데 스텝이 흘렀다 — 안 잡혔다")
        self.assertIn("1/1", gap, "흘러간 스텝을 안 적었다")

    def test_missing_status_lines_are_reported(self):
        # 머리 형식이 바뀌면 `None` 위에서 조용히 통과하는 것이 유일한 눈먼 자리다.
        self.assertIsNotNone(step_gap("plan: index-step-sync\n", self.INDEX),
                             "`step:` 줄이 없는데 통과시켰다")
        self.assertIsNotNone(step_gap("step: 1/1\n", self.INDEX),
                             "`plan:` 줄이 없는데 통과시켰다")


class ArchiveIndexTest(unittest.TestCase):
    """아카이브 전부가 `digest.md` 의 `## 완료` 절 명부에 실려 있는가.

    `digest.md` 는 스스로 *"원본은 `history_<NNN>.md` 에 그대로 있다"* 로 아카이브
    색인을 자처하는데, 오늘 22개 중 다섯이 그 절에 없었다. 색인에 구멍이 나면 그
    반복들의 판단 재료를 이름으로 못 찾는다 — 회전이 완료 항목을 지울 때마다 는다.

    **범위를 `## 완료` 절로 자른다.** `digest.md` 전체를 보면 `history_001.md` 를
    초록으로 만드는 것이 **구멍을 신고하는 그 문장 자신**이다(`## 반복 실패`).
    그리고 경계 매칭이 없으면 `plan_history_019.md` 가 `history_019.md` 를 대신
    통과시킨다 — 명부가 가리키는 것은 아카이브 원본뿐이다.
    """

    def test_every_archive_is_in_digest_done_section(self):
        archives = [p.name for p in sorted(DOCS.glob("history_[0-9]*.md"))]
        # glob 이 빈손이면 아래 단언이 "구멍 0" 위에서 조용히 통과한다.
        self.assertTrue(archives, "아카이브를 못 찾았다 — 경로가 틀렸다: %s" % DOCS)
        digest = DOCS / "digest.md"
        self.assertTrue(digest.is_file(), "digest 를 못 찾았다: %s" % digest)
        section = done_section(digest.read_text(encoding="utf-8"))
        # 절을 못 찾으면 빈 텍스트 위에서 통과하는 것이 아니라 실패한다.
        self.assertIsNotNone(section, "digest.md 에서 `## 완료` 절을 못 찾았다")
        missing = [n for n in archives if not indexed(n, section)]
        self.assertEqual(
            [], missing,
            "아카이브가 `digest.md` 의 `## 완료` 명부에 없다 — 이름으로 못 찾는다:\n"
            + "\n".join("  " + n for n in missing))


class IterationPatternTest(unittest.TestCase):
    """`ITER_ROW`·`ITER_LINE` 자신을 합성 표로 붙든다 — 위 검사는 자기를 못 잰다.

    `IterationSyncTest` 는 실물 문서 위에서만 도는데, 오늘 `metrics.md` 는 정확한
    행이 이웃들보다 **먼저** 나온다. 그래서 정규식을 넓혀도(`| 반복[^|]*|`) 첫 매치가
    그대로라 **초록이다**(2026-09-02 변이 실측). 넓어지는 변이가 사는 자리라
    설계 계약이 적어 둔 *"이웃 세 행은 안 문다"* 를 여기서 잰다.

    아래 표는 이웃을 **일부러 앞에 둔다** — 넓힌 정규식은 엉뚱한 수를 집는다.
    네 번째 행은 **줄 중간에서 시작하는 잡음 행**이다 — `^` 를 지운 변이는 `999` 를
    집는다(2026-09-06 실측: 그 변이가 전수 620건에서 살아 있었다).
    """

    TABLE = "\n".join([
        "| phase | 반복 수 |",
        "| 반복 상한 | 0 |",
        "| 평균 반복 | 5.3 |",
        "| 메모 | 아래는 옛 행 | 반복 | 999 |",
        "| 반복 | 232 |",
    ])

    def test_only_the_exact_row_matches(self):
        m = ITER_ROW.search(self.TABLE)
        self.assertIsNotNone(m, "`| 반복 | <수> |` 행을 못 찾았다 — 정규식이 죽었다")
        self.assertEqual(
            "232", m.group(1),
            "이웃 행을 물었다 — `| 반복 수 |`·`| 반복 상한 |`·`| 평균 반복 |` 은 "
            "반복 번호가 아니고, `999` 면 `^` 가 죽어 줄 중간의 잡음 행을 집은 것이다")

    def test_status_line_needs_the_whole_line(self):
        # `night_iterations:` 는 실제로 같은 프런트매터에 산다. 다만 이 줄이 막는 것은
        # 앵커가 아니라 **복수형 `s`**(`iterations: ` ≠ `iteration: `)다 — 앵커를 지워도
        # 그대로 초록이라, 앵커를 실제로 재는 것은 아래 두 줄이다.
        self.assertIsNone(ITER_LINE.search("night_iterations: 90"),
                          "`night_iterations` 를 `iteration` 으로 읽었다")
        self.assertIsNone(ITER_LINE.search("x iteration: 1"),
                          "줄 중간에 붙은 꼴을 물었다 — `^` 가 죽었다")
        self.assertIsNone(ITER_LINE.search("iteration: 1x"),
                          "꼬리가 붙은 꼴을 물었다 — `$` 가 죽었다")
        m = ITER_LINE.search("plan: x\niteration: 232\nctx: 62")
        self.assertIsNotNone(m, "`iteration: <수>` 줄을 못 찾았다")
        self.assertEqual("232", m.group(1))


class IterGapTest(unittest.TestCase):
    """`iter_gap` 의 갈래를 합성 문자열로 전부 밟는다.

    `IterationPatternTest` 가 재는 것은 **정규식 둘**이고, 그 위에 얹힌 **판정**은
    `IterationSyncTest` 가 실물 문서로만 불렀다. 두 문서는 늘 맞춰져 있어서
    2026-09-06 실측에서 판정을 무력화하는 변이 **4종이 전수 614건에서 4/4 생존**했다 —
    ① 대조를 자기비교로 바꾸기 ②·③ 「행·줄이 없다」 가드 삭제 ④ 판정 통째 삭제.
    `StepGapTest`·`ArchiveMatchTest` 가 같은 자리에서 배운 것이다.
    """

    METRICS = "\n".join([
        "| 평균 반복 | 5.3 |",
        "| 반복 | 356 |",
    ])

    @staticmethod
    def status(iteration):
        return "plan: x\niteration: %s\nctx: 55\n" % iteration

    def test_agreeing_docs_have_no_gap(self):
        self.assertIsNone(
            iter_gap(self.status("356"), self.METRICS),
            "맞는 문서를 어긋났다고 신고했다 — 매 반복이 빨개진다")

    def test_iteration_mismatch_is_reported(self):
        gap = iter_gap(self.status("357"), self.METRICS)
        self.assertIsNotNone(gap, "356 ≠ 357 을 통과시켰다 — 4회 재발한 그 결함이다")
        self.assertIn("356", gap, "어느 수가 어긋났는지 안 적었다")
        self.assertIn("357", gap, "어느 수가 어긋났는지 안 적었다")

    def test_missing_metrics_row_is_reported(self):
        # 표 모양이 바뀌면 `a` 가 `None` 이다 — 조용히 통과하면 안 된다.
        gap = iter_gap(self.status("356"), "| 반복 수 | 356 |")
        self.assertIsNotNone(gap, "metrics 에 행이 없는데 통과시켰다")
        self.assertIn("metrics.md", gap, "어느 문서가 비었는지 안 적었다")

    def test_missing_status_line_is_reported(self):
        gap = iter_gap("night_iterations: 173\n", self.METRICS)
        self.assertIsNotNone(gap, "status 에 줄이 없는데 통과시켰다")
        self.assertIn("status.md", gap, "어느 문서가 비었는지 안 적었다")


class ArchivePatternTest(unittest.TestCase):
    """`ARCHIVE` 자신을 리터럴로 붙든다 — 위 `DocCitationTest` 는 자기를 못 잰다.

    `ARCHIVE` 는 **어느 문서를 줄번호 검사에서 뺄지**를 혼자 정하는데, 넓히는 변이
    셋(`$` 제거 · `re.I` · `[0-9]+`→`[0-9]*`)도 이름 하나를 빼 좁히는 변이 하나도
    전수 620건에서 죽은 단언 0 이었다(2026-09-06 실측). `DocHeadPatternTest` 가
    `DOC_HEAD` 에 하는 일과 같다 — 판정 대상을 실물이 아니라 코드 안에 고정한다.
    """

    # 아카이브로 인정해야 하는 꼴 — **실물 목록이 아니라 접두어 셋의 모양**이다.
    # 실물 아카이브가 늘거나 줄어도 이 셋은 안 움직인다.
    CAUGHT = (
        "history_001.md",
        "plan_history_049.md",
        "design_history_046.md",
    )
    # 아카이브가 아닌 꼴 — 판정을 넓히는 변이는 여기서 죽는다.
    NOT_CAUGHT = (
        "history_current.md",       # 살아 있는 기록 — 빠지면 검사 밖으로 나간다
        "history_001.md.bak.md",    # 끝을 안 묶으면(`$` 제거) 잡힌다
        "history_.md",              # 번호가 없다(`[0-9]+`→`[0-9]*` 가 여기서 죽는다)
        "HISTORY_001.MD",           # 대소문자를 흘리면(`re.I`) 잡힌다
        "digest.md",
        "index.md",
    )

    def test_pattern_catches_archive_names(self):
        for name in self.CAUGHT:
            with self.subTest(name=name):
                self.assertRegex(name, ARCHIVE,
                                 "아카이브를 검사 대상으로 끌어들인다 — 판정이 좁아졌다")

    def test_pattern_leaves_live_docs(self):
        for name in self.NOT_CAUGHT:
            with self.subTest(name=name):
                self.assertNotRegex(name, ARCHIVE,
                                    "살아 있는 문서를 검사에서 뺀다 — 판정이 넓어졌다")


class ArchiveMatchTest(unittest.TestCase):
    """`done_section`·`indexed` 를 합성 `digest` 로 붙든다 — 위 검사는 자기를 못 잰다.

    명부를 넣은 뒤로 실물 `digest.md` 는 **어느 쪽으로 재도 구멍 0** 이다. 범위를
    파일 전체로 넓혀도, 경계 매칭(`(?<![A-Za-z_])`)을 빼도 초록이다(2026-09-02 변이
    실측 — 둘 다 살아남았다). 설계가 갈림길 하나씩을 걸어 고른 두 결정인데
    **아무도 안 재고 있었다.** `CitationPatternTest` 가 `CITATION` 에 하는 일과 같다.
    """

    DIGEST = "\n".join([
        "# 다이제스트",
        "## 반복 실패",
        "- 아카이브 `history_001.md` 의 압축 줄을 안 남긴다",
        "## 완료",
        "- **아카이브 명부** | `history_002.md` `plan_history_003.md`",
        "## 보류",
        "- `history_004.md`",
    ])

    # 명부에 이름으로 실렸다.
    INDEXED = ["history_002.md"]
    # 실리지 않았다 — 셋이 각각 다른 이유다.
    NOT_INDEXED = [
        # 신고문이 자기 신고 대상을 초록으로 만들면 안 된다(`## 반복 실패`).
        "history_001.md",
        # 접두어에 가려졌다 — `plan_history_003.md` 는 원본이 아니다.
        "history_003.md",
        # `## 완료` 절 밖이라 명부가 아니다.
        "history_004.md",
    ]

    def test_indexed(self):
        section = done_section(self.DIGEST)
        for name in self.INDEXED:
            with self.subTest(name=name):
                self.assertTrue(indexed(name, section),
                                "명부에 있는데 못 찾았다: %s" % name)

    def test_not_indexed(self):
        section = done_section(self.DIGEST)
        for name in self.NOT_INDEXED:
            with self.subTest(name=name):
                self.assertFalse(indexed(name, section),
                                 "명부 밖인데 색인으로 셌다: %s" % name)

    def test_missing_section_is_not_a_pass(self):
        # 절 이름이 바뀌면 빈 텍스트 위에서 조용히 통과하는 대신 `None` 이 온다.
        self.assertIsNone(done_section("# 다이제스트\n## 완료된 것\n- 없다"))


class StrikeSyncTest(unittest.TestCase):
    """닫힌 계획을 가리키는 후보 줄에 취소선이 그어져 있나.

    취소선과 「닫혔다 — 계획 NN `slug`, 날짜」는 손으로 긋는 규약이고 **그것을 재는
    단언이 오늘까지 0개였다**. 안 그으면 다음 반복의 탐색이 닫힌 항목을 후보로 다시
    센다 — `DocHeadTest` 가 적어 둔 계획 38 오염과 같은 결과이고, 거기는 머리가
    깨져서였다면 여기는 규약을 안 지켜서다.

    **판정은 `strike_gap` 이 한다** — 갈래를 실물 없이 밟는 것은 `StrikeGapTest` 다.
    """

    def test_closed_candidates_are_struck_through(self):
        gap = strike_gap((DOCS / "digest.md").read_text(encoding="utf-8"),
                         (DOCS / "index.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)

    def test_pointer_extractor_still_bites(self):
        # 추출기가 0을 내면 위 단언은 «볼 것이 없어» 초록이다. 하한을 박아 둔다.
        found = candidate_pointers((DOCS / "digest.md").read_text(encoding="utf-8"))
        self.assertGreaterEqual(
            len(found), STRIKE_POINTER_FLOOR,
            "후보 포인터가 %d개로 줄었다 — 포인터 문구가 바뀌었거나 추출기가 죽었다"
            % len(found))


class StrikeGapTest(unittest.TestCase):
    """`strike_gap` 의 갈래를 합성 문자열로 밟는다.

    실물은 고치면 초록이 되어 갈래가 한 번씩만 지나간다. 특히 **오탐 축**(진행 중인
    계획을 가리키는 열린 줄)은 실물에 표본이 없어 여기서만 밟힌다.

    마지막 하나는 판정이 아니라 **추출기의 범위**를 본다 — 하한 못은 범위가 좁아지는
    쪽만 막고, 넓어지는 쪽은 실물에 표본이 없어 아무도 안 물었다.
    """

    INDEX = ("| plan_done-one | 완료 | loop/x | 1/1 | 통과 | 설명 |\n"
             "| plan_running-one | 진행 | loop/y | 0/1 | — | 설명 |\n")

    def digest(self, line):
        return "# 다이제스트\n## 완료\n- 딴 절\n%s\n- 없다\n" % (
            "## 다음 계획 후보\n" + line)

    def test_struck_closed_candidate_is_quiet(self):
        self.assertIsNone(
            strike_gap(self.digest("- ~~[6] 무엇~~ — **→ 2026-09-06 계획 70 "
                                   "`done-one` 로 열었다**"), self.INDEX))

    def test_unstruck_closed_candidate_is_a_gap(self):
        gap = strike_gap(self.digest("- [6] 무엇 — **→ 2026-09-06 계획 70 "
                                     "`done-one` 로 열었다**"), self.INDEX)
        self.assertIsNotNone(gap)
        self.assertIn("done-one", gap)

    def test_running_plan_is_not_bitten(self):
        # 오탐 축 — 진행 중인 계획을 가리키는 줄은 아직 열려 있는 것이 맞다.
        self.assertIsNone(
            strike_gap(self.digest("- [6] 무엇 — **→ 2026-09-07 계획 71 "
                                   "`running-one` 를 열었다**"), self.INDEX))

    def test_pointer_to_an_unlisted_plan_is_a_gap(self):
        gap = strike_gap(self.digest("- [6] 무엇 — **→ 2026-09-07 계획 72 "
                                     "`no-such-plan` 으로 열었다**"), self.INDEX)
        self.assertIsNotNone(gap)
        self.assertIn("no-such-plan", gap)

    def test_only_candidate_list_lines_are_counted(self):
        # 범위를 **넓히는** 변이는 실물이 조용해 살아남았다(2026-09-07 실측: 절 자르기
        # 제거·목록 줄 요구 제거 둘 다 638건을 통과했다). 넓어지면 남의 절과 본문
        # 산문이 후보로 세어져 **거짓 RED** 가 된다 — 조용한 초록의 반대쪽 실패다.
        text = ("# 다이제스트\n"
                "## 완료\n"
                "- 계획 68 `done-one` 로 열었다 — 닫힌 것을 여기 또 적는다\n"
                "## 다음 계획 후보\n"
                "산문 줄에도 계획 69 `done-one` 으로 열었다 라고 적힐 수 있다\n"
                "- ~~[6] 무엇~~ — **→ 2026-09-06 계획 70 `done-one` 로 열었다**\n")
        self.assertEqual(candidate_pointers(text), [("done-one", True)])


class VerdictSyncTest(unittest.TestCase):
    """완료된 계획 행의 e2e 칸이 판정을 담고 있나.

    같은 표의 넷째 칸은 계획 60(`step_gap`), 둘째 칸은 계획 70(`strike_gap`)이 붙들었는데
    **다섯째 칸은 오늘까지 재는 자가 0개였다** — 그 사이에 `plan_noindex-entity-prefilter`
    행이 판정 대신 날짜(`2026-09-07`)를 담은 채로 갔다. 소비자는 루프 자신이다:
    탐색이 `index.md` 를 「이미 한 것」의 명부로 읽는데, 판정이 없는 행은 그 행만으로
    「e2e 를 통과해서 완료인지」를 알 수 없다.

    **판정은 `verdict_gap` 이 한다** — 갈래를 실물 없이 밟는 것은 `VerdictGapTest` 다.
    """

    def test_done_rows_carry_a_verdict(self):
        gap = verdict_gap((DOCS / "index.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)

    def test_row_extractor_still_bites(self):
        # 추출기가 0을 내면 위 단언은 «볼 것이 없어» 초록이다. 하한을 박아 둔다.
        found = VERDICT_ROW.findall((DOCS / "index.md").read_text(encoding="utf-8"))
        self.assertGreaterEqual(
            len(found), VERDICT_ROW_FLOOR,
            "계획 행이 %d개로 줄었다 — 표의 열 모양이 바뀌었거나 추출기가 죽었다"
            % len(found))


class VerdictGapTest(unittest.TestCase):
    """`verdict_gap` 의 갈래를 합성 표로 밟는다.

    실물은 고치면 초록이 되어 갈래가 한 번씩만 지나간다. 특히 **오탐 축**(`없음(…)`·
    `**새 e2e 0개**(…)` 인 정당한 판정)은 자를 잘못 세웠을 때만 물리므로 여기서 못을 박는다 —
    2026-09-07 실측에서 「`통과` 를 요구한다」안은 실물 여섯 행을 거짓 RED 로 만들었다.
    """

    DONE = "| plan_%s | 완료 | loop/x | 1/1 | %s | 설명 |"
    # **진행 행의 e2e 칸을 일부러 날짜로 둔다** — `—` 로 두면 날짜가 아니라서 완료
    # 가드가 없어도 안 물리고, 그 단언은 아무것도 재지 않는다(2026-09-07 실측: `완료`
    # 가드를 지운 변이가 647건을 그대로 통과했다). 계획 70 이 같은 자리에서 배운 것 —
    # 범위를 **넓히는** 변이는 실물에 표본이 없어 조용히 산다.
    RUNNING = "| plan_running-one | 진행 | loop/y | 0/1 | 2026-09-07 | 설명 |"

    def index(self, *rows):
        head = "# 색인\n\n| 계획 | 상태 | 브랜치 | 스텝 | e2e | 비고 |\n"
        return head + "\n".join(rows) + "\n"

    def test_verdict_row_is_quiet(self):
        self.assertIsNone(verdict_gap(self.index(
            self.DONE % ("done-one", "통과 — 전수 `Ran 639` OK rc 0"))))

    def test_date_only_cell_is_a_gap(self):
        gap = verdict_gap(self.index(self.DONE % ("dated-one", "2026-09-07")))
        self.assertIsNotNone(gap)
        self.assertIn("dated-one", gap)

    def test_non_verdict_wording_is_not_required(self):
        # 오탐 축 — 넷 다 `rules/e2e.md` 가 허용하는 정당한 판정이고 `통과` 가 없다.
        for cell in ("없음(제품 코드 0줄)", "**새 e2e 0개**(기존 스크립트에 더했다)",
                     "생략 — 문서 축", "—"):
            with self.subTest(cell=cell):
                self.assertIsNone(verdict_gap(self.index(self.DONE % ("x-one", cell))))

    def test_date_inside_a_verdict_is_not_a_gap(self):
        # 날짜가 **판정 안에** 있는 것은 판정이다. 칸 전체가 날짜뿐일 때만 문다.
        self.assertIsNone(verdict_gap(self.index(
            self.DONE % ("dated-verdict", "통과(2026-09-07)"))))

    def test_running_row_is_not_bitten(self):
        # 오탐 축 — 진행 중인 계획의 e2e 칸은 아직 비어 있는 것이 맞다.
        self.assertIsNone(verdict_gap(self.index(self.RUNNING)))

    def test_broken_column_shape_is_reported(self):
        # 열이 하나 사라지면 `VERDICT_ROW` 는 그 행을 조용히 건너뛴다 — 침묵이 아니라
        # 실패로 신고한다(계획서 8절의 위험).
        gap = verdict_gap(self.index("| plan_short-one | 완료 | loop/x | 1/1 |"))
        self.assertIsNotNone(gap)
        self.assertIn("열", gap)


if __name__ == "__main__":
    unittest.main()
