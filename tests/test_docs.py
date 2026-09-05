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
# 스텝 번호가 사는 두 자리. `index.md` 는 행이 수십 개라 **`plan:` 슬러그로 집는다** —
# 상태 칸(`진행`/`완료`)은 안 본다(`docs/design_index-step-sync.md` 「결정」).
# 행 패턴은 슬러그를 `re.escape` 해 끼우므로 상수는 템플릿이다. 이름 뒤 ` | ` 를
# 요구해 **접두 일치를 막는다** — 아니면 `plan_index-step-sync-2` 가 대신 통과한다.
# 아래 `StepPatternTest` 가 이 셋을 합성 표로 고정한다.
STEP_LINE = re.compile(r"^step: ([0-9]+/[0-9]+)$", re.M)
PLAN_SLUG = re.compile(r"^plan: ([A-Za-z0-9_-]+)", re.M)
STEP_ROW = r"^\| plan_%s \| [^|]* \| [^|]* \| ([0-9]+/[0-9]+) \|"


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


class IterationSyncTest(unittest.TestCase):
    """`metrics.md` 의 `반복` 과 `status.md` 의 `iteration` 이 같은 수인가.

    사람이 매 반복 끝에 두 곳을 손으로 갱신하는데, 어긋난 채로 간 것이 **4회**
    재발했다(`digest ## 반복 실패`). 어긋나면 다음 반복이 자기 번호를 잘못 적고
    기록이 통째로 밀린다. 규율이 아니라 스위트가 붙든다.

    매치가 `None` 이면 비교 전에 실패한다 — 표 형식이 바뀌면 검사가 `None == None`
    위에서 조용히 통과하는 것이 여기 유일한 눈먼 자리다.
    """

    def test_metrics_and_status_agree(self):
        metrics = (DOCS / "metrics.md").read_text(encoding="utf-8")
        status = (DOCS / "status.md").read_text(encoding="utf-8")
        a = ITER_ROW.search(metrics)
        b = ITER_LINE.search(status)
        self.assertIsNotNone(a, "metrics.md 에서 `| 반복 | <수> |` 행을 못 찾았다")
        self.assertIsNotNone(b, "status.md 에서 `iteration: <수>` 줄을 못 찾았다")
        self.assertEqual(
            a.group(1), b.group(1),
            "반복 번호가 어긋났다 — metrics.md `반복` %s ≠ status.md `iteration` %s"
            % (a.group(1), b.group(1)))


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
    """

    def test_index_row_and_status_agree(self):
        status = (DOCS / "status.md").read_text(encoding="utf-8")
        s = STEP_LINE.search(status)
        p = PLAN_SLUG.search(status)
        self.assertIsNotNone(s, "status.md 에서 `step: <N/M>` 줄을 못 찾았다")
        self.assertIsNotNone(p, "status.md 에서 `plan: <슬러그>` 줄을 못 찾았다")
        slug = p.group(1)
        if slug == "null":
            # 하네스 템플릿의 초기 상태. 대조할 행이 없으니 초기값 자신을 요구한다.
            self.assertEqual(
                "0/0", s.group(1),
                "`plan: null` 인데 `step` 이 %s 다 — 계획 없이 스텝만 흘렀다"
                % s.group(1))
            return
        index = (DOCS / "index.md").read_text(encoding="utf-8")
        r = step_row(slug).search(index)
        self.assertIsNotNone(
            r, "index.md 에 `| plan_%s |` 행이 없다 — 계획 커밋과 등재 커밋이 갈렸다"
            % slug)
        self.assertEqual(
            r.group(1), s.group(1),
            "스텝이 어긋났다 — index.md `plan_%s` %s ≠ status.md `step` %s"
            % (slug, r.group(1), s.group(1)))


class StepPatternTest(unittest.TestCase):
    """`STEP_LINE`·`PLAN_SLUG`·`STEP_ROW` 자신을 합성 표로 붙든다.

    `StepSyncTest` 는 실물 문서 위에서만 도는데, 문서를 맞춰 놓으면 **넓어지는 변이가
    조용히 산다** — 아무 행이나 잡아도, 접두로 넓혀도 초록이다. `IterationPatternTest`·
    `CitationPatternTest` 가 같은 자리에서 배운 것이라 검사 대상을 코드에 고정한다.

    표는 ① 다른 슬러그 행을 **앞에** ② 접두가 같은 더 긴 슬러그 행을 **앞에** 둔다 —
    넓힌 정규식은 엉뚱한 수를 집는다. ③ 대상 행의 상태 칸은 `완료` 다: 안 D 는 상태를
    안 보므로 그래도 잡혀야 한다.
    """

    TABLE = "\n".join([
        "| plan_endtag-cut-cover | 완료 | loop/x | 9/9 | 통과 |",
        "| plan_index-step-sync-2 | 진행 | loop/x | 3/7 | 미정 |",
        "| plan_index-step-sync | 완료 | loop/x | 1/1 | 미정 |",
    ])

    def test_row_is_picked_by_exact_slug(self):
        m = step_row("index-step-sync").search(self.TABLE)
        self.assertIsNotNone(m, "슬러그의 행을 못 찾았다 — 행 패턴이 죽었다")
        self.assertEqual(
            "1/1", m.group(1),
            "남의 행을 물었다 — 앞선 다른 슬러그 행이나 `plan_index-step-sync-2` 를 "
            "접두로 집었다")

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
        m = PLAN_SLUG.search("step: 1/1\nplan: index-step-sync 계획 60 (설계 완료)")
        self.assertIsNotNone(m, "`plan: <슬러그>` 줄을 못 찾았다")
        self.assertEqual("index-step-sync", m.group(1),
                         "슬러그 뒤의 설명까지 이름으로 읽었다")
        self.assertEqual("null", PLAN_SLUG.search("plan: null").group(1))


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
    """

    TABLE = "\n".join([
        "| phase | 반복 수 |",
        "| 반복 상한 | 0 |",
        "| 평균 반복 | 5.3 |",
        "| 반복 | 232 |",
    ])

    def test_only_the_exact_row_matches(self):
        m = ITER_ROW.search(self.TABLE)
        self.assertIsNotNone(m, "`| 반복 | <수> |` 행을 못 찾았다 — 정규식이 죽었다")
        self.assertEqual(
            "232", m.group(1),
            "이웃 행을 물었다 — `| 반복 수 |`·`| 반복 상한 |`·`| 평균 반복 |` 은 "
            "반복 번호가 아니다")

    def test_status_line_needs_the_whole_line(self):
        # `night_iterations:` 는 실제로 같은 프런트매터에 산다.
        self.assertIsNone(ITER_LINE.search("night_iterations: 90"),
                          "`night_iterations` 를 `iteration` 으로 읽었다")
        m = ITER_LINE.search("plan: x\niteration: 232\nctx: 62")
        self.assertIsNotNone(m, "`iteration: <수>` 줄을 못 찾았다")
        self.assertEqual("232", m.group(1))


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


if __name__ == "__main__":
    unittest.main()
