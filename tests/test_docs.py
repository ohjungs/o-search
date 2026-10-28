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

import ast
import pathlib
import re
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
# `dup_def_gap` 의 모집단. `scripts/` 는 오늘 `.py` 가 0개지만(`merge-to-main.sh` 뿐)
# `rglob` 이라 생기면 저절로 들어온다.
SOURCE_DIRS = ("src", "tests", "e2e", "scripts")
# 오늘 실측은 62파일이다(src 12 · tests 25 · e2e 25 · scripts 0). 하한을 두는 이유는
# **0 을 세면서 통과하지 않기** 위해서다 — 경로 오타나 `rglob` 실패로 아무것도 안 훑고
# 「위반 0」을 외치는 것이 이 저장소의 재발 항목이고(계획 101 이 `\bHTTPServer\(` 로
# 겪었다), `test_deps.py` 의 `FILE_FLOOR` 가 같은 자리를 같은 이유로 막는다.
SOURCE_FLOOR = 50
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
# 셋째 증인. `status`·`metrics` 는 병합이 **함께** 실어 올 수 있고(2026-09-09 실물:
# 둘 다 490, 기록은 494) 그때 둘만의 대조는 조용하다. `history_current.md` 는 append
# 전용이라 양쪽 기록이 다 남는 유일한 자리다. `### 반복 487~490` 같은 범위 머리에서는
# **끝 번호**를 문다. `HISTORY_ENTRY_HEAD` 와 같은 머리를 보지만 저쪽은 항목을 세고
# 이쪽은 번호를 읽는다 — 붙이면 한쪽 변이가 다른 축을 조용히 끈다.
HIST_ITER = re.compile(r"^### 반복 (?:[0-9]+~)?([0-9]+)", re.M)
# 기록 문서의 머리. 첫 줄 하나에만 대므로 `re.M` 은 없다 — `^` 는 문자열 머리다.
# `\S` 가 `#제목`·`# `(제목 없는 H1)를 가른다. 아래 `DocHeadPatternTest` 가 이것을
# 합성 리터럴로 고정한다(실물 문서는 늘 맞는 모양이라 자기를 못 잰다).
DOC_HEAD = re.compile(r"^# \S")
# 스텝 번호가 사는 두 자리. `index.md` 는 행이 수십 개라 **`plan:` 슬러그로 집는다** —
# 상태 칸(`진행`/`완료`)은 안 본다(`docs/design_history_046.md` 「결정」).
# 행 패턴은 슬러그를 `re.escape` 해 끼우므로 상수는 템플릿이다. 이름 뒤 ` | ` 를
# 요구해 **접두 일치를 막는다** — 아니면 `plan_index-step-sync-2` 가 대신 통과한다.
# 아래 `StepPatternTest` 가 이 셋을 합성 표로 고정한다.
STEP_LINE = re.compile(r"^step: ([0-9]+/[0-9]+)$", re.M)
PLAN_SLUG = re.compile(r"^plan: ([A-Za-z0-9_-]+)", re.M)
STEP_ROW = r"^\| plan_%s \| [^|]* \| [^|]* \| ([0-9]+/[0-9]+) \|"
# 후보 절이 계획을 가리키는 포인터. 「… **→ 2026-09-06 계획 68 `slug` 로 열었다**」
# 꼴만 문다. 조사 셋(`로`·`으로`·`를`)은 실물에 다 있고, **슬러그 백틱을 요구하는
# 것이 부정문을 가르는 자리다** — 「계획 49 범위 밖이라 안 열었다」에는 백틱 슬러그가
# 없어서 안 물린다(2026-09-07 **회전 뒤** 실측: 후보 두 절의 `열었다` 2자리 중 1자리가
# 포인터, 나머지 하나가 그 부정문이다 — 회전 전에는 11자리 중 9자리였다).
# **이 수는 회전이 흔든다** — 못을 여기 세우면 안 되는 이유이고, 그래서 하한은
# `CANDIDATE_HEAD_FLOOR` 로 옮겼다. 아래 `StrikeGapTest` 가 갈래를 합성으로 밟는다.
STRIKE_POINTER = re.compile(r"계획 [0-9]+ `([A-Za-z0-9_-]+)` (?:로|으로|를) 열었다")
# 같은 계획 행의 **상태 칸**. `STEP_ROW` 는 넷째 칸을 보고 이쪽은 둘째 칸을 본다.
PLAN_ROW = r"^\| plan_%s \| ([^|]*) \|"
# 같은 둘째 칸을 **슬러그 자리를 열어** 훑는다. 재는 대상이 「지금 도는 계획」이 아니라
# 「이 표에 진행인 채로 남은 행 전부」라 이름을 미리 알 수 없다. `PLAN_ROW` 를 그대로
# 먹여 만드는 이유는 표의 열 모양이 바뀌는 날 **둘이 함께 움직이게** 하려는 것이다.
LIVE_ROW = re.compile(PLAN_ROW % r"([A-Za-z0-9_-]+)", re.M)
# 상태 칸이 이것과 **같아야** 진행이다. `in` 으로 보면 `보류(미완)` 은 우연히 살지만
# `진행(재개)` 같은 표기가 생기는 날 갈린다 — `LiveGapTest` 가 그 자리를 재고 있다.
LIVE_MARK = "진행"
# 상태 칸이 「완료」인가. **다섯 자가 같은 칸을 읽으므로 술어를 한 자리에 둔다**
# (`archive_gap`·`strike_gap`·`opened_candidates`·`false_strike`·`verdict_gap`).
# 계획 124 가 `archive_gap` 만 고쳤더니 **나머지 넷이 리터럴로 남아** 실물에서 갈렸다:
# `verdict_gap` 이 `완료(2026-10-26 …)` 2행에 **조용**했고(e2e 칸 검사가 꺼진 것이다),
# `false_strike` 는 분기가 거꾸로라 그 2행에 **거짓 양성**을 낼 자리였다. 호출부를
# 다섯 번 패치하는 것보다 공유 지점 하나가 작다(ponytail 근본 원인).
#
# **접두만으로는 넓다** — `완료 예정`·`완료 대기`·`완료 안 됨` 이 전부 완료로 읽혀
# **안 끝난 계획의 문서를 치우라고 요구**한다(실측 넷 다 GAP). 그러면 이 저장소가
# 지키려는 오탐 축(중복 방지가 승인 대기 계획을 못 본다 · `discover.md` 5절)이 깨진다.
# 그래서 **낱말 뒤에 구분자를 요구한다**: 끝이거나 `(`·`·` 다. 실물 두 꼴
# (`완료` · `완료(2026-10-26 …)`)은 통과하고 위 넷은 전부 거절된다.
#
# **굵게와 공백을 함께 벗긴다** — `**보류**` 가 실물이라 `**완료**` 는 내일 쓰일 꼴이고,
# `** 완료 **` 처럼 안쪽에 공백이 낀 꼴도 같은 손이 만든다(`strip("*")` 만으로는 샜다).
DONE_MARK = "완료"
DONE_TAIL = "(·"


def is_done(cell):
    """상태 칸이 완료인가. 어휘 판정을 **한 자리**에 모은 술어다 (위 주석)."""
    body = cell.strip().strip("* ").strip()
    if not body.startswith(DONE_MARK):
        return False
    rest = body[len(DONE_MARK):].lstrip()
    return rest == "" or rest[0] in DONE_TAIL
# 후보 두 절의 머리. `## 다음 계획 후보` 와 `## 다음 계획 후보 (테스트 phase 갭 …)`.
CANDIDATE_HEAD = "## 다음 계획 후보"
# 후보 두 절의 **머리 개수**. 못이 여기 서 있는 이유는 이 모집단만 회전에 안 흔들려서다
# (계획 72 설계 탐침: 회전 전후 둘 다 **2**). 옛 못은 포인터 수(9)에 붙어 있었는데
# **포인터 10개가 10개 다 취소선**이라 닫힌 후보를 지우는 회전이 그것을 **0** 으로
# 만들었다 — 등재돼 있던 처방 「하한을 실측치에 붙인다」가 거기서 반증됐다.
# `assertGreaterEqual` 이라 후보 절이 셋으로 늘어도 안 막고, 하나라도 이름이 갈리면
# 문다(설계 탐침: 어느 쪽 머리를 드리프트시켜도 2 → 1). 실물 문서와 이 상수를 잇는
# 자는 아래 못 하나뿐이다 — 합성 갈래 넷은 문서 드리프트에 전부 조용했다.
CANDIDATE_HEAD_FLOOR = 2

# 마감이 `index.md` 완료 행에 적는 **착수 관용구**. 「탐색 N순위」와 후보 절 이름을
# **둘 다** 요구하는 것이 이 자의 전부다 — 제목 인용만으로 뽑으면 후보를 집어간 행과
# 방법론으로 인용한 행이 **같은 꼴**이라 오탐이 60% 다(2026-09-29 반복 667 실측: 제목이
# 취소선 없이 살아 있는 5건 중 셋이 `index-step-sync`·`head-anchor-cover`·
# `spec-citation-anchor` 의 방법론 인용이었다). 오탐 셋을 실제로 거르는 것은 `PICK`
# 쪽이다 — 완료 91행 중 `PICK` 단독이 이미 6행이고 `START` 가 더 거르는 행은 **오늘 0**
# 이다(반복 670 재실측: 앞서 적었던 「26행이 6행으로」는 틀린 수였다). 그래도 `START` 를
# 함께 요구하는 것은 **인용과 착수를 가르는 술어**라서다 — 「다음 계획 후보 [N]「제목」」
# 이라는 꼴 자체는 방법론 인용도 쓸 수 있고, 그때 걸러낼 것이 이쪽뿐이다.
OPENED_START = re.compile(r"탐색\s*\*{0,2}\d+순위")
# **점수 `[N]` 은 선택이다** — 필수로 두면 점수를 안 적은 완료 행이 `opened_candidates`
# 에서 **조용히 빠지고**(2026-10-11 실측: 29행 중 추출 6 · 대조 3), 그 중 하나가 실물
# 갭을 들고 있었다(`plan_hidden-passage` 가 2026-09-02 등재 뒤 계획 51 이 닫았는데도
# 취소선 없이 살아 있었다). 완화의 오탐을 먼저 쟀다 — 추출 6→8 · 대조 3→4 · 새로 들어온
# 자리는 그 하나뿐이고 **거짓 양성 0건**이다(제목이 산문과 겹쳐 엉뚱한 줄을 무는 축은
# 완화판에서도 안 들어온다). 「인용과 착수를 가르는」 몫은 위 `OPENED_START` 로 **일부만**
# 넘어간다 — 순위 관용구가 **없는** 인용은 그쪽이 거르지만, 순위 관용구를 **함께 단**
# 인용 행은 완화 전후 모두 그냥 뽑힌다(2026-10-12 실측: `탐색 6순위` + `` `[7]`「예시
# 제목」 꼴로 적는다 `` 를 심으니 「예시 제목」이 추출된다). 실물에 그 꼴은 **0행**이고
# 점수를 선택으로 만든 것이 이 축을 넓히지도 않았다(조임판도 똑같이 뽑는다).
OPENED_PICK = re.compile(r"다음 계획 후보`?\s*(?:의|에서)?\s*"
                         r"(?:`?\[(?:\d+|high|medium)\]`?\s*)?「([^」]+)」")
# `digest` 취소선 줄이 다는 **마감 관용구**. `STRIKE_POINTER` 가 *열린* 줄에 요구하던
# 「를 열었다」는 실물이 0으로 말랐지만(계획 111 의 근거) 이쪽은 **취소선 5줄 5/5** 가
# 이미 단다. 「계획 N」과 「짧은 경로」를 둘 다 받는 이유는 실측이 3 대 2 라서고,
# 백틱을 안 넘게 막은 것은 본문의 다른 백틱 낱말을 슬러그로 읽지 않으려는 것이다.
CLOSED_POINTER = re.compile(r"닫혔다[^`\n]{0,40}`([A-Za-z0-9_-]+)`")
# 같은 계획 행을 **두 등재 꼴**로 찾는다 — 짧은 경로는 `| plan_<슬러그> |` 와
# `| (짧은 경로) <슬러그> |` 가 섞여 산다(실측: `interval-call-site` 는 앞,
# `verdict-head` 는 뒤). `PLAN_ROW` 만 쓰면 뒤엣것이 「등재에 없다」로 거짓 RED 다.
ANY_PLAN_ROW = r"^\| (?:plan_|\(짧은 경로\) )%s \| ([^|]*) \|"
# 두 자의 **가시 표본 하한**. 이 계획이 열린 이유 자체가 계획 61 의 `strike_gap` 이
# 표본 0으로 조용해진 것이라(후보 75줄 중 관용구 0), 같은 실명이 오면 빨개져야 한다.
# **못은 「대조에 도달한 쌍」에 박는다** — 착수 관용구를 쓴 완료 행은 6이지만 그 제목이
# digest 후보 절에 아직 남아 있는 것은 3뿐이고(반복 670 실측), `index.md` 완료 행은
# append-only 라 **영원히 안 줄어든다.** 거기 못을 박으면 회전이 후보를 다 지워 대조가
# 0이 돼도 이 자가 조용하다 — 계획 61 이 죽은 것과 똑같은 죽음이다. 실측 3 에 한 칸
# 여유를 두고 2 에 박는다. 마감 쪽은 취소선 줄이 곧 대조 대상이라 모집단이 하나다(실측 6).
OPENED_FLOOR = 2
CLOSED_FLOOR = 3

# 같은 계획 행의 **다섯째 칸(e2e)**. `STEP_ROW` 는 넷째, `PLAN_ROW` 는 둘째를 보고
# 이것은 다섯째를 본다. 슬러그로 집지 않고 **행 전부를 훑는다** — 재는 대상이
# 「지금 진행 중인 계획」이 아니라 「이미 닫힌 47행의 부기」라서다.
# 무는 것: (슬러그, 상태 칸, e2e 칸).
VERDICT_ROW = re.compile(
    r"^\| plan_([A-Za-z0-9_-]+) \| ([^|]*) \| [^|]* \| [^|]* \| ([^|]*) \|", re.M)
# 위 정규식이 다섯째 칸까지 못 읽은 행을 세려고 머리만 따로 문다. 열이 줄면
# `VERDICT_ROW` 는 그 행을 **조용히 건너뛴다** — 침묵 대신 신고하게 만드는 자리다.
VERDICT_ROW_HEAD = re.compile(r"^\| plan_", re.M)
# 표 머리 한 줄. `VERDICT_ROW` 는 **다섯째 칸이 e2e 라는 자리 약속** 위에 서 있고,
# 위 행 수 대조가 잡는 것은 열이 **줄어든** 쪽뿐이었다 — e2e **앞에** 열을 끼우면
# 개수가 맞아 통과하고 엉뚱한 칸을 판정으로 읽어 **틀린 RED** 를 냈다(2026-09-07
# 계획 71 리뷰 실측). 자리 대신 **이름**을 확인해 그 축을 닫는다.
VERDICT_HEAD = re.compile(r"^\| *계획 *\|.*$", re.M)
# e2e 칸이 판정이 아니라 **날짜뿐**인 꼴. 어휘(`통과`)를 요구하지 않는 것이 설계다 —
# 2026-09-07 실측에서 `통과` 를 요구하면 `없음(…)`·`**새 e2e 0개**(…)` 여섯 행이
# 거짓 RED 였다(계획서 2절). 자는 날짜 하나만 거절한다.
VERDICT_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
# 오늘 실물의 계획 행은 **48**이다. 추출기가 0행을 내면 판정이 조용한 초록이 되므로
# 하한을 못으로 박는다(계획 70 이 후보 포인터에서 밟고 계획 72 가 절 머리로 옮긴 자리).
# 행은 늘기만
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


def iter_gap(status_text, metrics_text, history_text):
    """반복 축이 어긋난 자리를 한 줄로 돌려준다. 어긋남이 없으면 `None`.

    **증인이 셋인 이유**: `status`·`metrics` 둘만 대조하면 **나란히 틀린 것**을 못
    잡는다 — 2026-09-09 실물에서 `loop/backoff-429` 가 494 이전 지점에서 갈라져 두
    숫자를 함께 싣고 494 마감 뒤에 병합됐고, 둘 다 490 인 채로 전수 719건이 초록이었다.
    셋째는 **최댓값**이지 마지막 항목이 아니다 — 그날 마지막 항목은 490 이고 최댓값이
    494 였다. 병합 순서가 파일 순서를 뒤집는 한 붙들 수 있는 것은 최댓값뿐이다.

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
    heads = HIST_ITER.findall(history_text)
    if not heads:
        return "history_current.md 에서 `### 반복 <수>` 머리를 못 찾았다"
    top = max(int(n) for n in heads)
    if top != int(b.group(1)):
        return ("반복 번호가 어긋났다 — history_current.md 최대 %d ≠ status.md"
                " `iteration` %s" % (top, b.group(1)))
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



def live_gap(status_text, index_text):
    """`진행` 인 채로 남겨진 계획을 한 줄로 돌려준다. 남은 것이 없으면 `None`.

    **자매 여덟 벌이 전부 `status.plan` 이 가리키는 행만 본다.** `step_gap` 은 그
    행의 스텝 칸을 대조하고 `archive_gap` 은 `완료` 만 아카이브를 요구하니, 계획이
    스텝을 남기고 버려지면 **그 행은 아무의 시야에도 없다** — 2026-09-09 실물에서
    `iter-third-witness` 가 네 계획 동안 그렇게 남았고 전수 737건이 초록이었다.

    **산문을 안 읽는다.** 「`status.md` 본문이 `plan:` 슬러그를 부르는가」로 잡는 안도
    같은 실물을 물었겠지만, 산문 매칭은 거짓 RED 의 원천이고(`verdict_gap` 이 어휘
    `통과` 를 요구하지 않기로 한 것과 같은 이유) 버려졌다는 사실은 **표의 칸에 이미
    적혀 있다.**

    `진행` 이 0개인 것은 안 문다 — 계획 마감 직후와 `plan: null` 이 정당하게 그렇고,
    등재가 빠진 쪽은 `step_gap` 이 「행을 못 읽었다」로 이미 문다.
    **열이 줄어 이 정규식이 행을 통째로 건너뛰는 쪽**도 여기 눈먼 자리가 아니다 —
    `verdict_gap` 이 행 머리 수와 파싱된 수를 대조해 그 모양을 신고한다.
    """
    p = PLAN_SLUG.search(status_text)
    if p is None:
        return "status.md 에서 `plan: <슬러그>` 줄을 못 찾았다"
    left = [slug for slug, state in LIVE_ROW.findall(index_text)
            if state.strip() == LIVE_MARK and slug != p.group(1)]
    if left:
        return ("index.md 에 `진행` 인 채로 남겨진 계획이 있다 — %s (지금 도는 것은"
                " `%s` 다). 마쳤으면 `완료`, 버렸으면 사유와 함께 `보류` 로 적는다"
                % (" · ".join(left), p.group(1)))
    return None

# **frontmatter 의 `signal:` 이 쓸 수 있는 낱말 넷** — 하네스 `SKILL.md` 2절 신호등 표다.
# 어휘가 저장소 **밖**에 정의되고 사본이 여기 사는 구조라 **다섯째 신호가 생기는 날**
# **거짓 RED 다.** 피할 길이 없다 — `REPORT_SIGNAL` 의 이모지 넷이 이미 같은 천장 위에
# 살고, 저장소가 그 꼴을 받아들였다. 완화는 **메시지로만** 한다(넷을 전부 인쇄한다).
KNOWN_SIGNALS = ("GREEN", "YELLOW", "RED", "DONE")
# **게이트가 쓰는 리터럴 접두 그대로다** — `grep -q '^signal: GREEN'`. 공백이 하나가
# 아니면(`signal:GREEN`·`signal:  GREEN`·탭) **게이트는 그 줄을 못 읽는다**(실측).
# 그래서 이 꼴 판정이 어휘 판정보다 먼저 온다 — 꼴이 틀리면 값이 맞아도 무의미하다.
SIGNAL_PREFIX = "signal: "
FENCE = "---"


def signal_gap(status_text):
    """`signal:` 이 게이트가 읽을 수 있는 꼴로 **하나만** 있고 값이 아는 넷인지 본다.

    **이 값은 2026-10-26 부터 하중을 받는다.** 자동 루프의 병합 게이트가
    `~/.local/bin/o-search-autoloop.sh` 에서 이 줄을 읽어 병합 여부를 가른다(게이트 ⑲ ㉠).
    그 전까지는 **아무도 안 보는 값**이었고, 그래서 저장소에 읽는 자가 0개인 채로 하중을
    받게 됐다 — 틀린 밤에도 전수는 초록이고 게이트는 **조용히 영구히 병합을 안 한다.**
    그 침묵의 유일한 기록은 저장소 밖 로그다(게이트 ⑲ⓑ).

    **게이트의 «조건» 은 복사하지 않는다.** 「DONE 이거나 GREEN+`plan: null` 이면 병합」을
    여기 적으면 저장소 밖 로직의 사본이 되고, 사람이 스크립트를 고치는 날 **거짓말하는**
    **가드**가 된다(`digest` 후보의 「측정기가 규칙을 복사하는 사고」). 무는 것은 **그 줄을**
    **게이트가 읽을 수 있나**와 **값이 넷 중 하나인가** 둘뿐이다. 그래서 `signal: GREEN` 인데
    실제로 빨간 밤은 이 자가 못 잡는다 — 그쪽은 게이트가 병합 전에 전수를 직접 돌려 막는다.

    **세 가지를 순서대로 본다. 순서가 곧 「재지 못했다」와 「빨강」의 구별이다.**

    1. **울타리** — 여는 `---` 과 닫는 `---` 이 둘 다 있고 그 사이에 **빈 줄이 없어야** 한다.
       셋 다 2026-10-26 리뷰·테스트 phase 가 **실물로 찍은 구멍**이고 전부 같은 계열(「조용한
       초록」)이다: 울타리 전무 → 전문이 head · 여는 것만 있음 → 같은 구멍의 둘째 입구 ·
       `---\n---`(빈 frontmatter) → `fenced` 와 `head` 의 오프셋 비대칭이 만든 **세 번째 입구**
       · 닫는 울타리를 잃은 문서에서 **본문의 수평선**이 그 역할을 하는 네 번째. 빈 줄을
       금한 것이 마지막을 가른다 — frontmatter 는 `key: value` 만 쌓이고 실물이 그렇다.
    2. **유일성과 자리** — `^signal:` 로 시작하는 줄이 **파일 전체에 정확히 하나**고 그것이
       frontmatter **안**이어야 한다. 가드는 frontmatter 만 보는데 **게이트는 전문을 grep**
       **한다**([R123-6]) — 본문에 백틱 없이 줄 머리로 `signal: DONE` 이 들어오면 가드는
       조용하고 게이트는 **보류 브랜치를 병합한다.** 그 비대칭을 여기서 닫는다.
    3. **꼴과 값** — 접두가 `signal: `(공백 **정확히 하나**)여야 하고, 꼬리 공백과 `#` 주석을
       떼고 남은 것이 넷 중 하나여야 한다. 꼬리·주석을 봐 주는 것은 게이트가 **접두로**
       읽기 때문이고(`grep` 에 꼬리 앵커가 없다) 이 문서의 다른 frontmatter 줄들이 `#`
       주석을 일상으로 달기 때문이다(`plan:`·`mode:`).
    """
    lines = status_text.split("\n")
    if not lines or lines[0] != FENCE:
        return ("status.md 가 여는 `---` 으로 시작하지 않는다 — frontmatter 경계를 그을 수"
                " 없어 **재지 못했다**. 산문은 안 읽는다: 본문의 `signal:` 인용 한 줄이"
                " 판정을 가져가는 것이 이 자가 막는 사고다")
    try:
        close = lines.index(FENCE, 1)
    except ValueError:
        return ("status.md frontmatter 에 닫는 `---` 이 없다 — 경계를 그을 수 없어 **재지"
                " 못했다**. 본문의 수평선을 울타리로 읽으면 산문이 head 에 들어온다")
    front = lines[1:close]
    if "" in front:
        return ("status.md frontmatter 안에 빈 줄이 있다 — 닫는 `---` 이 진짜 울타리인지"
                " 본문의 수평선인지 가를 수 없어 **재지 못했다**. frontmatter 는"
                " `key: value` 줄만 쌓는다")
    everywhere = [l for l in lines if l.startswith("signal:")]
    inside = [l for l in front if l.startswith("signal:")]
    if not inside:
        return ("status.md frontmatter 에서 `signal: <값>` 줄을 못 찾았다 — 여는 `---` 과"
                " 닫는 `---` **사이**에 있어야 한다. 자동 루프의 병합 게이트가 바로 이"
                " 줄을 읽으므로 없으면 그 게이트는 병합을 영구히 안 한다"
                " (`~/.local/bin/o-search-autoloop.sh` · 게이트 ⑲ ㉠)")
    if len(everywhere) != 1:
        return ("status.md 에 `signal:` 로 시작하는 줄이 %d 개다 — **정확히 하나**여야 한다."
                " 가드는 frontmatter 만 보지만 **게이트는 `grep` 으로 전문을 본다** —"
                " 본문에 줄 머리로 하나가 더 서면 게이트가 그것을 읽어 **보류 브랜치를"
                " 병합할 수 있다**. 인용은 백틱 안에 두거나 들여쓴다: %s"
                % (len(everywhere), " · ".join("`%s`" % l[:40] for l in everywhere)))
    line = inside[0]
    if not line.startswith(SIGNAL_PREFIX):
        return ("status.md 의 `signal:` 줄이 게이트가 읽을 수 없는 꼴이다 — `%s`."
                " 게이트는 리터럴 접두 `grep -q '^signal: GREEN'` 으로 읽으므로 콜론 뒤"
                " 공백이 **정확히 하나**여야 한다(`signal:GREEN`·`signal:  GREEN`·탭은"
                " 전부 못 읽는다 — 실측). 값이 맞아도 게이트는 병합을 영구히 안 한다"
                % line[:40])
    value = line[len(SIGNAL_PREFIX):].split("#", 1)[0].rstrip()
    if value in KNOWN_SIGNALS:
        return None
    return ("status.md frontmatter 의 `signal:` 이 아는 낱말이 아니다 — 읽은 것은 `%s`"
            " 다. 쓸 수 있는 것은 **GREEN · YELLOW · RED · DONE** 넷뿐이다(하네스"
            " `SKILL.md` 2절). 이 값을 자동 루프의 병합 게이트가 읽어 병합 여부를"
            " 가르므로(`~/.local/bin/o-search-autoloop.sh` · 게이트 ⑲ ㉠), 모르는"
            " 낱말이면 게이트는 **조용히 영구히 병합을 안 하고** 그 침묵은 저장소 밖"
            " 로그에만 남는다" % value)


def candidate_heads(digest_text):
    """후보 절의 머리 줄. `candidate_pointers` 의 절 자르기와 **같은 술어**를 쓴다."""
    return [l for l in digest_text.split("\n") if l.startswith(CANDIDATE_HEAD)]


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
        if not is_done(row.group(1)):
            continue  # 진행 중인 계획을 가리키는 줄은 아직 열려 있는 것이 맞다.
        if not struck:
            return ("닫힌 후보에 취소선이 없다 — index.md `plan_%s` 는 `완료` 인데"
                    " digest 후보 줄이 `- ~~` 로 시작하지 않는다" % slug)
    return None


def candidate_lines(digest_text):
    """후보 절의 목록 줄. `candidate_pointers` 의 절 자르기와 **같은 술어**를 쓴다."""
    out, in_section = [], False
    for line in digest_text.split("\n"):
        if line.startswith("## "):
            in_section = line.startswith(CANDIDATE_HEAD)
            continue
        if in_section and line.startswith("- "):
            out.append(line)
    return out


def opened_candidates(index_text):
    """완료 행이 **착수 관용구**로 가리킨 `(슬러그, 후보 제목)`.

    「탐색 N순위」와 후보 절 이름을 **둘 다** 품은 행만 센다 — 한쪽만 보면 방법론
    인용이 섞인다(`OPENED_START` 주석의 실측). 관용구를 안 쓴 완료 행 85개는 뿌리가
    없어 여기서 **조용히 빠진다**: 서식을 강제하는 것은 계획 111 이 뺀 축이다.

    **모집단은 접두 둘이다** — `| plan_` 과 `| (짧은 경로) `. 위 `ANY_PLAN_ROW` 가
    같은 이유로 이미 둘을 받는데 여기만 앞엣것으로 좁아, 짧은 경로가 집은 후보는
    관용구를 ① 꼴로 맞춰 적어도 **구조적으로** 안 읽혔다(2026-10-15 반복 709 실측:
    착수 관용구를 단 짧은 경로 행 5 · 추출 0 · 그중 하나가 그날 닫은 자리였다).
    """
    out = []
    for line in index_text.split("\n"):
        cells = line.split("|")
        if len(cells) < 3 or not (line.startswith("| plan_")
                                  or line.startswith("| (짧은 경로) ")):
            continue
        if not is_done(cells[2]) or not OPENED_START.search(line):
            continue
        title = OPENED_PICK.search(line)
        if title is not None:
            out.append((cells[1].strip(), title.group(1)))
    return out


def closed_pointers(digest_text):
    """취소선 줄이 **마감 관용구**로 가리킨 `(슬러그, 줄)`."""
    out = []
    for line in candidate_lines(digest_text):
        if not line.startswith("- ~~"):
            continue
        hit = CLOSED_POINTER.search(line)
        if hit is not None:
            out.append((hit.group(1), line))
    return out


def open_gap(digest_text, index_text):
    """집어간 후보가 취소선 없이 살아 있는 자리를 한 줄로. 없으면 `None`.

    **`strike_gap` 과 방향이 반대다** — 저쪽은 후보 줄의 포인터에서 계획으로 가고
    이쪽은 완료 행의 착수 관용구에서 후보 줄로 온다. 잡는 사고도 다르다: 저쪽은
    거짓 취소선, 이쪽은 **긋는 것을 잊은 자리**다. 실물은 `OpenSyncTest` 가,
    갈래는 `OpenGapTest` 가 부른다.
    """
    lines = candidate_lines(digest_text)
    # 후보 절에 제목이 안 남은 자리는 뺀다 — 삭제인지 표기 차이인지 못 가른다.
    # 남은 것이 **이 자가 실제로 대조하는 전부**라, 하한도 여기에 박는다.
    compared = [(slug, title, [l for l in lines if title in l])
                for slug, title in opened_candidates(index_text)]
    compared = [(slug, title, hit[0]) for slug, title, hit in compared if hit]
    if len(compared) < OPENED_FLOOR:
        return ("완료 행의 후보 제목 중 digest 후보 절에 남아 대조된 것이 %d 자리뿐이다"
                " — 하한 %d. 이 자가 표본 0으로 조용해지는 것이 계획 111 의 근거였다"
                % (len(compared), OPENED_FLOOR))
    for slug, title, line in compared:
        if not line.startswith("- ~~"):
            return ("집어간 후보에 취소선이 없다 — index.md `%s` 는 `완료` 인데 digest"
                    " 후보 줄 「%s」 가 `- ~~` 로 시작하지 않는다" % (slug, title))
    return None


def false_strike(digest_text, index_text):
    """취소선 줄이 **안 닫힌 계획**을 가리키는 자리를 한 줄로. 없으면 `None`.

    실물은 `FalseStrikeSyncTest` 가, 갈래는 `FalseStrikeGapTest` 가 부른다.
    """
    closed = closed_pointers(digest_text)
    if len(closed) < CLOSED_FLOOR:
        return ("마감 관용구를 단 취소선 줄이 %d 개뿐이다 — 하한 %d. 취소선을 그으면서"
                " 닫은 계획을 안 적으면 이 자가 표본 0으로 조용해진다"
                % (len(closed), CLOSED_FLOOR))
    for slug, line in closed:
        row = re.search(ANY_PLAN_ROW % re.escape(slug), index_text, re.M)
        if row is None:
            return ("취소선 줄이 등재에 없는 계획을 가리킨다 — `%s` (%s…)"
                    % (slug, line[:40]))
        if not is_done(row.group(1)):
            return ("거짓 취소선 — index.md `%s` 의 상태는 `%s` 인데 digest 후보 줄은"
                    " 이미 `- ~~` 다" % (slug, row.group(1).strip()))
    return None


def verdict_gap(index_text):
    """완료 행의 e2e 칸이 판정이 아닌 자리를 한 줄로 돌려준다. 없으면 `None`.

    **몸통을 함수로 뺀 이유는 `step_gap`·`iter_gap`·`strike_gap` 과 같다** — 실물
    `index.md` 는 고치고 나면 늘 맞아서, 검사가 문서에만 붙어 있으면 판정을 무력화하는
    변이가 조용히 산다(계획 60 실측 6/6 생존 · 계획 61 실측 4/4 생존). 실물은
    `VerdictSyncTest` 가, 갈래는 `VerdictGapTest` 가 부른다.

    **`완료` 행만 본다** — 진행 중인 계획의 e2e 칸은 아직 `—` 인 것이 맞다.
    """
    head = VERDICT_HEAD.search(index_text)
    names = [c.strip() for c in head.group(0).strip("| \n").split("|")] if head else []
    if len(names) < 5 or names[4] != "e2e":
        return ("index.md 표 머리의 다섯째 칸이 `e2e` 가 아니다 — 읽힌 머리는 %r 다."
                " 이 자는 다섯째를 판정으로 읽으므로 자리가 밀리면 엉뚱한 칸을 문다"
                % (names,))
    rows = VERDICT_ROW.findall(index_text)
    heads = VERDICT_ROW_HEAD.findall(index_text)
    if len(rows) != len(heads):
        return ("index.md 의 계획 행 %d개 중 %d개만 다섯째 칸까지 읽혔다 — 열이"
                " 줄었거나 행 표기가 관례를 벗어났다(칸 구분은 공백 한 칸이다)"
                % (len(heads), len(rows)))
    for slug, status, verdict in rows:
        if not is_done(status):
            continue
        cell = verdict.strip()
        if VERDICT_DATE.fullmatch(cell):
            return ("e2e 칸에 판정이 아니라 날짜가 있다 — index.md `plan_%s` 의 다섯째"
                    " 칸이 `%s` 다. 판정은 docs/e2e/<슬러그>/result.md 에 있다"
                    % (slug, cell))
    return None


def archive_gap(index_text, live_names):
    """`완료` 인데 계획서가 아직 `docs/` 에 살아 있는 자리. 없으면 `None`.

    **몸통을 함수로 뺀 이유는 `step_gap`·`strike_gap`·`verdict_gap` 과 같다** — 실물은
    치우고 나면 맞아서, 검사가 문서에만 붙어 있으면 판정을 무력화하는 변이가 조용히 산다.
    실물은 `ArchiveBacklogTest` 가, 갈래는 `ArchiveGapTest` 가 부른다.

    **`docs.md` 4절이 오늘까지 재는 자가 0개였다.** 계획을 마치면 `plan_<slug>.md` 를
    `plan_history_<NNN>.md` 로 옮기라고 적혀 있는데 강제하는 것이 없어 **두 번 미끄러졌다**
    (2026-09-09 실측: 계획 80 의 `design_recrawl` · 계획 81 의 `plan_ethics-floor`).
    값은 다음 반복이 문다 — 루프는 「활성 계획은 동시에 1개」를 `docs/plan_*.md` 로 세고
    (`discover.md` 5절), 치우지 않은 완료본이 그 셈에 그대로 낀다.

    **`완료` 행만 본다** — `보류(패치)` 는 승인에 막혀 멈춘 것이라 제자리가 맞다.
    중복 방지가 `docs/plan_*.md` 중 보류인 것을 읽으므로 치우면 그 눈이 멀어진다.
    """
    for slug, status, _ in VERDICT_ROW.findall(index_text):
        # **동일성이 아니라 접두다.** 리터럴 `!= "완료"` 로 보던 자는 2026-10-26 에 사람이
        # 게이트 ⑱ 을 ㉢ 으로 닫으며 처음 쓴 `완료(2026-10-26 … 해제 · 병합)` 꼴에서
        # **조용했다** — 그 꼴 2건에서 완료 계획서 둘이 살아 있는데 전수가 초록이었다
        # (실측 2026-10-27 반복 761). 자가 틀린 날이 아니라 **문서의 어휘가 자보다
        # 넓어진 날**이라, 넓히는 쪽이 뿌리다(`index.md` 를 자에 맞춰 깎는 쪽이 아니다).
        #
        # **굵게를 먼저 벗긴다** — 살아 있는 `index.md` 상태 칸에 `**보류**` 가 실재하므로
        # `**완료**` 는 내일 쓰일 수 있는 꼴이다. 「값을 굵게 감싸니 재는 자가 죽었다」는
        # 이 저장소가 계획 122 리뷰에서 이미 한 번 밟았다(`signal_row_gap`).
        #
        # **포함이 아니라 접두인 것이 오탐을 막는다** — `in` 으로 넓히면
        # `보류(2026-10-23 · 승인 나면 완료 처리)` 같은 산문 한 줄이 승인 대기 계획서를
        # 치우라고 요구하고, 그러면 중복 방지(`discover.md` 5절)의 눈이 먼다.
        if not is_done(status):
            continue
        # **계획서와 설계 문서를 둘 다 본다.** 설계 축은 2026-10-27 까지 **재는 자가 0개**
        # 였다 — 4절이 같은 숨에 요구하는데 자는 `plan_` 접두만 봤고,
        # `design_history_095.md` 가 계획서(2026-10-20 아카이브)보다 이레를
        # 더 살아 있었다. `digest ## 반복 실패` 의 「절차를 문서에만 적고 재는 자를 안
        # 만든다」가 센 2회 중 **한 번이 설계 문서**였다(계획 80 `design_recrawl`).
        #
        # **없으면 조용한 것이 설계다** — 4절이 「설계를 건너뛰면 없다」를 명시하고
        # 실물에서 설계 없는 완료 계획이 다수다. `in live_names` 가 그 음성 대조를
        # 공짜로 준다(존재하는 것만 모집단에 든다).
        for kind in ("plan", "design"):
            name = "%s_%s.md" % (kind, slug)
            archive = "%s_history_<NNN>.md" % kind
            if name in live_names:
                return ("완료한 %s 문서가 안 치워졌다 — index.md `plan_%s` 는 `완료` 인데"
                        " docs/%s 가 살아 있다. `%s` 로 옮긴다 (docs.md 4절 ·"
                        " 번호는 계획서와 같은 `NNN` 을 쓴다)"
                        % (kind, slug, name, archive))
    return None


# `docs/project.md` 가 인용한 코드 상수. **`= 숫자` 가 붙은 인용만 문다** —
# `` `design_check.PAIRS` `` 처럼 값을 안 적은 인용까지 물면 문서가 상수를 못 부른다.
# 백틱과 `=` 사이에 줄바꿈·들여쓰기·굵게(`**= 35,000자**`)가 낀 꼴이 실물이라 함께 받는다.
# 사이는 공백만 건널 수 있다 — **빈 줄도 공백이라** 인용 바로 뒤 문단이 `= 숫자` 로
# 시작하면 거기까지 간다(실측). 산문에 그 꼴이 없어 실물은 안 새고, 새더라도 값이
# 어긋나 **시끄럽게 빨개지지** 조용히 통과하지는 않는다.
# ponytail: 괄호 표기(`fetcher.MAX_BYTES`(2MB))는 안 문다. 그 꼴이 늘면 그때 넓힌다.
CONST_CITATION = re.compile(
    r"`([a-z_]+)\.([A-Z][A-Z0-9_]+)`\s*(?:\*\*\s*)?=\s*(\d[\d,_]*\d|\d)")
# 상수가 사는 두 곳. 여기 없는 모듈을 인용하면 그 자체가 낡음이다.
CONST_DIRS = (DOCS.parent / "src" / "websearch", DOCS.parent / "e2e")

# `project.md` 가 **값까지 적어** 부르는 상수의 최소 개수. 오늘 실물은 **2**다
# (`indexer.MAX_PASSAGE_TAGS`·`MAX_PASSAGE_HTML`). 못을 박는 이유는 `const_gap` 이
# **인용 0건이면 조용한 초록**이기 때문이다 — 캡 문단을 다시 쓰면서 `= 숫자` 꼴을
# 안 쓰면 검사가 아무것도 안 재면서 통과한다. 그것이 이 검사가 거짓말을 하는 유일한
# 길이고, 계획 70·72 가 후보 포인터에서 이미 두 번 밟은 실패 유형이다.
# **값 축에 딱 붙이지 않았다** — 2 로 박으면 문단이 상수 하나만 부르도록 정당하게
# 줄어드는 날 거짓 RED 다(`VERDICT_ROW_FLOOR` 이 45 인 것과 같은 이유). 1 은
# 「아무것도 안 잰다」만 문다.
CONST_CITATION_FLOOR = 1


def _const_value(module, name):
    """코드에서 상수의 정수 리터럴을 읽어 `(값, 사유)` 로 돌려준다.

    **임포트가 아니라 소스를 읽는다** — 인용 대상은 `e2e/` 에도 살 수 있고 그쪽은
    임포트에 부작용이 있다. 문서가 인용하는 것은 대입문의 리터럴 그 자체이기도 하다.
    ponytail: 정수 리터럴만 읽는다. 식으로 바뀌면 「못 읽었다」로 보고한다 —
    조용히 통과시키는 것보다 낫다.
    """
    for base in CONST_DIRS:
        path = base / (module + ".py")
        if not path.exists():
            continue
        found = re.search(r"^%s\s*=\s*(\d[\d_]*)\b" % re.escape(name),
                          path.read_text(encoding="utf-8"), re.M)
        if found is None:
            return None, "`%s.py` 에 `%s = <정수>` 가 없다" % (module, name)
        return int(found.group(1).replace("_", "")), None
    return None, "`%s.py` 를 src/websearch 에서도 e2e 에서도 못 찾았다" % module


def const_gap(text, doc="project.md"):
    """문서가 인용한 상수가 코드와 어긋난 자리를 한 줄로 돌려준다. 없으면 `None`.

    `doc` 은 **메시지에 쓸 파일 이름**뿐이다 — 무는 파일이 둘이 된 뒤로(계획 97 이
    캡 설계 논증을 `baselines.md` 로 옮겼다) 「project.md 가」로 단정하면 틀린 자리를 가리킨다.

    **몸통을 함수로 뺀 이유는 `step_gap`·`iter_gap`·`verdict_gap` 과 같다** — 실물은
    `ProjectConstTest` 가, 갈래는 `ConstGapTest` 가 부른다.

    재는 것은 **상수 값 하나**다. 문단이 그 값에서 유도한 숫자(최악 ms·계수·p95)는
    코드에 없어서 못 잰다 — 상수가 닻이고, 닻이 움직이면 사람이 그 문단을 다시 읽는다.
    """
    for module, name, cited in CONST_CITATION.findall(text):
        value, why = _const_value(module, name)
        if why is not None:
            return "%s 가 `%s.%s` 를 인용하는데 %s" % (doc, module, name, why)
        want = int(cited.replace(",", "").replace("_", ""))
        if want != value:
            return ("%s 가 `%s.%s` 를 %s 라고 적었는데 코드는 %d 다 —"
                    " 그 값에서 유도한 숫자도 함께 낡았는지 문단을 다시 읽는다"
                    % (doc, module, name, cited, value))
    return None


E2E_DIR = DOCS.parent / "e2e"
# 문서 안에서 **낱말 하나로** 선 이름만 등재로 친다. 부분 문자열로 세면 안 된다 —
# 이 저장소에 실제 함정이 있다: `interrupt_e2e` 는 `indexer_interrupt_e2e` 의 부분
# 문자열이라, 뒤엣것만 적힌 문서가 앞엣것까지 등재한 것으로 읽힌다.
E2E_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# 「아무것도 안 잰다」를 닫는 하한. `e2e/` 가 비거나 경로가 어긋나면 `glob` 이 0개를
# 내고 `test_project_names_every_e2e` 는 조용한 초록이 된다.
# **다만 `CONST_CITATION_FLOOR` 과 값이 다르다 — 여기서는 못이 «유일한» 방벽이 아니다.**
# 아래 갈래 픽스처가 디스크에서 조립되므로 모집단이 비면 갈래가 **먼저** 죽는다
# (반복 572 변이 실측: `glob("*.pyx")`·`E2E_DIR` 이사 둘 다 갈래가 물었고, 못만 1→0 으로
# 내리는 변이는 **살았다**). 못이 하는 일은 원인을 이름으로 찍는 것이다.
# **오늘 값(22)에 안 붙인다** — e2e 를 정당하게 지우는 날 거짓 RED 이기 때문이다.
E2E_ROSTER_FLOOR = 1


def e2e_roster_gap(text, doc="project.md"):
    """문서가 이름으로 안 부르는 `e2e/*.py` 를 한 줄로 돌려준다. 없으면 `None`.

    **모집단은 디스크지 문서가 아니다.** 문서에서 출발해 「적힌 이름이 실재하나」를
    재는 자는 `test_readme.py` 가 이미 갖고 있고, 그 방향은 **빠뜨린 것을 구조적으로
    못 본다** — 실제로 못 봤다. 반복 570 실측에서 `e2e/*.py` 22개 중 **5개**가 어느
    문서에도 없었고 전수 763건이 그 상태로 전부 초록이었다.

    재는 것은 **이름이 있나**뿐이다. 그 e2e 가 실제로 도는지·누가 언제 돌리는지는
    안 잰다 — 그쪽은 러너의 몫이고 이 자는 명부가 낡는 것만 문다.

    **자리도 안 잰다** — 이름이 문서 어디에 낱말로 서 있기만 하면 등재로 친다.
    「안 돌리는 것들」 목록에 적어도 조용해진다. 자리를 재려면 명부 줄을 파싱해야
    하는데 그러면 줄 모양을 바꿀 때마다 거짓 RED 를 낸다 — 오늘 그 거래는 손해다.
    """
    named = set(E2E_WORD.findall(text))
    missing = sorted(p.stem for p in E2E_DIR.glob("*.py") if p.stem not in named)
    if missing:
        return ("%s 가 `e2e/` 의 %d개를 이름으로 안 부른다 — %s. 명부에 없는 e2e 는"
                " 아무도 안 돌린다(루프는 이 파일을 읽어 무엇을 칠지 정한다)"
                % (doc, len(missing), " · ".join("`%s`" % m for m in missing)))
    return None


# 명부 **항목**의 앵커. `- **e2e N종**:` 으로 시작해 다음 `- **` 항목 직전까지가 한 항목이다
# (실측 2026-09-13 반복 575: 4줄 · 다음 항목은 `측정`). `e2e_roster_gap` 이 문서 **전체**를
# 훑는 것과 달라서, 이쪽은 **자리를 잰다** — 유령이 태어난 자리가 바로 이 항목이다.
E2E_LABEL_ITEM = re.compile(r"^- \*\*e2e ([0-9]+)종\*\*:(.*?)(?=^- \*\*|\Z)", re.M | re.S)
# 항목 안의 백틱 토큰. 그중 **맨 식별자만** 이름으로 친다 — 실측에서 토큰 21개 중 18개가
# 맨 식별자이고 전부 `e2e/<이름>.py` 였다. 나머지 셋(`` `PYTHONPATH=… e2e/<이름>.py` ``·
# `` `test_docs.py` ``·`` `docs/baselines.md` ``)은 공백·점·슬래시가 있어 안 걸린다.
# **2026-09-13 반복 574 의 수정이 기댄 성질이 정확히 이것이다** — 유령 `E2eRosterTest` 를
# 파일명 `test_docs.py` 로 바꿔 닫았는데, 점이 든 토큰은 맨 식별자가 아니라서 통했다.
# 자가 다른 자를 쓰면 그 수정이 왜 통했는지를 아무도 안 재게 된다.
E2E_BACKTICK = re.compile(r"`([^`]+)`")


def e2e_label_gap(text, doc="project.md"):
    """명부 줄이 「기계가 읽는 줄」이기를 그친 자리를 한 줄로 돌려준다. 없으면 `None`.

    **방향이 `e2e_roster_gap` 과 반대다.** 그쪽은 **디스크에서 출발해** 문서가 안 부르는
    이름(빠진 것)을 보고, 이쪽은 **문서에서 출발해** 디스크에 없는 이름(유령)과 라벨
    드리프트를 본다. 하나로 합치면 한쪽 방향의 이빨이 조용히 빠진다 — 둘은 서로를
    대체하지 않는다(`db-state-invariant` 가 불변식과 값에서 배운 것과 같은 자리).

    **유령은 가설이 아니다.** 2026-09-13 계획 98 e2e 첫 판이 이 항목에서 이름을 **19개**
    뽑았고 열아홉째 `E2eRosterTest` 가 `rc=2`(그런 파일이 없다)로 죽었다 — 571 이 사람에게
    유익하라고 넣은 포인터였는데 **그 줄은 기계가 읽는 줄**이다. 574 는 문서를 고쳐 닫았고
    되돌아오는 것을 막는 자가 0개였다.

    **`glob` 개수와는 대조하지 않는다.** `digest.md` 가 적어 둔 처방은 「뽑은 이름 수 ==
    라벨 == `glob` 개수」였는데 실측은 **18 == 18 ≠ 22** 다 — `glob` 은 측정 넷
    (`perf_crawl`·`perf_search`·`quality_eval`·`passage_eval`)을 포함하고 그 넷은 같은
    문서의 `측정` 항목이 부르며 `e2e_roster_gap` 이 이미 문다. **등재된 처방은 근거지
    설계가 아니다** — 코드로 옮기기 전에 실물에 대봤고, 그래서 등식이 둘이다.

    **하한 못을 따로 안 박는다.** 추출이 통째로 죽어 이름이 0개가 되면 라벨(18)과
    안 맞아 **그 자리에서 빨개진다** — 「아무것도 안 잰다」가 조용한 초록이 되는 경로가
    없다. 못이 필요했던 `e2e_roster_gap` 쪽과 다른 것은 **모집단이 문서 안에 있어서**다.
    """
    m = E2E_LABEL_ITEM.search(text)
    if m is None:
        return ("%s 에서 `- **e2e N종**:` 항목을 못 찾았다 — 명부가 사라졌거나 줄 모양이"
                " 바뀌었다(루프도 e2e 러너도 이 항목을 읽어 무엇을 칠지 정한다)" % doc)
    names = [tok for tok in E2E_BACKTICK.findall(m.group(0)) if E2E_WORD.fullmatch(tok)]
    ghosts = [n for n in names if not (E2E_DIR / (n + ".py")).exists()]
    if ghosts:
        return ("%s 의 명부가 없는 파일을 %d개 부른다 — %s. 이 줄은 사람만 읽는 줄이"
                " 아니라 **기계가 읽는 줄**이라 유령 하나가 러너를 rc=2 로 죽인다"
                % (doc, len(ghosts), " · ".join("`%s`" % g for g in sorted(ghosts))))
    label = int(m.group(1))
    if label != len(names):
        return ("%s 의 라벨과 명부 길이가 어긋났다 — 「e2e %d종」인데 이름은 %d개다"
                % (doc, label, len(names)))
    return None


# `rules/docs.md` 3절의 `history_current.md` 상한. **여기 두 줄이 그 룰의 유일한
# 기계 표현이다** — 룰 파일은 저장소 밖(`~/.claude/skills/loop-harness/`)에 살아 검사가
# 읽을 수 없다. 룰이 바뀌면 이 둘을 손으로 맞춘다.
# **`digest.md` 200 은 일부러 안 잰다**(계획 76 「하지 않을 것」) — 그쪽 처방은 오래된
# 완료 항목 **삭제**라 무인 모드가 못 하고(`SKILL.md` 야간 금지 목록), 못을 박으면
# 야간이 스스로 못 푸는 RED 가 된다. history 쪽은 처방이 아카이브로 **밀어내기**라
# 야간이 실행할 수 있다 — 두 상한의 성질이 달라 한 못으로 묶지 않는다.
HISTORY_LINE_CAP = 300
HISTORY_ENTRY_CAP = 20
# 항목 머리. 회전으로 밀려난 옛 파일들은 `## 반복` 꼴도 쓰지만, **살아 있는 파일의
# 오늘 꼴은 `### 반복`** 이다. 문구가 드리프트하면 이 자가 0을 세고 조용해지므로
# `HistoryCapTest` 가 하한 못을 함께 박는다.
HISTORY_ENTRY_HEAD = re.compile(r"^### 반복 ", re.M)
# 항목 축이 «아무것도 안 재는 길»을 닫는 하한. **오늘 값(9)에 안 붙인다** —
# 회전 직후에는 항목이 몇 개든 정당하고, 값에 못을 박으면 정당한 날 거짓 RED 다
# (`CONST_CITATION_FLOOR` 이 2 가 아니라 1 인 것과 같은 이유).
HISTORY_ENTRY_FLOOR = 1


# `rules/docs.md` 1절이 «매 반복 읽는 넷»에 건 **총합** 상한. 파일별 상한의 합은
# 50+60+80+300 = **490** 이라 이 수보다 작다 — 룰이 남긴 110 줄의 여유가 의도고,
# 그래서 총합은 파일별의 파생이 아니라 **따로 물어야 하는 축**이다. 실제로 오늘
# `history_current.md` 300 축은(`HistoryCapTest` 가 무는 유일한 축) 안 넘겼는데
# 총합은 넘겼다.
READ_BUDGET_CAP = 600
# (파일명, 그 파일의 상한). 활성 계획은 슬러그가 매번 달라 여기 못 적고 아래서 붙인다.
READ_BUDGET_FILES = (("status.md", 50), ("project.md", 60), ("history_current.md", 300))
READ_BUDGET_PLAN_CAP = 80


def read_budget_gap(sizes):
    """필수 읽기 넷의 **합**이 상한을 넘었으면 한 줄로 돌려준다. 안 넘었으면 `None`.

    `sizes` 는 `(파일명, 실측 줄 수, 그 파일의 상한)` 의 순서열이다 — 재는 일과 판정을
    갈라 놔야 픽스처로 경계를 고정할 수 있다 (`cap_gap` 이 텍스트를 받는 것과 같다).

    **파일별 상한은 인쇄만 하고 안 문다.** 넘긴 파일이 있어도 합이 상한 안이면 조용하다.
    처방의 성질이 달라서다 — 합계는 중복 접기·회전이라 무인 루프가 실행할 수 있지만,
    개별 파일을 제 상한까지 줄이는 것은 「무엇을 남길지 사람이 고르기」다. 못을 박으면
    야간이 스스로 못 푸는 RED 가 된다(`digest.md` 200 을 일부러 안 재는 것과 같은 이유 —
    위 `HISTORY_LINE_CAP` 주석). 대신 **실패 메시지가 파일별 실측/상한을 전부 인쇄**한다.
    합계만 알려주면 사람이 어느 파일을 볼지 모른다.

    **경계는 초과가 아니다** — 룰 문구가 「넘으면」이라 정확히 600 인 날은 조용하다
    (`cap_gap` 과 같은 판단).
    """
    total = sum(n for _, n, _ in sizes)
    if total <= READ_BUDGET_CAP:
        return None
    detail = " · ".join("%s %d/%d" % (name, n, cap) for name, n, cap in sizes)
    return ("필수 읽기가 상한을 넘었다 — 합계 %d > %d (%s). 원본이"
            " `history_current.md`·`index.md`·`docs/e2e/*/result.md` 에 **있는 것을 확인한**"
            " 줄만 접는다 (`rules/docs.md` 1절)" % (total, READ_BUDGET_CAP, detail))


def read_budget_sizes(docs=DOCS):
    """살아 있는 문서에서 `read_budget_gap` 의 입력을 만든다.

    **활성 계획은 `status.md` 가 가리킬 때만 센다** — DONE 인 날은 읽을 계획이 없어
    넷이 아니라 셋이고, 다 읽은 계획서를 계속 세면 없는 비용을 무는 것이다.
    슬러그 추출은 `PLAN_SLUG` 를 그대로 쓴다. 그 정규식이 드리프트하면 계획이 조용히
    안 세어지지만 **그 자리는 `LivePlanSyncTest` 가 이미 물고 있다**(같은 상수로
    `index.md` 의 진행 행을 찾는다) — 여기 하한을 또 박지 않는 이유다.

    `docs` 를 인자로 받는 것은 **픽스처가 두 분기를 밟기 위해서다** — 살아 있는 트리는
    「계획이 있고 파일도 있다」 한 갈래뿐이라 나머지 둘이 아무도 안 밟는 채로 초록이 된다
    (실측: 변이 「파일 없어도 센다」·「아예 안 센다」가 둘 다 살았다).
    """
    sizes = [(name, len((docs / name).read_text(encoding="utf-8").splitlines()), cap)
             for name, cap in READ_BUDGET_FILES]
    slug = PLAN_SLUG.search((docs / "status.md").read_text(encoding="utf-8"))
    if slug:
        plan = docs / ("plan_%s.md" % slug.group(1))
        if plan.exists():
            sizes.append((plan.name,
                          len(plan.read_text(encoding="utf-8").splitlines()),
                          READ_BUDGET_PLAN_CAP))
    return sizes


def cap_gap(text):
    """`history_current.md` 가 상한을 넘은 축을 한 줄로 돌려준다. 안 넘었으면 `None`.

    **두 축을 함께 본다** — 짧은 반복이 스물한 번 쌓이는 날과 긴 반복이 여섯 번 쌓이는
    날은 다른 방식으로 같은 비용을 낸다. 이 파일은 매 반복 읽히므로 둘 다 상한이다.

    **경계는 초과가 아니다.** 룰 문구가 「넘으면」이라 정확히 상한인 날은 조용하다 —
    그날 회전을 강요하면 거짓 RED 이고, 다음 append 가 어차피 문다.
    """
    over = []
    lines = len(text.splitlines())
    if lines > HISTORY_LINE_CAP:
        over.append("줄 수 %d > %d" % (lines, HISTORY_LINE_CAP))
    entries = len(HISTORY_ENTRY_HEAD.findall(text))
    if entries > HISTORY_ENTRY_CAP:
        over.append("항목 수 %d > %d" % (entries, HISTORY_ENTRY_CAP))
    if not over:
        return None
    return ("history_current.md 가 상한을 넘었다 — %s. 오래된 항목부터"
            " `history_<NNN>.md` 로 밀어내고 `digest.md` 에 한 줄로 압축한다"
            " (`rules/docs.md` 3절)" % " · ".join(over))


# `status.md` 의 빈손 대조 핀. **줄을 새로 만들지 않고 지금 꼴을 그대로 읽는다** —
# 해시와 날짜가 이미 한 줄에 같이 있다. 실물 한 줄을 그대로 박아 둔다(`test.md` 3절 ⑧):
#   ## 빈손 대조 핀 — 기준 트리 `26f1393` (2026-10-22 반복 747 에 옮겼다)
# **날짜 괄호는 하룻밤짜리 꼴이다** — 2026-09-13~10-22 의 실물은 날짜가 없는
# `## 빈손 대조 핀 — 기준 트리 `064fe56`` 였다(`git show 3d83072:docs/status.md`).
# 그 꼴은 **빨강으로 받는다**(아래 `test_the_dateless_old_form_is_red`) — 날짜가 없으면
# 묵었는지를 셀 수 없고, 조용히 통과시키면 이 자가 처음부터 죽은 채로 초록이 된다.
# 못 찾으면 조용해지는 것이 아니라 **빨강이다** (`pin_rot_gap` 주석).
PIN_LINE = re.compile(
    r"^## 빈손 대조 핀 — 기준 트리 `([0-9a-f]{7,40})` \((\d{4}-\d{2}-\d{2})", re.M)
# 야간 보고서의 **표 줄**에서만 종합 신호를 읽는다. 문서 전체에서 이모지를 찾는 안은
# 범례 줄(`night_2026-10-08.md` 의 「🔴 실패 · 🟡 판단 · 🟢 완료 · ⚪ 빈손」)에
# 거짓 양성을 낸다 — 실측으로 확인했다.
#
# **칸 안에서 알려진 신호 넷을 찾는다 — 첫 글자를 집지 않는다.** 백지 패스 리뷰가
# 재현했다: `| **신호** | *(\S)` 꼴은 `| **신호** | **⚪ 빈손** |` 에서 `*` 를,
# 백틱을 두르면 `` ` `` 를 집어 그 밤이 **빈손으로 세어지지 않고** 꼴 가드도 조용했다.
# 즉 「값을 굵게 감싼다」는 평범한 편집 하나로 재는 자가 죽었다. 라벨 쪽 공백도 함께 푼다
# (정렬 패딩 `| **신호**  |` 가 `None` 이었다). 알려진 넷 밖의 글자는 **신호가 아니다** —
# 꼴 가드가 그 보고서를 빨강으로 받는 쪽이 조용히 세지 않는 쪽보다 낫다.
#
# **첫 매치가 이긴다**(`search`). 관용구가 「**맨 위** 종합 신호」이므로 이것이 규약과
# 같은 방향이다 — 실물 `night_2026-08-29.md` 가 이미 신호 줄을 둘 들고 있다(둘 다 🟢).
REPORT_SIGNAL = re.compile(r"^\| *\*\*신호\*\* *\|[^|]*?(🔴|🟡|🟢|⚪)", re.M)
# 보고서 날짜는 **파일명**에서 읽는다. 같은 날 두 벌이 있는 날이 넷이라
# (`09-09` 2 · `09-10` 2 · `09-12` 3 · `09-14` 2) 접미사를 허용해야 한다.
#
# **날짜 뒤에 구분자를 요구한다**(`(?=[_.])`) — 백지 패스가 실측한 자리다(계획 125 [R125-2]):
# 접두만 보면 `night_2026-10-055.md` 가 **맞고** `group(1)` 이 `2026-10-05` 라 세 자가 전부
# 날짜를 **잘못 읽는다**(`…05extra.md` 도 같다). 접미사 허용은 그대로다 — 실물 다섯은
# `_<슬러그>` 꼴이고 나머지는 `.md` 로 끝나 둘 다 통과한다. 계획 124 가 `is_done` 에서
# 낱말 뒤 구분자를 요구해 닫은 것과 **같은 계열**이다.
REPORT_NAME = re.compile(r"^night_(\d{4}-\d{2}-\d{2})(?=[_.])")
EMPTY_SIGNAL = "⚪"


def night_reports(docs=DOCS):
    """`docs/reports/` 의 야간 보고서를 `(파일명, 본문)` 으로, **날짜순**으로 돌려준다.

    ISO 날짜가 파일명 앞머리에 박혀 있어 사전순이 곧 날짜순이다 — `datetime` 이
    필요 없다. 디렉터리가 없으면 빈 목록이고, **그 길은 `NightReportSignalTest` 가
    하한으로 문다**(0건 위에서 조용히 통과하는 것을 막는다).
    """
    folder = docs / "reports"
    return [(path.name, path.read_text(encoding="utf-8"))
            for path in sorted(folder.glob("night_*.md"))]


def report_signal(text):
    """야간 보고서의 종합 신호 이모지. 표 줄이 없으면 `None`."""
    found = REPORT_SIGNAL.search(text)
    return found.group(1) if found else None


def signal_row_gap(reports):
    """**가장 최신** 보고서가 신호 줄을 안 들었으면 한 줄로 돌려준다.

    **과거는 일부러 안 본다** — 결손 8개가 전부 2026-10-08 이하고, 못 세는 ⚪ 는 전부
    핀 날짜보다 과거라 판정에 영향이 0 이다. 각 보고서는 **쓰인 날 최신**이므로 이 축
    하나로 앞으로의 보고서가 전부 지켜진다.

    **선택이 여기 있는 이유는 변이가 살았기 때문이다** — 축을 테스트 안에 두면
    「최신 대신 최초를 본다」로 바꿔도 가장 오래된 보고서가 줄을 들고 있어 초록이었다.
    """
    if not reports:
        return None
    latest = REPORT_NAME.match(reports[-1][0])
    if not latest:
        return ("최신 야간 보고서 %s 의 이름에서 날짜를 못 읽었다 —"
                " `night_YYYY-MM-DD…` 꼴이어야 하고, 0 패딩이 빠지면"
                " `pin_rot_gap` 의 ⚪ 집계에서 **조용히 빠진다**" % reports[-1][0])
    day = latest.group(1)
    # **그 날짜의 보고서를 전부 본다** — 파일 하나가 아니다. 같은 날 두 벌 이상인 날이
    # 넷이고(`09-09` 2 · `09-10` 2 · `09-12` 3 · `09-14` 2), 한 밤에 둘이 들어가면
    # 사전순 마지막 하나만 보는 축은 앞것을 영구히 검사하지 않는다(백지 패스 지적).
    missing = [name for name, text in reports
               if (REPORT_NAME.match(name) or None)
               and REPORT_NAME.match(name).group(1) == day
               and report_signal(text) is None]
    if not missing:
        return None
    return ("최신 날짜(%s)의 야간 보고서에 `| **신호** | <이모지> …` 줄이 없다 — %s."
            " `pin_rot_gap` 이 이 줄을 읽는다. 없으면 그 밤이 빈손이었는지"
            " 셀 수 없고 핀 가드가 조용히 죽는다" % (day, " · ".join(missing)))


def report_name_gap(reports):
    """이름에서 **날짜를 못 읽는** 보고서를 전부 모아 한 줄로 돌려준다. 없으면 `None`.

    `pin_rot_gap`·`signal_row_gap` 이 **정의역이 비는 것을 모르는 채 조용한 자리**를
    같은 스위트에서 **병행 신고**한다. 둘은 `REPORT_NAME` 으로 날짜를 읽는데 그 정규식이
    0 패딩을 요구하므로, 패딩이 빠진 이름은 ⚪ 집계에서 `if REPORT_NAME.match(name)` 에
    **걸러지고** 사전순 마지막이 아니면 꼴 가드도 못 본다 — 그 조합이 핀 썩음 판정을
    조용히 죽인다 (`digest.md` `## 다음 계획 후보` 의 `[7]`).

    **「입구에서 막는다」가 아니다** — 백지 패스가 기제를 재서 정정했다(계획 125 [R125-1]).
    이 자의 호출자는 `ReportNameTest` **일곱 곳뿐**이고 형제 둘은 한 줄도 안 바뀌었다.
    그래서 `PinRotTest` 만 따로 돌리면 거짓 초록이 유지되고, **전수를 돌릴 때** 이 자가
    옆에서 빨개진다. 전수가 이 저장소의 관문이라 값은 그대로지만 기제는 병행이다.

    **전 자리를 모은다** — `citation_alive_gap` 과 같다. 먼저 걸린 하나만 주면
    고치는 쪽이 전수를 한 번 더 돌려야 다음 것이 보인다.

    **판정은 접두까지다.** 접미사는 허용한다 — 같은 날 두 벌인 날이 넷이라
    (`09-09` 2 · `09-10` 2 · `09-12` 3 · `09-14` 2) 좁히면 실물이 거짓 RED 다.
    날짜의 **값**(`13-45` 류)은 안 본다: 실물 0건이고, `datetime` 을 들이면
    `night_reports` 의 「사전순이 곧 날짜순」 설계가 함께 흔들린다.

    **0건이면 조용하다** — 하한은 `ReportNameTest` 의 살아 있는 축이 `assertTrue` 로
    문다(`NightReportSignalTest` 와 같은 꼴).
    """
    bad = [name for name, _ in reports if not REPORT_NAME.match(name)]
    if not bad:
        return None
    return ("야간 보고서 이름에서 날짜를 못 읽었다 — %s. `night_YYYY-MM-DD…` 꼴이어야"
            " 하고, 0 패딩이 빠지면 `pin_rot_gap` 의 ⚪ 집계에서 **조용히 빠진다**"
            " (사전순 마지막이 아니면 `signal_row_gap` 도 못 본다)" % " · ".join(bad))


def pin_rot_gap(status_text, reports):
    """핀이 마지막 빈손 밤보다 묵었으면 한 줄로 돌려준다. 안 묵었으면 `None`.

    `reports` 는 `(파일명, 본문)` 의 순서열이다 — 재는 일과 판정을 갈라 놔야
    픽스처로 경계를 고정할 수 있다 (`read_budget_gap` 이 `sizes` 를 받는 것과 같다).

    **경계는 초과가 아니다** — 마지막 빈손 밤과 핀이 **같은 날**이면 조용하다. 그 밤이
    제 손으로 옮긴 핀을 그 밤이 무는 것은 거짓 RED 다 (`cap_gap` 과 같은 판단).

    **빈손 밤이 0건이면 조용하다.** 아직 빈손으로 끝난 밤이 없는 저장소에서 무는 것은
    핀과 무관한 사고다.

    **핀 줄을 못 찾으면 빨강이다.** 「재지 못했다」로 비키는 길을 일부러 안 뒀다 —
    꼴이 드리프트하면 이 자가 조용히 죽고, 그것이 이 저장소 최다 재발 계열이다.

    **천장 둘을 백지 패스가 쟀다. 이 자가 못 보는 것이다:**

    ① **해시를 안 본다.** 판정 입력이 날짜 문자열뿐이라, 해시를 묵은 채로 두고 괄호
    안 날짜만 미래로 고치면 초록이다(재현했다). 이 자가 막는 것은 **잊음**이고
    **거짓말이 아니다.** 닫으려면 핀 커밋의 날짜를 `git` 으로 읽어 대조해야 하는데
    그것은 이 계획의 축 밖이다 → `digest.md` 후보로 등재했다.

    ② **해상도가 하루다.** 밤 D 에 핀을 옮긴 뒤 같은 D 안에 변경이 들어오고 D 가
    빈손으로 끝나면 조용하다. 경계를 초과로 바꾸면 그 밤이 제 손으로 옮긴 핀을
    그 밤이 무는 거짓 RED 가 상시가 되므로, **이쪽을 고르고 천장을 적는 것**이 답이다.
    """
    pin = PIN_LINE.search(status_text)
    if not pin:
        return ("핀 줄을 못 찾았다 — `status.md` 의 `## 빈손 대조 핀 — 기준 트리"
                " `<해시>` (<YYYY-MM-DD> …` 꼴이 드리프트했다. 꼴을 되돌리거나"
                " `PIN_LINE` 을 같이 고친다 (`docs/design_history_096.md` 결정)")
    pin_hash, pin_date = pin.group(1), pin.group(2)
    empty = [REPORT_NAME.match(name).group(1) for name, text in reports
             if REPORT_NAME.match(name) and report_signal(text) == EMPTY_SIGNAL]
    if not empty:
        return None
    last = max(empty)
    if last <= pin_date:
        return None
    return ("빈손 대조 핀이 마지막 빈손 밤보다 묵었다 — 핀 `%s` (%s) 인데 빈손 밤이"
            " %s 에 있었다. 그 밤 이후 들어간 것을 핀이 구별하지 못하므로 다음 빈손"
            " 밤의 대조가 아무것도 판정하지 못한다(실측 58파일 `+5,149/-143`)."
            " 핀을 그 밤의 `main` 으로 옮기고 날짜를 그 밤으로 적는다"
            % (pin_hash, pin_date, last))


def python_sources(root=ROOT):
    """훑을 `.py` 를 이름순으로. 이름순이라 실패 목록이 안 흔들린다.

    **없는 디렉터리는 건너뛴다** — 모듈 최상위가 아니라 호출 시점에 도는데도 그렇게
    하는 이유는 얕은 체크아웃 하나가 전수를 흔들지 않게 하기 위해서다. 진짜로 한
    덩이가 사라진 판은 `SOURCE_FLOOR` 가 문다 (`test_deps.py` 와 같은 분담).
    """
    return sorted(p for d in (root / name for name in SOURCE_DIRS) if d.is_dir()
                  for p in d.rglob("*.py"))


def _scope_dups(scope):
    """한 스코프의 `body` 에서 같은 이름 함수 정의가 둘 이상인 자리를 흘린다.

    **`body` 를 직접 보고 `ast.walk` 로 내려가지 않는다** — 부르는 쪽이 스코프마다
    한 번씩 부르므로, 여기서 또 내려가면 안쪽 정의가 바깥 스코프 것으로 센다.

    **`if`·`try` 안의 둘째 정의는 안 본다**(그 `body` 는 다른 리스트다). 조건부 재정의
    (`try: from _x import f / except ImportError: def f()`)는 **의도된 꼴**이라
    그것이 맞다 — 천장은 `dup_def_gap` 의 docstring 에 적었다.
    """
    seen = {}
    for node in scope.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in seen:
                yield node.name, seen[node.name], node.lineno
            seen[node.name] = node.lineno


def dup_def_gap(sources):
    """같은 스코프에 같은 이름 함수 정의가 둘인 자리를 한 줄로. 없으면 `None`.

    **파이썬은 뒤엣것만 남기므로 앞엣것은 도달 불가능한 죽은 코드다.** 실측 근거
    (계획 126 · `digest.md` 후보 `[7]`): `tests/test_docs.py` 에 `def archive_gap` 이
    `:580`·`:609` 둘이었고 죽은 `:580` 의 몸통은 `verdict_gap` 의 복사본이라
    `cell = verdict.strip()` 의 `verdict` 가 **정의되지 않은 이름**이었다. 살아남는
    쪽이 옳은 몸통이어서 **전수 998 이 조용했다** — 피해 경로는 다음 사람이 위에 있어
    먼저 읽히는 죽은 쪽을 고치는 것이고, 그러면 **전수가 초록인 채로 아무 일도
    안 일어난다.** 이 저장소 최다 재발(「재는 자가 죽었는데 초록이다」)이고 이번엔
    재는 자 자신의 파일 안에서 났다.

    **스코프를 안다 — 그래서 `^def ` 를 세지 않는다.** 등재문의 처방은 regex 수집
    이었는데 그 꼴은 서로 다른 클래스의 `setUp`·`index`·`status`·`test_*` 를
    **오탐 7건**으로 잡는다(계획 126 실측). `ast` 는 같은 일을 더 적은 코드로 하고
    오탐이 0 이다 (ponytail 사다리 3번).

    **모든 자리를 모은다** — `report_name_gap`·`citation_alive_gap` 선례. 하나씩
    돌려주면 고치는 쪽이 전수를 한 번 더 돌려야 다음 것이 보인다.

    **천장 둘.** ① `@property`/`@x.setter` 쌍은 같은 이름을 **합법적으로** 다시
    정의하는데 이 저장소에 오늘 0건이라 **면제를 안 만들었다**(ponytail 1번). 들어오면
    이 자가 거짓 RED 를 낸다 — 그 방향이 의도다. 거짓 RED 는 시끄러워 그날 고쳐지고,
    조용한 누락은 이 자가 막으려는 바로 그 병이다.
    ② 문법이 깨진 파일은 `SyntaxError` 로 터진다 — **삼키지 않는다.** 그것도 알려야
    하는 사실이고, 삼키면 안 읽힌 파일이 「위반 0」에 조용히 섞인다.
    """
    # ponytail: 데코레이터를 안 본다 — `@x.setter` 가 들어오면 거짓 RED 다.
    # 그때 둘째 정의의 `decorator_list` 가 `<이름>.setter` 인 것을 면제한다.
    sites = []
    for label, text in sources:
        tree = ast.parse(text, filename=str(label))
        scopes = [tree] + [node for node in ast.walk(tree)
                           if isinstance(node, (ast.ClassDef, ast.FunctionDef,
                                                ast.AsyncFunctionDef))]
        for scope in scopes:
            for name, first, second in _scope_dups(scope):
                sites.append("%s 의 `%s` (:%d 와 :%d)" % (label, name, first, second))
    if not sites:
        return None
    return ("같은 스코프에 같은 이름 함수 정의가 둘이다 — 파이썬은 뒤엣것만 남기므로"
            " 앞엣것은 도달 불가능한 죽은 코드다. 앞엣것을 지운다(고칠 때 위에 있는"
            " 쪽을 고치면 전수가 초록인 채로 아무 일도 안 일어난다): %s"
            % " · ".join(sorted(sites)))


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
                       (DOCS / "metrics.md").read_text(encoding="utf-8"),
                       (DOCS / "history_current.md").read_text(encoding="utf-8"))
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


class LivePlanSyncTest(unittest.TestCase):
    """`index.md` 에서 `진행` 인 계획 행이 `status.md` 의 `plan:` 하나뿐인가.

    **버려진 계획을 무는 자가 0개였다.** 2026-09-09 실물: `iter-third-witness` 가
    개발 2/3 에서 버려져 계획 행 68개 중 **유일한 「진행」**으로 네 계획을 남았고,
    그동안 `status.md` 본문은 그 계획을 설명하며 이미 끝난 스텝을 시켰다.
    전수 737건이 초록이었다 — 문서 가드 여덟 벌이 전부 `status.plan` 이 가리키는
    행만 봐서다(`step_gap` 은 `backoff-recovery` 행을 2/2 = 2/2 로 대조해 초록이고
    뒤에 남겨진 행은 시야 밖, `archive_gap` 은 `완료` 만 아카이브를 요구한다).

    **판정은 `live_gap` 이 한다** — 실물 문서는 늘 맞춰져 있어서 판정에만 붙여 두면
    무력화 변이가 조용히 산다(`StepGapTest`·`IterGapTest` 가 같은 자리에서 배웠다).
    갈래를 밟는 것은 `LiveGapTest` 다.
    """

    def test_only_the_running_plan_is_live(self):
        gap = live_gap((DOCS / "status.md").read_text(encoding="utf-8"),
                       (DOCS / "index.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)


class LiveGapTest(unittest.TestCase):
    """`live_gap` 의 갈래를 합성 문자열로 전부 밟는다.

    **넓어지는 변이 둘을 픽스처가 붙든다** — 2026-09-09 테스트 phase 가 실제로 심어
    보고 **둘 다 745건에서 살아남는 것을 보고** 넣은 자리다.
    ① `^` 앵커 삭제: 어느 행도 줄 중간에 `| plan_x | 진행 |` 를 품지 않아 조용했다.
    무는 것은 **`INDEX` 에 낀 `QUOTED` 한 줄**이고 아래 테스트가 아니다(실측: 테스트를
    지워도 3건이 그대로 죽고, `QUOTED` 를 빼면 앵커 변이가 도로 산다).
    ② 상태 칸 비교를 `in` 으로: `보류(미완)` 은 「진행」을 **안 품어** 우연히 살았다 —
    품는 표기(`진행(재개)`)를 픽스처에 넣어야 비로소 갈린다. 이쪽은 아래
    `test_a_state_that_merely_contains_the_mark_is_not_live` 가 유일한 킬러다.
    **이 docstring 의 앞 판은 ② 를 「여기서 잰다」고 적어 놓고 재지 않았다.** 주장은
    그 주장이 참인 범위까지만 적는다(digest ## 반복 실패).
    """

    # 비고 칸이 **다른 행을 인용하는** 꼴. `^` 앵커가 죽으면 이것을 행으로 읽는다.
    # **오늘 실물에 이 꼴은 0건이라 예방이다** — `docs/index.md` 의 비고 칸이 백틱 안에
    # 파이프를 무는 줄은 34개인데 계획 행을 통째로 인용한 줄은 없다(2026-09-09 실측).
    # 실재하는 것은 **머리 문구** 인용 습관이고(계획 76 · 반복 516), 표 행 인용은 그
    # 습관이 표로 번지는 날의 이야기다. 앞 판 주석은 이 구별 없이 「있다」고 적었다.
    QUOTED = ("| plan_quoting-row | 완료 | loop/z | 1/1 | 통과 |"
              " 옛 행은 `| plan_ghost | 진행 | loop/g | 0/1 |` 였다 |")
    # 같은 행을 **줄 머리로** 올린 것. 조립하지 않고 그대로 적는다 — 산문 한 글자에
    # 매달린 `replace` 사슬은 조용히 no-op 이 되고, 그 결과가 칸이 안 닫힌 깨진 행이었다.
    PROMOTED = "| plan_ghost | 진행 | loop/g | 0/1 | — | 부기 |"
    INDEX = "\n".join([
        "| plan_live-plan-gap-2 | 완료 | loop/x | 3/7 | 통과 | 부기 |",
        "| plan_live-plan-gap | 진행 | loop/x | 1/2 | — | 부기 |",
        "| plan_left-behind | 완료 | loop/y | 2/2 | 통과 | 부기 |",
        QUOTED,
    ])

    @staticmethod
    def status(plan):
        return "attempt: 0\nstep: 1/2\nplan: %s\nctx: 62\n" % plan

    def test_the_running_plan_alone_is_quiet(self):
        self.assertIsNone(live_gap(self.status("live-plan-gap"), self.INDEX),
                          "맞는 문서를 신고했다 — 매 반복이 빨개진다")

    def test_an_abandoned_plan_is_reported(self):
        index = self.INDEX.replace("| plan_left-behind | 완료 |",
                                   "| plan_left-behind | 진행 |")
        gap = live_gap(self.status("live-plan-gap"), index)
        self.assertIsNotNone(gap, "버려진 계획이 진행인 채인데 통과시켰다 — 그 결함이다")
        self.assertIn("left-behind", gap, "어느 계획이 남겨졌는지 안 적었다")
        # 메시지는 대조 대상을 「지금 도는 것은 …」으로 **일부러** 적는다. 신고 목록은
        # 그 앞이고, 지금 도는 계획이 거기 있으면 안 된다.
        self.assertNotIn("live-plan-gap", gap.split("(지금 도는 것은")[0],
                         "지금 도는 계획을 남겨진 것으로 신고했다")

    def test_every_abandoned_plan_is_named(self):
        index = self.INDEX.replace("| 완료 |", "| 진행 |")
        gap = live_gap(self.status("live-plan-gap"), index)
        self.assertIsNotNone(gap, "여럿이 남겨졌는데 통과시켰다")
        for slug in ("live-plan-gap-2", "left-behind"):
            self.assertIn(slug, gap, "%s 를 안 적었다 — 하나만 신고하고 멈췄다" % slug)

    def test_no_live_row_is_quiet(self):
        # 계획을 마감한 직후·`plan: null` 이 정당하게 그렇다. 등재 누락은 `step_gap` 몫이다.
        index = self.INDEX.replace("| 진행 |", "| 완료 |")
        self.assertIsNone(live_gap(self.status("live-plan-gap"), index),
                          "`진행` 이 0개인데 신고했다 — 마감 직후가 매번 빨개진다")
        self.assertIsNone(live_gap(self.status("null"), index),
                          "`plan: null` + 진행 0개는 하네스 템플릿의 정상 상태다")

    def test_null_plan_with_a_live_row_is_reported(self):
        gap = live_gap(self.status("null"), self.INDEX)
        self.assertIsNotNone(gap, "계획 없이 진행 행만 남았는데 통과시켰다")
        self.assertIn("live-plan-gap", gap, "남은 행을 안 적었다")

    def test_a_held_row_is_not_live(self):
        # `보류(미완)` 은 「진행」을 **안 품어** 부분 문자열 비교로도 통과한다. 가르는
        # 것은 아래 `진행(재개)` 쪽이고, 이 케이스는 보류 표기 자체를 붙든다.
        index = self.INDEX.replace("| plan_left-behind | 완료 |",
                                   "| plan_left-behind | 보류(미완) |")
        self.assertIsNone(live_gap(self.status("live-plan-gap"), index),
                          "보류 행을 진행으로 읽었다 — 버려둔 계획이 매 반복 빨개진다")

    def test_a_state_that_merely_contains_the_mark_is_not_live(self):
        # 상태 칸을 `in` 으로 보는 변이가 745건에서 살아남은 자리다(2026-09-09 실측).
        index = self.INDEX.replace("| plan_left-behind | 완료 |",
                                   "| plan_left-behind | 진행(재개) |")
        self.assertIsNone(live_gap(self.status("live-plan-gap"), index),
                          "「진행」을 품기만 한 칸을 진행으로 읽었다 — 칸을 잘라서"
                          " 같은지 보는 것이 계약이다")

    def test_a_row_quoted_inside_a_cell_is_not_a_row(self):
        # 앵커 변이를 무는 것은 `INDEX` 의 `QUOTED` 줄이고, 이 테스트가 재는 것은 그
        # 반대편이다 — **앵커가 산 채로 진짜 행까지 놓치지는 않는다**. 둘을 한 자리에서
        # 보여야 「인용은 안 읽고 행은 읽는다」가 한 계약으로 읽힌다.
        self.assertIsNone(live_gap(self.status("live-plan-gap"), self.INDEX),
                          "비고 칸이 인용한 행을 진짜 행으로 읽었다 — `^` 가 죽었다")
        gap = live_gap(self.status("live-plan-gap"),
                       self.INDEX + "\n" + self.PROMOTED)
        self.assertIsNotNone(gap, "줄 머리에 놓인 같은 슬러그의 행은 진짜 행이다")
        self.assertIn("ghost", gap, "줄 머리의 행을 안 읽었다")

    def test_missing_status_line_is_reported(self):
        # 머리 형식이 바뀌면 `None` 위에서 조용히 통과하는 것이 유일한 눈먼 자리다.
        self.assertIsNotNone(live_gap("step: 1/2\n", self.INDEX),
                             "`plan:` 줄이 없는데 통과시켰다")


class StatusSignalTest(unittest.TestCase):
    """살아 있는 `docs/status.md` 의 `signal:` 이 아는 낱말인지 판정한다.

    **이 값은 2026-10-26 부터 하중을 받는다** — 자동 루프의 병합 게이트가
    `~/.local/bin/o-search-autoloop.sh` 에서 그것을 읽어 병합 여부를 가른다(게이트 ⑲ ㉠).
    그 전까지는 아무도 안 보는 값이었고, 그래서 **저장소에 읽는 자가 0개인 채로 하중을**
    **받게 됐다**: 오타·새 낱말·한글 표기가 들어간 밤에도 전수는 초록이고 게이트는
    조용히 영구히 병합을 안 한다. 그 침묵의 유일한 기록은 저장소 밖 로그다(⑲ⓑ).

    **게이트의 조건은 복사하지 않는다** — 「DONE 이거나 GREEN+`plan: null` 이면 병합」을
    여기 적으면 저장소 밖 로직의 사본이 되고, 사람이 스크립트를 고치는 날 **거짓말하는**
    **가드**가 된다(`digest` 후보 `[6]` 의 「측정기가 규칙을 복사하는 사고」). 무는 것은
    **어휘뿐**이다 — 넷 중 하나인가. 게이트가 그 넷으로 무엇을 하는지는 안 본다.

    갈래를 밟는 것은 `SignalGapTest` 다 — 실물은 늘 맞춰져 있어 판정에만 붙여 두면
    무력화 변이가 조용히 산다(`LivePlanTest`·`IterGapTest` 가 같은 자리에서 배웠다).
    """

    def test_the_live_status_carries_a_known_signal(self):
        gap = signal_gap((DOCS / "status.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)


class SignalGapTest(unittest.TestCase):
    """`signal_gap` 의 갈래를 합성 문자열로 전부 밟는다.

    **frontmatter 만 본다.** 이 문서의 산문은 게이트를 인용하느라 `signal: DONE` 같은
    낱말을 백틱 안에 수십 번 들고 있고(이 반복이 적은 게이트 ⑲ 본문이 그렇다), 줄
    머리로 올라온 인용이 한 번이라도 생기면 **본문이 판정을 가져간다.** `live_gap` 이
    `PLAN_SLUG` 로 전문을 훑는 것과 **일부러 다르다** — 그쪽은 슬러그가 산문에 줄
    머리로 설 일이 없지만 이쪽은 인용이 일상이다.
    """

    HEAD = "---\nsignal: %s\nphase: 개발\nplan: x\n---\n"

    def test_each_known_signal_is_quiet(self):
        for word in ("GREEN", "YELLOW", "RED", "DONE"):
            with self.subTest(word):
                self.assertIsNone(signal_gap(self.HEAD % word),
                                  "아는 신호를 신고했다 — 매 반복이 빨개진다")

    def test_a_korean_word_is_reported(self):
        gap = signal_gap(self.HEAD % "초록")
        self.assertIsNotNone(gap, "모르는 낱말을 통과시켰다")
        self.assertIn("초록", gap, "실제 값을 안 인쇄하면 고칠 자리를 모른다")
        for word in ("GREEN", "YELLOW", "RED", "DONE"):
            self.assertIn(word, gap, "아는 넷을 안 인쇄했다")

    def test_the_vocabulary_is_case_sensitive(self):
        # 게이트는 `grep -q '^signal: GREEN'` 이라 `Green` 을 **안 본다**.
        self.assertIsNotNone(signal_gap(self.HEAD % "Green"),
                             "대소문자가 다른 값을 통과시켰다")

    def test_an_empty_value_is_reported(self):
        self.assertIsNotNone(signal_gap("---\nsignal:\nphase: 개발\n---\n"),
                             "값이 빈 줄을 통과시켰다")

    def test_a_missing_line_is_unmeasured_not_a_verdict(self):
        # 「재지 못했다」와 「빨강」을 안 섞는다 — `live_gap` 이 `plan:` 에 쓰는 그 꼴이다.
        gap = signal_gap("---\nphase: 개발\nplan: x\n---\n")
        self.assertIsNotNone(gap, "`signal:` 줄이 없는데 통과시켰다")
        self.assertIn("못 찾았다", gap, "어휘 위반과 구별되는 사유를 안 냈다")

    def test_prose_quoting_the_gate_does_not_decide(self):
        # 실물이 늘 하는 꼴 — 산문이 게이트 조건을 줄 머리로 인용한다.
        # frontmatter 를 안 보고 전문을 훑으면 이 `DONE` 이 판정을 가져간다.
        doc = self.HEAD % "초록" + "\n## 이 밤\n\nsignal: DONE 이면 병합한다고 적혀 있다\n"
        gap = signal_gap(doc)
        self.assertIsNotNone(gap, "산문의 인용이 판정을 가져갔다")
        self.assertIn("초록", gap, "frontmatter 가 아닌 줄을 읽었다")

    def test_a_shape_the_gate_cannot_read_is_reported(self):
        # **[R123-4] 백지 패스가 잡은 가장 심한 것** — 공백이 하나가 아니면 게이트의
        # 리터럴 `grep -q '^signal: GREEN'` 이 **못 읽는다**(실측: `signal:GREEN`·
        # `signal:  GREEN` 둘 다 못 읽음). 그런데 앞 판은 셋 다 **초록**이었다 —
        # 즉 이 자가 막으려던 바로 그 실패(전수 초록 + 게이트 영구 미병합) 위에서
        # 자신이 조용했다. 어휘를 대소문자까지 엄격히 받는 근거와도 모순이었다.
        for bad in ("signal:GREEN", "signal:  GREEN", "signal:\tGREEN"):
            with self.subTest(bad):
                gap = signal_gap("---\n%s\nphase: x\n---\n" % bad)
                self.assertIsNotNone(gap, "게이트가 못 읽는 꼴을 통과시켰다")

    def test_the_gate_readable_shape_is_quiet(self):
        # 꼬리 공백과 `#` 주석은 게이트가 접두로 읽으므로 **통과해야 한다** —
        # 이 문서의 다른 frontmatter 줄들이 `#` 주석을 일상으로 단다(`plan:`·`mode:`).
        for ok in ("signal: GREEN", "signal: GREEN   ", "signal: GREEN  # 사유"):
            with self.subTest(ok):
                self.assertIsNone(signal_gap("---\n%s\nphase: x\n---\n" % ok),
                                  "게이트가 읽는 꼴을 신고했다 — 매 반복이 빨개진다")

    def test_an_empty_frontmatter_does_not_let_prose_decide(self):
        # **[R123-1]** `---\n---` 이면 앞 판의 `fenced`(`[3:]`)와 `head`(`[4:]`) 가
        # 비대칭이라 **본문 전체가 head** 가 됐다 — 「조용한 초록」의 **세 번째 입구**다.
        gap = signal_gap("---\n---\nsignal: DONE 이면 병합한다\n")
        self.assertIsNotNone(gap, "빈 frontmatter 에서 산문이 판정을 가져갔다")

    def test_a_body_rule_is_not_a_closing_fence(self):
        # **[R123-3]** 닫는 울타리를 잃은 문서에서 **본문의 수평선**이 그 역할을 해
        # 산문이 head 에 들어왔다. frontmatter 는 빈 줄을 품지 않는다는 것으로 가른다.
        doc = "---\nphase: x\n\n## 본문\n\nsignal: DONE\n\n---\n"
        self.assertIsNotNone(signal_gap(doc), "본문 수평선을 울타리로 읽었다")

    def test_a_stray_signal_line_in_the_body_is_reported(self):
        # **[R123-6]** 가드는 frontmatter 만 보는데 **게이트는 전문을 grep 한다.**
        # 본문에 백틱 없이 줄 머리로 `signal: DONE` 이 들어오면 가드는 조용하고
        # 게이트는 보류 브랜치를 병합한다 — 그 비대칭을 여기서 닫는다.
        doc = "---\nsignal: YELLOW\nphase: x\n---\n\nsignal: DONE 이라고 적혀 있다\n"
        gap = signal_gap(doc)
        self.assertIsNotNone(gap, "본문의 줄머리 `signal:` 을 통과시켰다 — 게이트는 그것을 읽는다")

    def test_a_document_without_frontmatter_is_unmeasured(self):
        # **2026-10-26 테스트 phase 가 제 구현에서 잡은 조용한 초록이다.**
        # 울타리가 전무하면 `split` 이 전문을 head 로 돌려주고, 산문의 인용 한 줄이
        # 판정을 가져가 **초록**이었다 — 이 저장소 최다 재발 계열(「조용한 초록」)이
        # 그 계열을 막으려고 만든 자 안에서 재현된 꼴이다.
        gap = signal_gap("# 보고\n\nsignal: DONE 이면 병합한다고 적혀 있다\n")
        self.assertIsNotNone(gap, "울타리 없는 문서에서 산문이 판정을 가져갔다")
        self.assertIn("재지 못했다", gap, "어휘 위반이 아니라 「재지 못했다」여야 한다")

    def test_a_body_signal_before_a_rule_needs_the_opening_fence(self):
        # **변이 ⓟ 가 살아서 드러난 형제 구멍이다** — 여는 울타리 검사를 지워도
        # 나머지 테스트가 전부 통과했다(다른 갈래가 먼저 물어서다). 이 꼴만
        # **그 검사 하나에 매달려 있다**: 제목 다음에 `signal:` 이 서고 그 뒤에
        # 수평선이 오면 `lines[1:close]` 가 그 줄을 frontmatter 로 삼아 **초록**이다
        # (실측: 변이 하에서 초록 · 지금 구현에서 빨강).
        self.assertIsNotNone(signal_gap("# 제목\nsignal: GREEN\n---\n"),
                             "여는 울타리가 없는데 본문의 `signal:` 을 판정했다")

    def test_an_unclosed_frontmatter_is_unmeasured(self):
        # 여는 울타리만 있는 꼴. 닫는 것이 없으면 **경계를 그을 수 없다** —
        # 전문을 head 로 삼으면 위와 같은 구멍이 다른 입구로 열린다.
        gap = signal_gap("---\nsignal: GREEN\n")
        self.assertIsNotNone(gap, "닫히지 않은 frontmatter 를 판정했다")
        self.assertIn("재지 못했다", gap, "어휘 위반이 아니라 「재지 못했다」여야 한다")

    def test_the_closing_fence_bounds_the_frontmatter(self):
        # frontmatter 에 `signal:` 이 **없을** 때 본문의 인용으로 내려가면 조용해진다.
        doc = "---\nphase: 개발\n---\n\nsignal: GREEN\n"
        self.assertIn("못 찾았다", signal_gap(doc) or "",
                      "닫는 울타리를 안 보고 본문까지 내려갔다")


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

    def test_the_done_section_names_only_archives_that_exist(self):
        """**반대 방향** — 명부가 가리킨 것이 실재하나.

        위 단언은 「모든 아카이브가 명부에 있나」만 본다. 2026-10-07 실측으로 명부가
        **없는 파일 `history_075.md`** 를 들고 있었다 — 그 파일은 계획 89 커밋에서
        만들어졌다가 **같은 커밋에서 지워졌고**(내용은 `history_079.md` 로 갔다),
        명부는 그 이름을 그대로 들고 반 년을 갔다. 계획 112 가 세운 문서 인용 자도
        이걸 못 본다 — 그 패턴은 `plan_`·`design_` 접두만 읽는다.

        **절을 `## 완료` 로 자르는 것은 위 단언과 같은 이유다** — 다른 절에는 「없는
        이름을 신고하는 문장 자신」이 산다(이 구멍을 등재한 후보 줄이 실제로 그렇다).
        """
        digest = DOCS / "digest.md"
        section = done_section(digest.read_text(encoding="utf-8"))
        self.assertIsNotNone(section, "digest.md 에서 `## 완료` 절을 못 찾았다")
        named = sorted(set(re.findall(r"history_[0-9]+\.md", section)))
        # 순회가 죽으면 **0건 초록**이 된다. 실물은 아카이브 수만큼 있으니 하한을 둔다.
        self.assertGreaterEqual(
            len(named), 90,
            "명부에서 아카이브 이름을 %d 개밖에 못 읽었다 — 절을 잘못 잘랐으면 0건"
            " 초록이 된다" % len(named))
        gone = [n for n in named if not (DOCS / n).is_file()]
        self.assertEqual(
            [], gone,
            "명부가 없는 파일을 가리킨다 — 지워졌거나 개명된 아카이브다. 이름을 빼거나"
            " 실제 파일 이름으로 고친다:\n" + "\n".join("  " + n for n in gone))


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

    def test_history_head_reads_the_end_of_a_range(self):
        # 범위 머리(`487~490`)에서 앞 번호를 집으면 자가 **낮은 쪽**을 최댓값으로 믿는다.
        # `?:` 를 지우는 변이는 `group(1)` 이 `487` 이 되어 여기서 죽는다.
        self.assertEqual(["490"], HIST_ITER.findall("### 반복 487~490 — 계획 84"))
        self.assertEqual(["494"], HIST_ITER.findall("### 반복 494 — 짧은 경로"))
        self.assertEqual(
            [], HIST_ITER.findall("`### 반복 439` 처럼 줄 중간에 인용한다"),
            "인용을 항목 머리로 읽었다 — `^` 가 죽었다")
        self.assertEqual([], HIST_ITER.findall("#### 반복 12 — 더 깊은 제목"),
                         "`####` 를 물었다 — 머리 깊이가 안 고정됐다")


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

    # 마지막 항목이 최댓값이 **아닌** 모양을 픽스처 자신이 든다 — 2026-09-09 실물이
    # 그랬고(494 뒤에 병합된 항목이 490 을 달았다), 「마지막 항목」으로 짠 자는
    # 여기서만 죽는다.
    #
    # **최댓값을 범위 머리에서 나오게 둔 것도 픽스처의 일**이다 — 2026-09-10 반복 528
    # 변이 실측: `HIST_ITER` 의 범위 처리(`(?:[0-9]+~)?`)를 지우면 죽는 것이
    # `IterationPatternTest` **한 벌뿐**이고 판정 층은 조용했다. 최댓값이 여느 머리에서
    # 나오면 범위를 잘못 읽어도 `max` 가 안 움직여서다. 실물이 조용한 것은 더 얇은
    # 이유였다 — 오늘 `history_current.md` 의 최신 머리가 마침 범위가 아니었을 뿐이고,
    # 머리 15개 중 **6개(40%)가 범위**다. **반사실을 실측했다**(반복 529 리뷰): 최신
    # 머리만 `527~528` 로 바꿔 같은 변이를 태우니 `IterationSyncTest` 가
    # 「최대 527 ≠ iteration 528」로 물었다. **이빨이 그날 기록의 표기에 달려 있으면
    # 그것은 자가 아니라 우연이다.**
    HISTORY = "\n".join([
        "### 반복 355 — 앞",
        "### 반복 350~356 — 뒤에 병합됐지만 최댓값이고, 그 값이 범위 끝에서 나온다",
        "### 반복 354~355 — 옛 지점에서 갈라진 것이 뒤에 왔다",
    ])

    @staticmethod
    def status(iteration):
        return "plan: x\niteration: %s\nctx: 55\n" % iteration

    def test_agreeing_docs_have_no_gap(self):
        self.assertIsNone(
            iter_gap(self.status("356"), self.METRICS, self.HISTORY),
            "맞는 문서를 어긋났다고 신고했다 — 매 반복이 빨개진다")

    def test_iteration_mismatch_is_reported(self):
        gap = iter_gap(self.status("357"), self.METRICS, self.HISTORY)
        self.assertIsNotNone(gap, "356 ≠ 357 을 통과시켰다 — 4회 재발한 그 결함이다")
        self.assertIn("356", gap, "어느 수가 어긋났는지 안 적었다")
        self.assertIn("357", gap, "어느 수가 어긋났는지 안 적었다")

    def test_missing_metrics_row_is_reported(self):
        # 표 모양이 바뀌면 `a` 가 `None` 이다 — 조용히 통과하면 안 된다.
        gap = iter_gap(self.status("356"), "| 반복 수 | 356 |", self.HISTORY)
        self.assertIsNotNone(gap, "metrics 에 행이 없는데 통과시켰다")
        self.assertIn("metrics.md", gap, "어느 문서가 비었는지 안 적었다")

    def test_missing_status_line_is_reported(self):
        gap = iter_gap("night_iterations: 173\n", self.METRICS, self.HISTORY)
        self.assertIsNotNone(gap, "status 에 줄이 없는데 통과시켰다")
        self.assertIn("status.md", gap, "어느 문서가 비었는지 안 적었다")

    def test_history_disagreeing_with_the_other_two_is_reported(self):
        """둘이 **나란히** 틀린 그 모양이다 — status·metrics 는 서로 맞는다."""
        metrics = self.METRICS.replace("| 반복 | 356 |", "| 반복 | 352 |")
        gap = iter_gap(self.status("352"), metrics, self.HISTORY)
        self.assertIsNotNone(
            gap, "status·metrics 가 나란히 352 인데 기록은 356 이다 — 그 병합 모양이다")
        self.assertIn("history_current.md", gap, "어느 문서가 갈렸는지 안 적었다")
        self.assertIn("356", gap, "기록의 최댓값을 안 적었다")

    def test_missing_history_head_is_reported(self):
        # 머리 문구가 드리프트하면 `heads` 가 비고, 그때 `max()` 는 예외다.
        # 조용한 통과도 트레이스백도 아닌 한 줄 신고여야 한다.
        gap = iter_gap(self.status("356"), self.METRICS, "## 반복 356 — 머리가 아니다\n")
        self.assertIsNotNone(gap, "기록에 머리가 없는데 통과시켰다")
        self.assertIn("history_current.md", gap, "어느 문서가 비었는지 안 적었다")


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

    def test_candidate_heads_still_found(self):
        # 추출기가 빈 목록을 내면 위 단언은 «볼 것이 없어» 초록이다. 못을 박아 둔다.
        # **포인터 수가 아니라 절 머리 수에 박는다** — 포인터는 회전이 지우는 쪽이라
        # (계획 72 실측: 10개가 10개 다 취소선) 닫힌 후보를 지우는 날 0 이 된다.
        found = candidate_heads((DOCS / "digest.md").read_text(encoding="utf-8"))
        self.assertGreaterEqual(
            len(found), CANDIDATE_HEAD_FLOOR,
            "후보 절 머리가 %d개다 — 실물 문서의 절 이름이 `CANDIDATE_HEAD` 와 갈렸다"
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

    def test_heads_do_not_count_other_sections(self):
        # `## ` 를 아무거나 세는 변이는 실물에서 조용하다 — `digest.md` 의 `## ` 줄은
        # 일곱이라 하한 2 를 그냥 넘긴다. 넓어지는 쪽은 여기서만 죽는다.
        text = "# 다이제스트\n## 완료\n## 반복 실패\n## 다음 계획 후보\n- 줄\n"
        self.assertEqual(candidate_heads(text), ["## 다음 계획 후보"])


class OpenSyncTest(unittest.TestCase):
    """집어간 후보가 실물에서 닫혀 있나. 갈래는 `OpenGapTest` 가 밟는다.

    `StrikeSyncTest` 와 **같은 두 문서를 반대 방향으로** 읽는다. 저쪽이 못 보는 것이
    여기 산다: 후보 줄에 포인터 관용구가 하나도 안 남아(2026-09-29 실측 75줄 중 0)
    저쪽은 표본 0으로 조용한데, 착수 관용구는 완료 행에 26개가 살아 있다.
    """

    def test_opened_candidates_are_struck_through(self):
        gap = open_gap((DOCS / "digest.md").read_text(encoding="utf-8"),
                       (DOCS / "index.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)


class FalseStrikeSyncTest(unittest.TestCase):
    """취소선 줄이 실물에서 닫힌 계획만 가리키나. 갈래는 `FalseStrikeGapTest`."""

    def test_struck_lines_point_at_finished_plans(self):
        gap = false_strike((DOCS / "digest.md").read_text(encoding="utf-8"),
                           (DOCS / "index.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)


class OpenGapTest(unittest.TestCase):
    """`open_gap` 의 갈래를 합성으로 밟는다. 실물은 고치면 초록이라 한 번씩만 지난다."""

    ROW = ("| plan_%s | 완료 | loop/x | 1/1 | 통과 | **99.** 탐색 **6순위** — "
           "`digest ## 다음 계획 후보` 의 `[7]` 「%s」 를 집었다 |")
    DIGEST = "## 다음 계획 후보\n\n- [7] **%s** (2026-09-29 실측)\n"
    # 같은 관용구에서 **점수 표기만** 뺀 꼴. 실물에서 **둘**이 이렇게 적는다
    # (2026-10-12 실측: 모집단 29 중 읽히는 것 8 · 그중 점수 없는 꼴이
    # `plan_hidden-passage`·`plan_focus-ring-combinator` 둘). 처음 적었던 「다수가」는
    # 과장이었다 — 바로 위 주석이 그 수를 정확히 적고 있었다.
    SCORELESS_ROW = ("| plan_%s | 완료 | loop/x | 1/1 | 통과 | **99.** 탐색 **6순위** — "
                     "`digest ## 다음 계획 후보` 의 「%s」 를 집었다 |")

    def _index(self, n=3, title="어떤 자리"):
        return "\n".join(self.ROW % ("s%d" % i, title) for i in range(n))

    def test_a_live_candidate_of_a_finished_plan_bites(self):
        gap = open_gap(self.DIGEST % "어떤 자리", self._index())
        self.assertIn("취소선이 없다", gap)
        self.assertIn("어떤 자리", gap)

    def test_a_struck_candidate_is_silent(self):
        digest = "## 다음 계획 후보\n\n- ~~[7] **어떤 자리**~~ 닫혔다 — 계획 99 `s0`.\n"
        self.assertIsNone(open_gap(digest, self._index()))

    # 짧은 경로 행은 `| (짧은 경로) <슬러그> |` 로 등재된다. 같은 파일의
    # `ANY_PLAN_ROW`(`:126`) 가 **그 두 꼴이 섞여 산다**고 이미 적어 뒀는데
    # `opened_candidates` 의 모집단만 `| plan_` 접두로 좁아, 짧은 경로가 집은 후보는
    # **관용구를 ① 꼴로 맞춰 적어도** 구조적으로 안 읽혔다(2026-10-15 반복 709 실측:
    # 착수 관용구를 단 짧은 경로 행 5개 · 추출 0).
    SHORT_ROW = ("| (짧은 경로) %s | 완료 | loop/x | 1/1 | 해당 없음 | **짧은 경로.** "
                 "근거 — 탐색 **6순위** · `digest ## 다음 계획 후보` 의 `[6]` 「%s」 를 집었다 |")

    def test_a_short_path_row_is_in_the_population(self):
        """짧은 경로 행이 집어간 후보도 대조된다 — 접두가 둘이라서다.

        `plan_` 쪽 제목은 **그어 두고** 짧은 경로 쪽만 열어 둔다 — `open_gap` 은 첫
        어긋남에서 돌아오므로, 그러지 않으면 `plan_` 행이 먼저 물어 이 축이 조용히
        통과한다(처음 쓴 판이 실제로 그랬다).
        """
        index = self._index(2) + "\n" + self.SHORT_ROW % ("짧은것", "짧은 자리")
        digest = ("## 다음 계획 후보\n\n"
                  "- ~~[7] **어떤 자리**~~ 닫혔다 — 계획 99 `s0`.\n"
                  "- [6] **짧은 자리** (2026-10-15 실측)\n")
        gap = open_gap(digest, index)
        self.assertIn("취소선이 없다", gap)
        self.assertIn("짧은 자리", gap)

    def test_a_short_path_row_struck_is_silent(self):
        index = self._index(2) + "\n" + self.SHORT_ROW % ("짧은것", "짧은 자리")
        digest = (self.DIGEST % "어떤 자리"
                  + "- ~~[6] **짧은 자리**~~ 닫혔다 — 계획 99 `짧은것`.\n")
        # 「어떤 자리」가 안 그어져 있으니 그쪽이 물어야 하고, 짧은 자리는 조용하다.
        self.assertNotIn("짧은 자리", open_gap(digest, index) or "")

    def test_a_row_without_the_rank_idiom_is_not_counted(self):
        # 방법론 인용은 「탐색 N순위」가 없다 — 오탐 축이라 실물에 표본이 안 남는다.
        rows = self._index().replace("탐색 **6순위** — ", "")
        self.assertIn("하한", open_gap(self.DIGEST % "어떤 자리", rows))

    def test_a_candidate_outside_the_section_is_not_read(self):
        # 절 밖의 줄을 읽었으면 「취소선이 없다」가 나온다. 하한 문구가 나온다는 것이
        # 곧 **안 읽었다**는 뜻이다 — 대조 표본이 0이라 못이 먼저 문다.
        gap = open_gap("## 완료\n\n- [7] **어떤 자리**\n", self._index())
        self.assertNotIn("취소선이 없다", gap)
        self.assertIn("하한", gap)

    def test_too_few_compared_pairs_bite(self):
        self.assertIn("하한 2", open_gap(self.DIGEST % "어떤 자리", self._index(1)))

    def test_rotation_draining_the_section_bites(self):
        # 착수 행은 append-only 라 안 줄지만 후보 절은 회전으로 마른다. 못을 완료 행
        # 수에 박았다면 여기서 조용했다 — 계획 61 의 자가 죽은 것과 같은 죽음이다.
        gap = open_gap("## 다음 계획 후보\n\n- [1] **딴 자리**\n", self._index(6))
        self.assertIn("대조된 것이 0 자리", gap)

    def test_a_row_citing_the_title_without_a_score_is_counted(self):
        # **제목 추출 실패는 조용히 빠진다** — 하한은 점수를 적은 다른 둘이 채우고,
        # 빠진 행이 들고 온 **열린 후보가 숨는다.** 실물의 조용한 초록을 그대로
        # 재연한 자리다(2026-10-11: `plan_hidden-passage` 가 2026-09-02 등재 뒤
        # 계획 51 이 닫았는데도 취소선 없이 살아 있었고 전수 868 이 초록이었다).
        index = "\n".join([self.ROW % ("s0", "닫힌 자리"),
                           self.ROW % ("s1", "닫힌 자리"),
                           self.SCORELESS_ROW % ("s2", "숨은 자리")])
        digest = ("## 다음 계획 후보\n\n"
                  "- ~~[7] **닫힌 자리**~~ 닫혔다 — 계획 99 `s0`.\n"
                  "- [7] **숨은 자리** (2026-10-11 실측)\n")
        gap = open_gap(digest, index)
        self.assertIsNotNone(gap, "점수 없는 완료 행이 모집단에서 빠져 열린 후보가 숨었다")
        self.assertIn("취소선이 없다", gap)
        self.assertIn("숨은 자리", gap)


class FalseStrikeGapTest(unittest.TestCase):
    """`false_strike` 의 갈래를 합성으로 밟는다."""

    DIGEST = "## 다음 계획 후보\n\n" + "".join(
        "- ~~[7] **자리 %d**~~ **닫혔다 — 2026-09-29 계획 9%d `s%d`.**\n" % (i, i, i)
        for i in range(3))
    ROWS = "\n".join("| plan_s%d | 완료 | loop/x | 1/1 | 통과 | 비고 |" % i
                     for i in range(3))

    def test_all_pointers_finished_is_silent(self):
        self.assertIsNone(false_strike(self.DIGEST, self.ROWS))

    def test_a_pointer_at_a_running_plan_bites(self):
        rows = self.ROWS.replace("| plan_s1 | 완료 |", "| plan_s1 | 진행 |")
        self.assertIn("거짓 취소선", false_strike(self.DIGEST, rows))

    def test_a_pointer_missing_from_the_index_bites(self):
        rows = self.ROWS.replace("| plan_s2 |", "| plan_other |")
        self.assertIn("등재에 없는", false_strike(self.DIGEST, rows))

    def test_the_short_path_row_form_is_accepted(self):
        rows = self.ROWS.replace("| plan_s0 |", "| (짧은 경로) s0 |")
        self.assertIsNone(false_strike(self.DIGEST, rows))

    def test_too_few_struck_pointers_bite(self):
        digest = self.DIGEST.replace("**닫혔다 — 2026-09-29 계획 92 `s2`.**", "")
        self.assertIn("하한 3", false_strike(digest, self.ROWS))


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
        # 오탐 축 — 셋 다 `rules/e2e.md` 가 허용하는 정당한 판정이고 `통과` 가 없다.
        # **`—` 와 빈 칸은 일부러 여기 없다** — 그것은 정당한 판정이 아니라 이 자가
        # 못 무는 **천장**이고(계획 71 계획서 8절), 여기 적으면 천장을 「옳다」고
        # 못박는 것이 된다. 여는 조건은 날짜 아닌 비판정이 실물에 나타나는 날이다.
        for cell in ("없음(제품 코드 0줄)", "**새 e2e 0개**(기존 스크립트에 더했다)",
                     "생략 — 문서 축"):
            with self.subTest(cell=cell):
                self.assertIsNone(verdict_gap(self.index(self.DONE % ("x-one", cell))))

    def test_date_inside_a_verdict_is_not_a_gap(self):
        # 날짜가 **판정 안에** 있는 것은 판정이다. 칸 전체가 날짜뿐일 때만 문다.
        self.assertIsNone(verdict_gap(self.index(
            self.DONE % ("dated-verdict", "통과(2026-09-07)"))))

    def test_running_row_is_not_bitten(self):
        # 오탐 축 — 진행 중인 계획의 e2e 칸은 아직 비어 있는 것이 맞다.
        self.assertIsNone(verdict_gap(self.index(self.RUNNING)))

    def test_a_column_inserted_before_e2e_is_reported(self):
        # 열이 **줄면** 행 머리 수가 갈려 잡히지만, e2e **앞에** 끼우면 개수가 맞아
        # 통과하고 엉뚱한 칸을 판정으로 읽는다(2026-09-07 계획 71 리뷰 실측 —
        # 날짜 칸을 물어 **틀린 RED** 가 났다). 단언을 `표 머리` 에 거는 것은
        # 아래 행이 옛 갈래(날짜 칸)로도 울기 때문이다 — 다른 이유로 초록이면
        # 이 자는 아무것도 안 잰다(`digest.md` 「부정 단언 하나가 다른 이유로」).
        text = ("# 색인\n\n| 계획 | 상태 | 브랜치 | 스텝 | 날짜 | e2e | 비고 |\n"
                "| plan_done-one | 완료 | loop/x | 1/1 | 2026-09-07 | 통과 | 설명 |\n")
        gap = verdict_gap(text)
        self.assertIsNotNone(gap)
        self.assertIn("표 머리", gap)

    def test_a_missing_head_is_reported(self):
        # 머리가 아예 없으면 자리 약속을 확인할 수 없다 — 침묵이 아니라 신고다.
        gap = verdict_gap(self.DONE % ("headless-one", "통과") + "\n")
        self.assertIsNotNone(gap)
        self.assertIn("표 머리", gap)

    def test_broken_column_shape_is_reported(self):
        # 열이 하나 사라지면 `VERDICT_ROW` 는 그 행을 조용히 건너뛴다 — 침묵이 아니라
        # 실패로 신고한다(계획서 8절의 위험).
        gap = verdict_gap(self.index("| plan_short-one | 완료 | loop/x | 1/1 |"))
        self.assertIsNotNone(gap)
        self.assertIn("열", gap)


def live_doc_names(docs=DOCS):
    """아카이브가 아닌 `plan_*.md`·`design_*.md` 의 이름. `archive_gap` 의 모집단이다.

    **설계 문서를 함께 담는 것이 2026-10-27 반복 763 의 수정이다** — 전에는 계획서만
    담아서 `archive_gap` 이 4절의 절반만 셌다(경위는 그 함수 주석).

    **`docs` 를 인자로 받는 것은 `read_budget_sizes`·`doc_citation_sites` 와 같은 이유다** —
    픽스처가 **순회를 밟아야** 한다. 실물은 치우고 나면 초록이라 모집단을 좁히는 변이가
    조용히 산다: 이 자를 세운 반복에서 **변이 ⓘ(설계 glob 삭제)가 실제로 살아남았다**
    (`archive_gap` 의 갈래는 집합을 직접 받으므로 이 함수를 안 밟는다).
    """
    return {p.name for p in docs.glob("plan_*.md") if not ARCHIVE.match(p.name)} | {
        p.name for p in docs.glob("design_*.md") if not ARCHIVE.match(p.name)}


class ArchiveBacklogTest(unittest.TestCase):
    """완료한 계획서가 `docs/` 에 그대로 남아 있나 — `docs.md` 4절의 자.

    **판정은 `archive_gap` 이 한다** — 갈래를 실물 없이 밟는 것은 `ArchiveGapTest` 다.
    """

    def test_done_plans_are_archived(self):
        gap = archive_gap((DOCS / "index.md").read_text(encoding="utf-8"),
                          live_doc_names())
        self.assertIsNone(gap, gap)

    def test_the_population_carries_both_kinds(self):
        """모집단이 계획서와 설계를 **둘 다** 담고 아카이브는 뺀다.

        **실물로는 못 재는 축이다** — 치운 트리에서는 설계 glob 을 지워도 초록이라
        변이 ⓘ 가 살아남았다(실측). 합성 트리로 순회를 직접 밟는다.
        """
        with tempfile.TemporaryDirectory() as tmp:
            docs = pathlib.Path(tmp)
            for name in ("plan_%s.md" % "alive-plan", "design_%s.md" % "alive-design",
                         "plan_history_001.md", "design_history_001.md", "note.md"):
                (docs / name).write_text("x", encoding="utf-8")
            self.assertEqual(
                {"plan_%s.md" % "alive-plan", "design_%s.md" % "alive-design"},
                live_doc_names(docs),
                "모집단이 틀렸다 — 설계를 빠뜨렸거나 아카이브를 담았다")

    def test_the_scan_still_reaches_docs(self):
        # 살아 있는 계획서는 **0개가 정상**이라(전부 치운 밤) 그쪽에 하한을 박으면
        # 거짓 RED 다. 경로가 섰다는 증거는 **아카이브 쪽**에서 받는다 — 늘기만 한다.
        archived = [p.name for p in DOCS.glob("plan_history_[0-9]*.md")]
        self.assertGreaterEqual(
            len(archived), 60,
            "계획 아카이브가 %d개로 줄었다 — 경로가 틀렸다: %s" % (len(archived), DOCS))


class IsDoneTest(unittest.TestCase):
    """상태 칸 어휘 술어. **다섯 자가 이것을 공유하므로 갈래를 여기서 전부 밟는다.**

    계획 124 가 `archive_gap` 만 손으로 넓혔더니 **나머지 넷이 리터럴로 남아** 갈렸다 —
    백지 패스(별도 세션)가 실측으로 둘을 들고 왔다: `verdict_gap` 이 실물 `완료(…)` 2행에
    **조용**했고(e2e 칸 검사가 꺼졌다), 접두만으로는 `완료 예정` 류 넷이 **완료로 읽혀**
    안 끝난 계획의 문서를 치우라고 요구했다. 술어 하나로 모으고 양쪽을 여기서 못박는다.
    """

    # 실물에 있는 두 꼴 — `index.md` 에서 글자 그대로 가져왔다(상상한 꼴이 아니다).
    REAL = ("완료", "완료(2026-10-26 게이트 ⑱ ㉢ 으로 해제 · 병합)")

    def test_the_real_forms_are_done(self):
        for cell in self.REAL:
            with self.subTest(cell=cell):
                self.assertTrue(is_done(cell))

    def test_bold_and_inner_space_are_stripped(self):
        # `**보류**` 가 실물이라 `**완료**` 는 내일 쓰일 꼴이고, 같은 손이 `** 완료 **` 도 만든다.
        for cell in ("**완료**", "** 완료 **", "  완료  "):
            with self.subTest(cell=cell):
                self.assertTrue(is_done(cell))

    def test_a_separator_may_follow(self):
        # 이 저장소는 `·` 를 구분자로 일상으로 쓴다 — 거절하면 새 침묵이 된다.
        self.assertTrue(is_done("완료 · 2026-10-26 병합"))

    def test_done_followed_by_a_word_is_not_done(self):
        """**오탐 축** — 접두만 보면 넷 다 완료로 읽혀 **안 끝난 계획**을 치우라고 요구한다.

        그러면 중복 방지(`discover.md` 5절)가 승인 대기 계획을 못 보고 밤새 다시 만든다 —
        `archive_gap` docstring 이 스스로 경고한 피해다.
        """
        for cell in ("완료 예정", "완료 예정(2026-11-02)", "완료 대기", "완료 안 됨"):
            with self.subTest(cell=cell):
                self.assertFalse(is_done(cell), "%r 을 완료로 읽었다" % cell)

    def test_the_other_three_words_are_not_done(self):
        # `index.md` 머리가 고정한 어휘 넷 중 나머지 셋 + 실물 꼴.
        for cell in ("진행", "보류(패치)", "**보류**", "폐기", "미완료", ""):
            with self.subTest(cell=cell):
                self.assertFalse(is_done(cell))


class SiblingDoneReadersTest(unittest.TestCase):
    """**같은 칸을 읽는 자 다섯이 같은 술어를 쓰나.** 백지 패스가 들고 온 축이다.

    계획 124 가 `archive_gap` 하나만 고친 결과 `verdict_gap` 은 실물 2행에서 **꺼져**
    있었고 `false_strike` 는 분기가 거꾸로라 그 2행에 **거짓 양성**을 낼 자리였다.
    호출부를 다섯 번 패치하는 것보다 공유 지점 하나가 작다(ponytail 근본 원인).
    """

    HEAD = "# 색인\n\n| 계획 | 상태 | 브랜치 | 스텝 | e2e | 비고 |\n"
    ANNOT = "완료(2026-10-26 게이트 ⑱ ㉢ 으로 해제 · 병합)"

    def test_verdict_gap_reads_annotated_done(self):
        # e2e 칸이 **날짜뿐**인 꼴은 신고 대상이다. 상태 칸에 주석이 붙었다고 그 검사가
        # 꺼지면 안 된다 — 실물 2행에서 실제로 꺼져 있었다.
        for cell in ("완료", self.ANNOT, "**완료**"):
            with self.subTest(cell=cell):
                idx = self.HEAD + ("| plan_%s | %s | loop/x | 1/1 | 2026-10-26 | 설명 |\n"
                                   % ("verdict-x", cell))
                self.assertIsNotNone(verdict_gap(idx), "%r 에서 e2e 칸 검사가 꺼졌다" % cell)

    def test_verdict_gap_still_skips_the_unfinished(self):
        idx = self.HEAD + "| plan_%s | 진행 | loop/x | 1/1 | 2026-10-26 | 설명 |\n" % "verdict-y"
        self.assertIsNone(verdict_gap(idx))


class ArchiveGapTest(unittest.TestCase):
    """`archive_gap` 의 갈래. 실물은 `ArchiveBacklogTest` 가 부른다.

    실물은 치우고 나면 초록이라 갈래가 한 번씩만 지나간다. 특히 **오탐 축**(보류 행)은
    자를 「완료」에 안 매고 세웠을 때만 물리므로 여기서 못을 박는다 — 보류본을 치우면
    중복 방지(`discover.md` 5절)가 승인 대기 중인 계획을 못 보고 밤새 다시 만든다.
    """

    DONE = "| plan_%s | 완료 | loop/x | 1/1 | 통과 | 설명 |"
    HELD = "| plan_%s | 보류(패치) | loop/x | 2/2 | (미개설) | 설명 |"

    def index(self, *rows):
        head = "# 색인\n\n| 계획 | 상태 | 브랜치 | 스텝 | e2e | 비고 |\n"
        return head + "\n".join(rows) + "\n"

    def test_archived_plan_is_quiet(self):
        self.assertIsNone(archive_gap(self.index(self.DONE % "gone-one"), set()))

    # 픽스처 이름은 **조립한다** — 리터럴로 박으면 `citation_sites` 가 제 픽스처를 물어
    # 검사가 자기 때문에 영원히 빨갛다 (`docs/design_history_083.md` 계약).
    def test_live_done_plan_is_a_gap(self):
        gap = archive_gap(self.index(self.DONE % "stayed-one"),
                          {"plan_%s.md" % "stayed-one"})
        self.assertIsNotNone(gap)
        self.assertIn("stayed-one", gap)

    def test_held_plan_stays_put(self):
        # 오탐 축 — `보류` 는 승인에 막힌 것이라 제자리가 맞다.
        self.assertIsNone(archive_gap(self.index(self.HELD % "waiting-one"),
                                      {"plan_%s.md" % "waiting-one"}))

    def test_live_done_design_is_a_gap(self):
        # **설계 축은 2026-10-27 까지 재는 자가 0개였다.** `docs.md` 4절은 계획서와 같은 숨에
        # `design_<slug>.md` → `design_history_<NNN>.md` 를 요구하는데 자는 계획서만 봤고,
        # `design_history_095.md` 가 그 침묵의 실물이었다(계획서는 2026-10-20 에
        # 치워졌는데 설계 문서만 이레를 남았다). `digest ## 반복 실패` 의 「절차를 문서에만
        # 적고 재는 자를 안 만든다」가 센 2회 중 **한 번이 바로 설계 문서**였다(계획 80).
        gap = archive_gap(self.index(self.DONE % "designed-one"),
                          {"design_%s.md" % "designed-one"})
        self.assertIsNotNone(gap, "완료 계획의 설계 문서가 살아 있는데 조용하다")
        self.assertIn("designed-one", gap)
        self.assertIn("design", gap, "계획서가 아니라 설계 문서라는 것을 안 댔다")

    def test_a_plan_without_a_design_doc_is_quiet(self):
        # **오탐 축 — 이것이 없으면 설계를 생략한 계획 전부가 거짓 RED 다.**
        # `docs.md` 4절이 「설계를 건너뛰면 없다」를 명시하고, 이 저장소 실물에서 설계
        # 문서가 없는 완료 계획이 다수다(계획 123 이 바로 그 꼴이다 — 트리거에 안 걸렸다).
        self.assertIsNone(archive_gap(self.index(self.DONE % "no-design-one"), set()))

    def test_held_plan_keeps_its_design_doc(self):
        # 보류는 계획서도 설계도 제자리가 맞다 — 승인 대기 중에 설계를 치우면 재개할 때
        # 「왜 이렇게 만들었나」의 유일한 기록이 아카이브로 흩어진다(4절).
        self.assertIsNone(archive_gap(
            self.index(self.HELD % "waiting-design"),
            {"plan_%s.md" % "waiting-design", "design_%s.md" % "waiting-design"}))

    def test_both_living_docs_are_named(self):
        # 계획서와 설계가 **둘 다** 남은 꼴. **자는 먼저 걸린 하나만 돌려준다** — 치우고
        # 다시 돌리면 다음 것이 걸린다(이 계획이 실제로 그렇게 두 반복을 썼다). 여기서
        # 고정하는 것은 「둘 다 남아도 조용하지 않다」이고, 둘을 한 번에 인쇄하라는
        # 요구는 안 한다 — `digest` 후보 `[4]` 로 등재했다.
        gap = archive_gap(self.index(self.DONE % "both-one"),
                          {"plan_%s.md" % "both-one", "design_%s.md" % "both-one"})
        self.assertIsNotNone(gap)
        self.assertIn("both-one", gap)
        # **`assertIn("plan", …)` 은 공허했다** — 설계 쪽 메시지도 `` `plan_both-one` ``
        # 조각 때문에 그 낱말을 품는다(백지 패스가 변이로 잡았다: 종류 순서를 뒤집어도
        # 983 전부 초록이었다). 메시지 **문구**로 고정한다.
        self.assertIn("완료한 plan 문서", gap, "계획서가 설계보다 먼저 걸리는 순서를 고정한다")

    def test_prefix_sharing_slug_is_not_bitten(self):
        # 이름 대조는 **완전 일치**다. `startswith` 로 넓히는 변이는 `plan_seed` 행이
        # 아직 살아 있는 `plan_seed-tier1` 계획서를 물어, 안 끝난 계획서를 치우라고 시킨다.
        self.assertIsNone(archive_gap(self.index(self.DONE % "seed"),
                                      {"plan_%s.md" % "seed-tier1"}))

    # 주석·날짜가 붙은 완료. **실물에서 조용했던 꼴이다** — 2026-10-26 에 사람이 게이트 ⑱ 을
    # ㉢ 으로 닫으면서 `index.md` 에 처음 썼고(`완료(2026-10-26 … 해제 · 병합)`), 자가
    # `!= "완료"` 로 리터럴 동일성을 봐서 **완료 계획서 둘이 살아 있는데 전수가 초록이었다.**
    ANNOTATED = "| plan_%s | 완료(2026-10-26 게이트 ⑱ ㉢ 으로 해제 · 병합) | loop/x | 1/1 | 통과 | 설명 |"

    def test_annotated_done_is_still_done(self):
        gap = archive_gap(self.index(self.ANNOTATED % "noted-one"),
                          {"plan_%s.md" % "noted-one"})
        self.assertIsNotNone(gap, "주석 달린 완료를 완료로 안 읽었다")
        self.assertIn("noted-one", gap, "어느 계획인지 안 댔다")

    def test_annotated_done_that_is_archived_is_quiet(self):
        self.assertIsNone(archive_gap(self.index(self.ANNOTATED % "noted-gone"), set()))

    def test_held_with_an_annotation_still_stays_put(self):
        # **오탐 축이 접두 판정의 대가다.** `보류(패치)` 는 이미 위에서 보지만, 접두로
        # 넓히면 「`완료` 를 **포함**하면」으로 미끄러지기 쉽고 그때 이 행이 물린다 —
        # 승인 대기 계획서를 치우면 중복 방지(`discover.md` 5절)의 눈이 먼다.
        rows = (self.HELD % "waiting-two",
                "| plan_%s | 보류(2026-10-23 · 승인 나면 완료 처리) | loop/x | 1/2 | (미개설) | 설명 |"
                % "waiting-three")
        live = {"plan_%s.md" % "waiting-two", "plan_%s.md" % "waiting-three"}
        self.assertIsNone(archive_gap(self.index(*rows), live),
                          "보류 행을 완료로 읽었다 — 산문에 `완료` 가 있어도 상태는 보류다")

    def test_bold_wrapped_done_is_still_done(self):
        # **굵게 감싸는 습관이 이 파일에 실재한다** — 살아 있는 `index.md` 의 상태 칸에
        # `**보류**` 가 있다(실측). 그래서 `**완료**` 는 내일 쓰일 수 있는 꼴이고,
        # 「값을 굵게 감싸니 재는 자가 죽었다」는 이 저장소가 이미 한 번 밟은 사고다
        # (계획 122 리뷰의 `signal_row_gap` — 빈손 밤이 안 세어졌다).
        gap = archive_gap(self.index("| plan_%s | **완료** | loop/x | 1/1 | 통과 | 설명 |"
                                     % "bold-one"), {"plan_%s.md" % "bold-one"})
        self.assertIsNotNone(gap, "굵게 감싼 완료를 완료로 안 읽었다")
        self.assertIn("bold-one", gap)

    def test_bold_wrapped_held_still_stays_put(self):
        # 굵게 풀기의 오탐 축 — 실물에 있는 바로 그 꼴이다.
        self.assertIsNone(archive_gap(
            self.index("| plan_%s | **보류** | loop/x | 1/2 | (미개설) | 설명 |" % "bold-held"),
            {"plan_%s.md" % "bold-held"}))

    def test_abandoned_is_not_read_as_done(self):
        # `index.md` 머리가 고정한 어휘 넷 중 `폐기`. 4절이 폐기본의 처분을 안 적었으므로
        # **지어내지 않는다** — 오늘 실물 0건이고, 완료로 읽으면 없는 일을 시킨다.
        self.assertIsNone(archive_gap(
            self.index("| plan_%s | 폐기 | loop/x | 1/1 | 없음 | 설명 |" % "dropped-one"),
            {"plan_%s.md" % "dropped-one"}))


class ConstGapTest(unittest.TestCase):
    """`const_gap` 의 갈래. 실물은 `ProjectConstTest` 가 부른다.

    **몸통을 함수로 뺀 이유는 `step_gap`·`strike_gap`·`verdict_gap` 과 같다** —
    실물 `project.md` 는 고치고 나면 늘 맞아서, 판정을 무력화하는 변이가 조용히 산다.

    살아 있는 상수(`indexer.MAX_PASSAGE_TAGS`)를 일부러 쓴다. 가짜 이름으로만 재면
    **인용을 해석하는 배선**은 재도 **코드에서 값을 읽어 오는 배선**은 안 재게 된다.
    """

    def test_agreeing_citation_is_quiet(self):
        self.assertIsNone(const_gap("`indexer.MAX_PASSAGE_TAGS` **= 3,000** 태그"))

    def test_stale_value_is_reported(self):
        gap = const_gap("`indexer.MAX_PASSAGE_TAGS` **= 35,000자**가 자른다")
        self.assertIsNotNone(gap)
        self.assertIn("MAX_PASSAGE_TAGS", gap)
        self.assertIn("3000", gap.replace(",", ""))

    def test_citation_without_a_number_is_not_bitten(self):
        # 실물 두 꼴이다. 값을 안 적은 인용까지 물면 문서가 상수를 못 부른다.
        self.assertIsNone(const_gap("`design_check.PAIRS` 에 짝을 안 적으면 종료 2 다"))
        self.assertIsNone(const_gap("`fetcher.MAX_BYTES`(2MB)까지 채운 문서 10건"))

    def test_absent_constant_is_reported_not_skipped(self):
        # **조용히 넘기면 이름을 바꾼 상수가 그대로 낡는다** — 그것이 이 검사의 절반이다.
        gap = const_gap("`indexer.PASSAGE_TAG_CAP` = 3,000")
        self.assertIsNotNone(gap)
        self.assertIn("PASSAGE_TAG_CAP", gap)

    def test_absent_module_is_reported(self):
        gap = const_gap("`nosuchmod.SOME_CAP` = 5")
        self.assertIsNotNone(gap)
        self.assertIn("nosuchmod", gap)

    def test_citation_reads_across_a_line_break(self):
        # 실물이 이 꼴이다 — 백틱과 `**=` 사이에 줄바꿈과 들여쓰기가 들어간다.
        self.assertIsNone(const_gap(
            "  - `indexer.MAX_PASSAGE_TAGS`\n    **= 3,000 태그**가 자른다"))

    def test_underscore_literal_in_source_is_read(self):
        # 코드는 `3_000`, 문서는 `3,000` 이다. 두 표기를 같은 수로 못 읽으면
        # 검사가 매번 거짓으로 빨개져 아무도 안 믿게 된다.
        self.assertIsNone(const_gap("`indexer.MAX_PASSAGE_HTML` = 2,000,000"))


class ProjectConstTest(unittest.TestCase):
    """살아 있는 문서가 인용한 상수가 오늘의 코드와 같은지 본다 — `project.md` 와 `baselines.md`.

    **이 검사가 있는 이유는 그 자리가 세 번 낡았기 때문이다** — 계획 57·58 은
    `project.md` 의 캡 문단을 손으로 맞췄고(`e6f375c` 「기록 자리 둘을 오늘 값으로
    맞춘다」) 계획 74 는 자를 바이트에서 태그로 갈면서 코드와 `test_indexer.py` 만
    고치고 문서를 잊었다. `MAX_PASSAGE_HTML` **= 35,000자**라고 적힌 채 실제 값은
    2,000,000 이었다.

    **`project.md` 는 루프가 매 반복 읽는 네 파일 중 하나**이고 「품질 기준」 절이
    판단의 눈금이다. 거짓 눈금은 코드 버그처럼 터지지 않고 **판단에 조용히 든다** —
    소스만 보는 테스트로는 영원히 안 잡힌다(`DocCitationTest` 와 같은 부류다).

    **계획 97 이 그 눈금의 절반을 `baselines.md` 로 옮겼다** — 예산 밖이라 매 반복
    읽히지는 않지만, 낡으면 「실제로 그 도구를 쓰는 반복」이 거짓 눈금을 든다.
    """

    def test_project_cites_live_constants(self):
        # `baselines.md` 도 문다 — **이 검사가 사는 이유인 「세 번 낡은 그 자리」(캡 설계
        # 논증)가 계획 97 에서 그 파일로 이사했다.** 오늘은 같은 상수가 두 파일에 다 남아
        # 우연히 덮이지만, `project.md` 를 더 줄여 포인터 한 줄로 바꾸면 조용해진다.
        # FLOOR 못은 아래대로 `project.md` 에만 둔다 — 예산 밖 파일은 인용 0건이 정상이다.
        for name in ("project.md", "baselines.md"):
            with self.subTest(doc=name):
                gap = const_gap((DOCS / name).read_text(encoding="utf-8"), name)
                self.assertIsNone(gap, gap)

    def test_project_still_cites_at_least_one_constant(self):
        # 위 단언은 인용이 0건이면 «볼 것이 없어» 초록이다. 못을 박아 둔다 —
        # 캡 문단을 `= 숫자` 없이 다시 쓰면 검사가 아무것도 안 재면서 통과한다.
        found = CONST_CITATION.findall((DOCS / "project.md").read_text(encoding="utf-8"))
        self.assertGreaterEqual(
            len(found), CONST_CITATION_FLOOR,
            "project.md 가 값까지 적어 부르는 상수가 %d개다 — 「품질 기준」 절이"
            " `mod.CONST` **= 숫자** 꼴을 잃었고, 그러면 이 검사는 아무것도 안 잰다"
            % len(found))


class E2eRosterGapTest(unittest.TestCase):
    """`e2e_roster_gap` 의 갈래. 실물은 `E2eRosterTest` 가 부른다.

    **몸통을 함수로 뺀 이유는 `const_gap`·`step_gap`·`cap_gap` 과 같다** — 실물
    `project.md` 는 한 번 맞추고 나면 늘 맞아서, 판정을 무력화하는 변이가 조용히 산다.

    모집단이 디스크라 픽스처가 이름을 **지어낼 수 없다** — 살아 있는 e2e 이름을 쓴다.
    """

    def _all_but(self, *drop):
        return " ".join(p.stem for p in E2E_DIR.glob("*.py") if p.stem not in drop)

    def test_a_full_roster_is_quiet(self):
        self.assertIsNone(e2e_roster_gap(self._all_but()))

    def test_a_missing_name_is_reported(self):
        gap = e2e_roster_gap(self._all_but("recrawl_e2e"))
        self.assertIsNotNone(gap)
        self.assertIn("recrawl_e2e", gap)

    def test_every_missing_name_is_listed_not_just_the_first(self):
        # 한 이름만 찍으면 다음 반복이 나머지를 모른 채 초록으로 읽는다.
        gap = e2e_roster_gap(self._all_but("recrawl_e2e", "url_normalize_e2e"))
        self.assertIn("recrawl_e2e", gap)
        self.assertIn("url_normalize_e2e", gap)
        # 이름 순서는 `glob` 이 아니라 `sorted` 가 정한다 — 디렉터리 순회 순서에 맡기면
        # 같은 결함이 실행마다 다른 줄을 내고 두 RED 를 눈으로 못 맞춘다.
        self.assertLess(gap.index("recrawl_e2e"), gap.index("url_normalize_e2e"))

    def test_the_message_names_the_document_it_was_given(self):
        # **`doc` 은 이 저장소가 이미 한 번 밟은 자리다** — `const_gap` 이 파일명을
        # 안 받던 시절 `baselines.md` 의 오류를 「project.md 가」로 귀속했다([R568-2]).
        # 부르는 문서가 하나뿐인 오늘은 기본값이 우연히 맞아 아무도 이 축을 안 밟는다.
        gap = e2e_roster_gap(self._all_but("recrawl_e2e"), doc="README.md")
        self.assertIn("README.md", gap)
        self.assertNotIn("project.md", gap)

    def test_a_substring_is_not_a_listing(self):
        # **이 저장소의 실제 함정이다** — `interrupt_e2e` 는 `indexer_interrupt_e2e`
        # 의 부분 문자열이라, 부분 문자열로 세는 자는 뒤엣것만 적힌 명부를 통과시킨다.
        gap = e2e_roster_gap(self._all_but("interrupt_e2e"))
        self.assertIsNotNone(gap, "부분 문자열을 등재로 세고 있다")
        self.assertIn("interrupt_e2e", gap)


class E2eRosterTest(unittest.TestCase):
    """살아 있는 `project.md` 가 `e2e/*.py` 를 전부 이름으로 부르는지 본다.

    **이 검사가 있는 이유는 실물이 이미 그 상태였기 때문이다** — 2026-09-13 반복 570
    실측에서 22개 중 다섯(`crawl_politeness_e2e`·`pagination_ui_e2e`·`recrawl_e2e`·
    `retry_interval_e2e`·`url_normalize_e2e`)이 어느 문서에도 이름이 없었고, **다섯 다
    rc=0 으로 멀쩡히 도는 e2e** 였다. `project.md` 는 「13종」이라 적고 13만 나열했고
    `README.md` 는 `ls e2e/*.py` 로 **세기만 하고 이름을 안 줬다.**

    **세는 것과 부르는 것은 다르다.** 루프는 매 반복 `project.md` 를 읽어 무엇을 칠지
    정하므로, 숫자만 맞는 명부는 다섯을 영원히 안 돌린다 — 전수 763건이 그 상태로
    전부 초록이었다(`DocCitationTest`·`ProjectConstTest` 와 같은 부류의 눈먼 자리다).
    """

    def test_project_names_every_e2e(self):
        gap = e2e_roster_gap((DOCS / "project.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)

    def test_there_is_something_to_count(self):
        # 위 단언은 `e2e/*.py` 가 0개면 «볼 것이 없어» 초록이다. 경로가 어긋나거나
        # 디렉터리가 비면 이 검사는 아무것도 안 재면서 통과한다.
        found = list(E2E_DIR.glob("*.py"))
        self.assertGreaterEqual(
            len(found), E2E_ROSTER_FLOOR,
            "`e2e/*.py` 가 %d개다 — 모집단이 비어 이 검사는 아무것도 안 잰다" % len(found))


class E2eLabelGapTest(unittest.TestCase):
    """`e2e_label_gap` 의 갈래. 실물은 `E2eLabelTest` 가 부른다.

    **픽스처가 이름을 지어낼 수 없다** — 유령 판정이 디스크를 보므로, 「정상」 픽스처는
    살아 있는 e2e 이름으로 조립한다(`E2eRosterGapTest` 와 같은 이유).
    """

    def _item(self, names, label=None):
        live = [p.stem for p in sorted(E2E_DIR.glob("*.py"))][:3]
        names = live if names is None else names
        if label is None:
            label = len(names)
        return ("- **e2e %d종**: `PYTHONPATH=src python3 e2e/<이름>.py` — %s.\n"
                "  명부가 낡으면 `test_docs.py` 가 문다 · 나머지는 `docs/baselines.md`\n"
                "- **측정**: `e2e/perf_crawl.py`\n"
                % (label, " ".join("`%s`" % n for n in names)))

    def test_a_true_roster_is_quiet(self):
        self.assertIsNone(e2e_label_gap(self._item(None)))

    def test_a_name_without_a_file_is_reported(self):
        # 2026-09-13 반복 574 가 실제로 밟은 모양 — 사람용 포인터가 이름 자리에 섰다.
        gap = e2e_label_gap(self._item(["crawl_e2e", "E2eRosterTest"], label=2))
        self.assertIsNotNone(gap, "유령을 등재로 세고 있다")
        self.assertIn("E2eRosterTest", gap)

    def test_a_dotted_token_is_not_a_name(self):
        # **574 의 수정이 기댄 성질이다** — 포인터를 `test_docs.py` 로 바꿔 닫았다.
        # 이 자가 점 든 토큰을 이름으로 세기 시작하면 그 수정이 도로 유령이 된다.
        # 위 `_item` 이 본문에 `test_docs.py`·`docs/baselines.md`·명령 토큰을 이미 들고 있다.
        # **라벨을 1 로 조여 센다**(반복 578 리뷰 [R99-1]) — 위 「정상」 픽스처와 같은
        # 호출을 두 번 하면 축이 하나 늘어난 척만 하고 실제로 재는 것은 같아진다.
        self.assertIsNone(e2e_label_gap(self._item(["crawl_e2e"], label=1)))

    def test_a_stale_label_is_reported_with_both_numbers(self):
        # 한쪽 수만 찍으면 어느 쪽을 고칠지 모른 채 문서를 틀리게 맞추게 된다.
        gap = e2e_label_gap(self._item(["crawl_e2e", "recrawl_e2e"], label=7))
        self.assertIsNotNone(gap, "라벨과 이름 수가 갈렸는데 조용하다")
        self.assertIn("7", gap)
        self.assertIn("2", gap)

    def test_a_ghost_is_reported_before_a_stale_label(self):
        # 유령이 들어오면 라벨도 함께 어긋나는데, 먼저 말해야 하는 원인은 유령이다
        # (라벨을 고치면 유령이 합법이 된다 — 자를 통과시키려고 자를 깎는 길).
        gap = e2e_label_gap(self._item(["crawl_e2e", "E2eRosterTest"], label=1))
        self.assertIn("E2eRosterTest", gap)

    def test_a_missing_item_is_reported(self):
        # 앵커가 드리프트하면 이름이 0개가 되고, 그 상태의 조용한 초록이 가장 나쁘다.
        gap = e2e_label_gap("# 프로젝트 정보\n\n- **측정**: `e2e/perf_crawl.py`\n")
        self.assertIsNotNone(gap, "명부 항목이 없는데 조용하다")
        self.assertIn("e2e N종", gap)

    def test_an_emptied_roster_is_quiet_here_and_loud_next_door(self):
        # 이 자의 **유일한 구멍**이다(반복 577 변이 탐색) — 이름 0개에 라벨 0 이면
        # 0 == 0 이라 조용하다. 막는 것은 이쪽에 못을 하나 더 박는 것이 아니라
        # **모집단이 디스크인 형제**다. 둘이 서로를 대체하지 않는다는 주장이
        # 주석에만 있으면 한쪽을 지우는 날 아무도 안 센다 — 그래서 여기서 잰다.
        emptied = self._item([], label=0)
        self.assertIsNone(e2e_label_gap(emptied))
        self.assertIsNotNone(e2e_roster_gap(emptied), "명부를 비웠는데 둘 다 조용하다")

    def test_the_message_names_the_document_it_was_given(self):
        # `doc` 이 **죽은 칸**이 되는 것은 이 저장소가 두 번 밟은 자리다
        # ([R568-2] · 계획 98 테스트 phase 의 변이 M9 가 살아남았던 그 축).
        gap = e2e_label_gap(self._item(["E2eRosterTest"], label=1), doc="README.md")
        self.assertIn("README.md", gap)
        self.assertNotIn("project.md", gap)


class E2eLabelTest(unittest.TestCase):
    """살아 있는 `project.md` 의 명부 줄이 **그대로 실행 가능한지** 본다.

    `E2eRosterTest` 와 방향이 반대다 — 그쪽은 「빠진 이름」, 이쪽은 「없는 이름」과
    「낡은 라벨」이다. 2026-09-13 계획 98 e2e 가 이 항목을 기계로 읽어 조립해 돌렸고
    첫 판이 유령 하나 때문에 `rc=2` 로 죽었다. 그때 고친 것은 문서였고, **같은 편집이
    내일 다시 통과하는 것**을 막는 자가 이것이다.
    """

    def test_project_roster_names_are_all_runnable(self):
        gap = e2e_label_gap((DOCS / "project.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)


class CapGapTest(unittest.TestCase):
    """`cap_gap` 의 갈래. 실물은 `HistoryCapTest` 가 부른다.

    **몸통을 함수로 뺀 이유는 `iter_gap`·`step_gap`·`const_gap` 과 같다** — 실물
    `history_current.md` 는 회전하고 나면 늘 상한 안이라, 판정을 무력화하는 변이가
    조용히 산다(오늘 회전 직후 148줄·6회).
    """

    def _text(self, entries, filler=0):
        body = "".join("### 반복 %d — 무엇\n- 한 일\n" % (400 + i) for i in range(entries))
        return body + "\n" * filler

    def test_inside_the_caps_is_quiet(self):
        self.assertIsNone(cap_gap(self._text(6)))

    # **축 이름은 통째로 단언한다.** `"줄"`·`"항목"` 만 보면 **처방 문장이 그 단언을
    # 만족시킨다** — 처방이 「오래된 **항목**부터 ... 한 **줄**로 압축한다」이기 때문이다
    # (반복 444 실측: 항목 축만 넘긴 메시지에도 `"줄"` 이 들어 있었다). 이름만 읽으면
    # 축을 보는 것 같은데 실제로는 아무 메시지나 통과하던 단언이다.
    def test_too_many_lines_is_reported(self):
        gap = cap_gap(self._text(2, filler=HISTORY_LINE_CAP))
        self.assertIsNotNone(gap)
        self.assertIn("줄 수 %d > %d" % (HISTORY_LINE_CAP + 4, HISTORY_LINE_CAP), gap)
        self.assertNotIn("항목 수", gap)

    def test_too_many_entries_is_reported_on_its_own(self):
        # 줄 수는 여유가 있는데 항목만 넘는 꼴 — 축 하나가 단독으로 물어야 한다.
        gap = cap_gap(self._text(HISTORY_ENTRY_CAP + 1))
        self.assertIsNotNone(gap)
        self.assertIn("항목 수 %d > %d" % (HISTORY_ENTRY_CAP + 1, HISTORY_ENTRY_CAP), gap)
        self.assertNotIn("줄 수", gap)

    def test_both_axes_are_reported_together(self):
        gap = cap_gap(self._text(HISTORY_ENTRY_CAP + 1, filler=HISTORY_LINE_CAP))
        self.assertIn("줄 수", gap)
        self.assertIn("항목 수", gap)

    def test_the_boundary_is_not_over(self):
        # 룰 문구가 「넘으면」이다. 정확히 상한인 날 회전을 강요하면 거짓 RED 다.
        self.assertIsNone(cap_gap("\n" * HISTORY_LINE_CAP))
        self.assertIsNone(cap_gap(self._text(HISTORY_ENTRY_CAP)))

    def test_only_entry_heads_are_counted(self):
        # 본문이 「반복 439」를 언급해도 항목이 아니다 — 세는 것은 `### 반복` 머리다.
        # **줄 중간의 인용도 항목이 아니다** — 이 저장소의 기록은 머리 문구를 그대로
        # 인용하는 습관이 있고(실측: 오늘 `history_current.md` 에 2줄), `^` 앵커를
        # 지운 변이는 그것을 항목으로 세어 **거짓 RED** 를 만든다. 앵커를 물리는
        # 픽스처가 이 두 줄이다 (`IterationPatternTest` 가 같은 자리에서 배운 것).
        body = (self._text(3) + "- 반복 439 에서 쟀다\n" * 30
                + "- 머리 문구를 `### 반복 439` 로 적어 뒀다\n" * 30)
        self.assertIsNone(cap_gap(body))


class HistoryCapTest(unittest.TestCase):
    """살아 있는 `history_current.md` 가 `rules/docs.md` 3절의 상한 안인가.

    **이 검사가 있는 이유는 그 상한을 지키는 것이 사람의 기억뿐이었기 때문이다** —
    계획 72 반복 419(352줄)와 반복 440(383줄·20회) 두 번 놓쳤고, 두 번째는 **줄 수를
    83줄 넘긴 채** 여섯 반복을 지나갔다. 전수 664건이 그동안 조용했다.
    **항목 축 20 은 정확히 상한이라 그날도 조용한 것이 맞다**(반복 446 e2e 실측 —
    회전 직전을 되살려 먹이니 문 것은 줄 수 축 하나였다). 두 축을 다 두는 이유는
    반대 꼴(짧은 반복이 스물한 번 쌓이는 날)이 같은 비용을 내기 때문이다.

    처방은 **아카이브로 밀어내기**(`history_<NNN>.md`)라 야간 루프가 스스로 실행할 수
    있다 — 그래서 이 못은 루프를 교착시키지 않는다. `digest.md` 200 이 여기 없는 이유는
    그 반대다(처방이 삭제 · 계획 76 「하지 않을 것」).
    """

    def test_live_history_is_within_the_caps(self):
        gap = cap_gap((DOCS / "history_current.md").read_text(encoding="utf-8"))
        self.assertIsNone(gap, gap)

    def test_live_history_still_has_entries_to_count(self):
        # 위 단언은 항목이 0건이어도 «넘긴 것이 없어» 초록이다. 파일이 비거나 머리
        # 문구가 `## 반복` 로 드리프트하면 항목 축은 아무것도 안 재면서 통과한다.
        # 못은 **오늘 값(9)에 안 붙인다** — 회전 직후에는 항목이 몇 개든 정당하다
        # (`CONST_CITATION_FLOOR`·`VERDICT_ROW_FLOOR` 과 같은 이유).
        found = HISTORY_ENTRY_HEAD.findall(
            (DOCS / "history_current.md").read_text(encoding="utf-8"))
        self.assertGreaterEqual(
            len(found), HISTORY_ENTRY_FLOOR,
            "history_current.md 의 `### 반복` 항목이 %d개다 — 파일이 비었거나 항목 머리"
            " 문구가 바뀌었고, 그러면 항목 축은 아무것도 안 잰다" % len(found))


class ReadBudgetGapTest(unittest.TestCase):
    """`read_budget_gap` 이 무는 것과 안 무는 것을 픽스처로 고정한다."""

    def _sizes(self, status, project, history, plan=None):
        sizes = [("status.md", status, 50), ("project.md", project, 60),
                 ("history_current.md", history, 300)]
        if plan is not None:
            sizes.append(("plan_%s.md" % "x", plan, 80))
        return sizes

    def test_under_the_cap_is_silent(self):
        self.assertIsNone(read_budget_gap(self._sizes(50, 60, 300, 80)))

    def test_exactly_the_cap_is_silent(self):
        # 경계는 초과가 아니다 — 룰 문구가 「넘으면」이다. 그날 접기를 강요하면
        # 거짓 RED 고, 다음 append 가 어차피 문다 (`CapGapTest` 와 같은 판단).
        self.assertIsNone(read_budget_gap(self._sizes(100, 100, 300, 100)))

    def test_one_line_over_the_cap_bites(self):
        gap = read_budget_gap(self._sizes(100, 100, 300, 101))
        self.assertIsNotNone(gap)
        self.assertIn("합계 601 > 600", gap)

    def test_the_message_prints_every_file_with_its_own_cap(self):
        # 합계만 알려주면 사람이 어느 파일을 볼지 모른다. 이 단언이 없으면 내역을
        # 빼는 변이가 살아남는다.
        gap = read_budget_gap(self._sizes(299, 63, 241, 100))
        for expected in ("status.md 299/50", "project.md 63/60",
                         "history_current.md 241/300", "plan_%s.md 100/80" % "x"):
            self.assertIn(expected, gap)

    def test_a_file_over_its_own_cap_is_silent_while_the_sum_fits(self):
        # **이 자의 설계 결정 자체가 여기 걸려 있다.** status.md 가 제 상한 50 의
        # 여섯 배여도 합이 600 안이면 안 문다 — 처방이 사람 판단이라 야간이 스스로
        # 못 푸는 못이 되기 때문이다. 파일별을 단언으로 승격하는 변이는 여기서 죽는다.
        self.assertIsNone(read_budget_gap(self._sizes(299, 60, 200, 40)))

    def test_no_active_plan_counts_three_files(self):
        # DONE 인 날은 읽을 계획이 없다. 없는 계획을 80 으로 쳐서 무는 변이가 여기서 죽는다.
        self.assertIsNone(read_budget_gap(self._sizes(250, 250, 100)))


class ReadBudgetRosterTest(unittest.TestCase):
    """명부와 파일별 상한을 `rules/docs.md` 1절 그대로 못박는다.

    **명부에 하한이 없으면 자가 제 입력을 줄여 초록이 된다** — 실측(반복 612 변이 M7):
    `READ_BUDGET_FILES` 에서 `status.md` 한 줄을 빼면 합계에서 180줄이 조용히 사라지고
    전수 112건이 **그대로 OK** 였다. 오늘 예산을 넘긴 바로 그 파일이 빠지는 변이다.
    파일별 상한(50/60/300/80)도 같이 못박는다 — 단언에는 안 쓰이지만 **실패 메시지가
    사람에게 인쇄하는 수**라, 틀리면 어느 파일을 볼지를 틀리게 알려준다(M8·M9 도 살았다).

    룰 파일은 저장소 밖(`~/.claude/skills/loop-harness`)이라 대조할 원본을 임포트할 수
    없다. 그래서 **값을 그대로 적어 고정**한다 — 룰이 바뀌면 이 줄이 빨개지고, 그때
    사람이 두 곳을 같이 고친다 (`E2E_ROSTER_FLOOR`·`CONST_CITATION_FLOOR` 과 같은 자리).
    """

    def test_the_roster_is_the_four_files_the_rule_names(self):
        self.assertEqual(
            READ_BUDGET_FILES,
            (("status.md", 50), ("project.md", 60), ("history_current.md", 300)))
        self.assertEqual(READ_BUDGET_PLAN_CAP, 80)


class ReadBudgetSizesTest(unittest.TestCase):
    """`read_budget_sizes` 의 세 갈래를 픽스처로 밟는다.

    살아 있는 트리는 「계획을 가리키고 그 파일도 있다」 한 갈래뿐이다 — 나머지 둘은
    여기서만 밟힌다.
    """

    def _docs(self, tmp, plan_line, make_plan):
        docs = pathlib.Path(tmp)
        (docs / "status.md").write_text("---\n%s\n---\n" % plan_line, encoding="utf-8")
        (docs / "project.md").write_text("a\nb\n", encoding="utf-8")
        (docs / "history_current.md").write_text("c\n", encoding="utf-8")
        if make_plan:
            (docs / ("plan_%s.md" % "x")).write_text("d\ne\nf\n", encoding="utf-8")
        return docs

    def test_an_active_plan_with_a_file_is_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            sizes = read_budget_sizes(self._docs(tmp, "plan: x", True))
        self.assertEqual(sizes[-1], ("plan_%s.md" % "x", 3, READ_BUDGET_PLAN_CAP))

    def test_an_active_plan_without_a_file_is_not_counted(self):
        # 아카이브 직후 `status.md` 가 아직 옛 슬러그를 가리키는 날이 있다. 없는
        # 파일을 80 으로 치면 없는 비용을 무는 것이다.
        with tempfile.TemporaryDirectory() as tmp:
            sizes = read_budget_sizes(self._docs(tmp, "plan: x", False))
        self.assertEqual(len(sizes), len(READ_BUDGET_FILES))

    def test_no_plan_line_is_not_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            sizes = read_budget_sizes(self._docs(tmp, "signal: DONE", False))
        self.assertEqual(len(sizes), len(READ_BUDGET_FILES))


class ReadBudgetTest(unittest.TestCase):
    """살아 있는 필수 읽기 넷이 `rules/docs.md` 1절의 총합 상한 안인가.

    **이 검사가 있는 이유는 그 상한을 지키는 것이 사람의 기억뿐이었기 때문이다** —
    저장소는 이 예산을 세 번 고쳤고(`status-read-budget` 721→448 ·
    `status-narrative-fold` 600→589 · 계획 97 `project-md-diet` 600→411) 세 번 다
    손이라 자가 안 남았다. 97 이 스스로 적어 둔 예측(「앞 둘이 되밀린 것은 밤마다
    쓰는 파일이라서다」)대로 `status.md` 가 103 → 299 로 돌아오는 동안 **전수 797건이
    조용했고**, 정작 `status.md` 본문은 「525줄/600 · 여유 75줄」이라 적고 있었다 —
    손으로 적은 수가 파일과 따로 늙는다.

    `HistoryCapTest` 가 무는 `history_current.md` 300 축은 그동안 안 넘겼다.
    **무는 자가 있는 축은 안 넘겼고, 없는 축이 넘겼다.**
    """

    def test_live_required_reading_is_within_the_budget(self):
        gap = read_budget_gap(read_budget_sizes())
        self.assertIsNone(gap, gap)

    def test_live_sizes_are_all_nonzero(self):
        # 위 단언은 파일이 비면 «합이 작아져» 더 초록이다. 넷 중 하나가 0줄이면
        # 세는 일 자체가 고장 난 것이다 (`HISTORY_ENTRY_FLOOR` 과 같은 자리).
        for name, lines, _ in read_budget_sizes():
            self.assertGreater(lines, 0, "%s 가 0줄이다 — 재는 일이 고장 났다" % name)


# ── 인용의 존재 축 (계획 109) ────────────────────────────────────────────────
# 코드가 대는 `` `plan_<이름>.md` ``·`` `design_<이름>.md` `` 는 **「실재하는 파일을
# 가리킨다」는 약속**이다. 계획을 마치면 `plan_<슬러그>.md` 가 아카이브 이름으로 옮겨
# 가는데(`rules/docs.md` 4절) 인용은 따라가지 않아 **포인터가 조용히 끊긴다** —
# 2026-09-28 실측으로 코드 안 **28자리**가 없는 파일을 가리켰고 전수 833 이 하나도 안
# 물었다. 가장 아픈 자리는 `tests/__init__.py` 다: 그 주석의 존재 이유가 「지우려는
# 사람에게 설계를 가리키는 것」이라 포인터가 끊기면 파일이 지워진다.
# **아카이브 꼴도 함께 문다** — 그쪽은 이름이 불변이라 공짜다.
# **계획 110 이 백틱 조건을 없앴다** — 109 의 자는 백틱에 든 `` `design_<이름>.md` `` 는
# 물고 같은 줄의 맨 이름은 놓쳐 **코드 인용의 41%(48/117)만** 봤고, 실제로 끊긴 65자리가 그
# 반대편에 있었다. 이제 **표기 형태를 안 본다**(`docs/design_history_083.md` 결정 A).
# 약속 밖으로 남는 것은 둘뿐이다 — `.md` 를 뗀 슬러그(과거 사례 산문이 그리로 빠진다)와
# 자리표시자 `` `plan_<슬러그>.md` ``(첫 글자가 꺾쇠라 안 걸린다). **합성 픽스처는
# 예외를 받지 않는다** — 자에 구멍을 내는 대신 픽스처 쪽이 이름을 **조립해서** 쓴다.
# 백틱이 주던 경계를 낱말 경계가 **양쪽에서** 대신한다 — 앞만 막으면
# `plan_x.mdx`·`plan_x.md_backup` 이 잘려 들어와 없는 문서로 잡힌다.
ALIVE_CITATION = re.compile(
    r"(?<![A-Za-z0-9_-])(?:docs/)?((?:plan|design)_[A-Za-z0-9][A-Za-z0-9_-]*\.md)"
    r"(?![A-Za-z0-9_-])")
# 인용이 사는 네 곳과 읽을 확장자. `docs/` 는 이 축 밖이다 — 그쪽 결손 44종은 해석
# 뿌리가 넷(저장소 루트·`docs/specs/`·`docs/e2e/<슬러그>/result.md`·저장소 밖 루프 룰)
# 으로 갈려 판정이 다르다(`docs/plan_history_084.md` 3절).
ALIVE_DIRS = ("src", "tests", "e2e", "scripts")
ALIVE_SUFFIXES = (".py", ".sh", ".js")
# 순회가 죽으면 **0건 초록**이 된다 — `CONST_CITATION_FLOOR` 과 같은 실패 유형이라 같은
# 방식으로 못을 박는다. 축을 넓힌 직후가 **117회**(백틱 안 48 + 밖 69)였고, 픽스처 9개를
# 조립 꼴로 옮긴 **오늘 실물은 108**이다(정정은 이름만 바꿔 수를 안 줄인다). 100 은
# 「아무것도 안 잰다」와 대량 삭제만 문다 — 여유가 8뿐이라 인용을 9개 걷어내면 여기가 먼저 운다.
ALIVE_CITATION_FLOOR = 100


def citation_sites(root):
    """`root` 아래 코드에서 `(경로, 줄번호, 이름)` 을 모은다.

    `root` 를 인자로 받는 것은 **픽스처가 순회를 밟기 위해서다** — 실물 트리는 네
    디렉터리가 다 살아 있는 한 갈래뿐이라 `ALIVE_DIRS` 를 줄이는 변이가 조용히 산다.
    """
    sites = []
    for name in ALIVE_DIRS:
        base = root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in ALIVE_SUFFIXES:
                continue
            for no, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
                for found in ALIVE_CITATION.finditer(line):
                    sites.append((str(path.relative_to(root)), no, found.group(1)))
    return sites


def citation_alive_gap(sites, docs):
    """실재하지 않는 문서를 가리킨 인용을 한 줄로 돌려준다. 없으면 `None`.

    재는 일(`citation_sites`)과 판정을 가른다 — `read_budget_gap` 과 같은 이유다.
    **빈 목록에서는 조용하다**: 순회가 죽은 경우를 여기서 막으면 픽스처가 「인용이
    하나도 없는 트리」를 못 만든다. 그 자리는 `ALIVE_CITATION_FLOOR` 이 실물에서 문다.
    """
    dead = ["  %s:%d — `%s`" % (path, no, name)
            for path, no, name in sites if not (docs / name).exists()]
    if not dead:
        return None
    return ("인용이 없는 문서를 가리킨다 — 아카이브된 이름으로 고치거나, 파일이 아닌"
            " 예시면 `.md` 를 떼고 슬러그로 적는다 (`docs/design_history_082.md`"
            " 계약 2). 테스트의 합성 픽스처면 셋째 길이다 — 한 리터럴에 토큰을 담지 말고"
            " 이름을 **조립**한다 (`docs/design_history_083.md` 계약):\n" + "\n".join(dead))


class CitationAlivePatternTest(unittest.TestCase):
    """`ALIVE_CITATION` 자신을 리터럴로 붙든다 — 실물 축은 자기를 못 잰다.

    **이름을 조립해서 만든다.** 픽스처를 리터럴로 박으면 `CitationAliveTest` 가 자기
    픽스처를 물어 **검사가 자기 때문에 영원히 빨갛다**(설계 계약 4번). 조립한 이름은
    백틱 안에 있어도 소스에는 조각으로만 남아 순회가 못 본다.
    """

    NAME = "%s_%s.md"
    CAUGHT = (
        "설계는 `%s` 에 있다" % (NAME % ("design", "x-slug")),
        "옮겨 간 자리는 `%s` 다" % (NAME % ("plan", "history_012")),   # 아카이브 꼴
        "경로까지 적은 꼴 `docs/%s`" % (NAME % ("design", "y-slug")),
        "| `%s` | 표 칸 안 |" % (NAME % ("plan", "z-slug")),
        "절까지 같은 백틱 `%s ## 계약`" % (NAME % ("design", "w-slug")),
        "줄까지 같은 백틱 `%s:12`" % (NAME % ("plan", "v-slug")),
        "백틱이 아예 없는 꼴 %s" % (NAME % ("plan", "q-slug")),        # 계획 110
        "경로까지 맨몸으로 docs/%s" % (NAME % ("design", "r-slug")),   # 계획 110
    )
    NOT_CAUGHT = (
        "자리표시자 `plan_<슬러그>.md`",
        "`.md` 를 뗀 슬러그 `%s`" % "recrawl",
        "다른 접두 `spec_%s`" % (NAME % ("x", "y"))[2:],
        # 뒤쪽 경계. 백틱을 버린 대가로 **양쪽**을 낱말 경계가 대신해야 하는데
        # 앞만 막으면 `.md` 로 시작하는 더 긴 이름이 잘려 들어온다 (계획 110 리뷰).
        "확장자가 더 붙은 꼴 %sx" % (NAME % ("plan", "s-slug")),
        "뒤에 낱말이 붙은 꼴 %s_backup" % (NAME % ("design", "t-slug")),
    )

    def test_pattern_catches_document_citations(self):
        for line in self.CAUGHT:
            with self.subTest(line=line):
                self.assertRegex(line, ALIVE_CITATION, "인용을 못 잡는다 — 검사가 좁아졌다")

    def test_pattern_leaves_non_citations(self):
        for line in self.NOT_CAUGHT:
            with self.subTest(line=line):
                self.assertNotRegex(line, ALIVE_CITATION, "인용이 아닌 것을 잡는다 — 오탐")


class CitationAliveGapTest(unittest.TestCase):
    """`citation_sites` 와 `citation_alive_gap` 의 갈래를 합성 트리로 밟는다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.docs = self.root / "docs"
        self.docs.mkdir()

    def code(self, rel, line):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("머리\n%s\n" % line, encoding="utf-8")

    def doc(self, name):
        (self.docs / name).write_text("# 문서\n", encoding="utf-8")

    def test_citation_to_an_existing_document_is_quiet(self):
        self.code("src/a.py", "# 근거는 `%s` 다" % ("design_%s.md" % "alive"))
        self.doc("design_%s.md" % "alive")
        self.assertIsNone(citation_alive_gap(citation_sites(self.root), self.docs))

    def test_citation_to_a_missing_document_is_a_gap(self):
        self.code("src/a.py", "# 근거는 `%s` 다" % ("design_%s.md" % "gone"))
        gap = citation_alive_gap(citation_sites(self.root), self.docs)
        self.assertIsNotNone(gap, "없는 문서를 가리키는데 조용하다")
        self.assertIn("src/a.py:2", gap, "자리를 안 알려준다 — 사람이 못 찾는다")
        self.assertIn("design_%s.md" % "gone", gap, "이름을 안 알려준다")

    def test_the_gap_message_offers_the_fixture_way_out(self):
        """설계 계약 — 고칠 **세 번째 길**을 메시지에서 읽는다.

        `tests` 가 `ALIVE_DIRS` 에 있어 이 자는 **자기 픽스처를 문다**. 그때 유일한
        해법이 이름 조립인데 메시지가 아카이브 이름과 슬러그 둘만 대면 다음 사람은
        **틀린 방향으로** 간다 (`docs/design_history_083.md` 계약 4번).
        """
        self.code("tests/t.py", "# `%s`" % ("plan_%s.md" % "fixture"))
        gap = citation_alive_gap(citation_sites(self.root), self.docs)
        self.assertIn("조립", gap, "픽스처가 이름을 조립하는 길을 안 알려준다")

    # 명부를 **리터럴로** 든다. `ALIVE_DIRS` 로 픽스처와 기대를 함께 만들면 상수를
    # 줄이는 변이가 양쪽을 같이 줄여 **조용히 산다** — 2026-09-28 실측에서 `scripts`
    # 를 뺀 변이가 122건 전부 초록이었다(그 디렉터리의 인용은 2회라 하한 40 도 안 문다).
    ROSTER = ("src", "tests", "e2e", "scripts")

    def test_all_four_dirs_are_walked(self):
        for i, name in enumerate(self.ROSTER):
            self.code("%s/f%d.py" % (name, i), "# `%s`" % ("plan_%s.md" % name))
        sites = citation_sites(self.root)
        self.assertEqual(sorted(n for _, _, n in sites),
                         sorted("plan_%s.md" % n for n in self.ROSTER),
                         "네 디렉터리 중 안 훑은 곳이 있다 — 변이가 조용히 산다")

    def test_other_suffixes_are_not_read(self):
        self.code("src/a.txt", "# `%s`" % ("plan_%s.md" % "gone"))
        self.assertEqual([], citation_sites(self.root),
                         "확장자 밖 파일까지 읽는다 — 데이터 픽스처가 빨개진다")

    def test_a_name_without_backticks_is_also_a_citation(self):
        # 계획 110 이 뒤집은 갈래다. 끊긴 65자리가 전부 이 모양이었다.
        self.code("src/a.py", "# 과거 사례는 %s 였다" % ("plan_%s.md" % "gone"))
        self.assertEqual([("src/a.py", 2, "plan_%s.md" % "gone")],
                         citation_sites(self.root))

    def test_a_longer_word_ending_in_the_name_is_not_a_citation(self):
        # 백틱이 경계를 주던 자리를 **낱말 경계**가 대신한다. 이것이 없으면
        # `my_plan_x.md` 같은 접두 붙은 이름까지 물어 오탐이 된다.
        self.code("src/a.py", "# 파일 my_%s 를 만든다" % ("plan_%s.md" % "gone"))
        self.assertEqual([], citation_sites(self.root))

    def test_an_empty_tree_is_quiet_here(self):
        # 순회가 죽은 경우를 판정에 섞지 않는다 — 실물은 `ALIVE_CITATION_FLOOR` 이 문다.
        self.assertIsNone(citation_alive_gap(citation_sites(self.root), self.docs))


class CitationAliveTest(unittest.TestCase):
    def test_code_cites_documents_that_exist(self):
        sites = citation_sites(DOCS.parent)
        self.assertGreaterEqual(
            len(sites), ALIVE_CITATION_FLOOR,
            "인용을 %d 회밖에 못 셌다 — 순회가 죽었으면 0건 초록이 된다" % len(sites))
        gap = citation_alive_gap(sites, DOCS)
        self.assertIsNone(gap, gap)


# 계획 112 — 위의 `ALIVE_*` 축과 **같은 결손의 문서 쪽**이다. 그쪽은 `ALIVE_DIRS` 네 곳만
# 보고, 2026-10-07 착수 때 `docs/*.md` 안 **42자리**가 없는 파일을 가리키는데 전수가 하나도
# 안 물었다(경위·실측은 `docs/design_history_087.md`).
#
# **축을 합치지 않은 것이 설계의 결정이다** — `ALIVE_DIRS` 에 `docs` 를 끼우면 2줄로 끝나지만
# 문서 쪽 인용이 코드 쪽보다 많아서 `ALIVE_CITATION_FLOOR` 가 **코드 축을 지키는 일을
# 그만둔다**(코드 인용이 전부 사라져도 합산 하한은 조용하다). 그래서 **순회와 하한만** 따로
# 두고 판정자와 정규식은 공유한다.
#
# **날짜 박힌 실측치는 여기 안 적는다** — 리뷰 A-2 지적이다. 아무도 안 거는 숫자는 쓰인
# 다음 반복에 거짓이 된다(이 주석의 첫 판이 이미 그랬다: 121 이라 적었고 실물은 126 이었다).
# 거는 숫자는 아래 하나뿐이고, 분포 서술은 설계 문서가 든다.
#
# 하한 90 의 근거: 실물 인용의 대다수가 `index.md` 한 파일에 있고 그 파일은 **회전하지 않고
# 계획마다 한 줄씩 늘기만 한다.** 나머지는 회전·덮어쓰기로 흔들려 하한에 안 기댄다.
DOC_CITATION_FLOOR = 90


def doc_citation_sites(docs):
    """`docs` 의 **살아 있는** `*.md` 에서 `(파일명, 줄번호, 이름)` 을 모은다.

    **계약**(리뷰 A-1 — 판정 기제가 이 함수 밖에 있어 읽는 사람이 역추론해야 했다):
    인용은 `ALIVE_CITATION` 이 읽는 `` `(plan|design)_<슬러그>.md` `` 꼴이고(백틱 유무를
    안 보며 꺾쇠로 시작하는 자리표시자는 안 걸린다), **결손 판정은 `citation_alive_gap`
    이 `docs / 이름` 의 실재로** 한다. 이 함수는 **모으기만** 한다.

    **최상위만 훑는다**(비재귀 — 리뷰 A-4). `docs/specs/` 와 `docs/e2e/<슬러그>/result.md`
    는 해석 뿌리가 또 갈려 판정이 다르므로 **일부러** 축 밖이다(계획 5절). 넓히려면
    `rglob` 이 아니라 뿌리를 먼저 정해야 한다.

    `docs` 를 인자로 받는 것은 `citation_sites` 와 같은 이유다 — **픽스처가 순회를
    밟아야** 「아카이브를 빼는 조건」과 「대상 확장자」를 좁히는 변이가 조용히 살지 않는다.
    """
    sites = []
    for path in sorted(docs.glob("*.md")):
        if ARCHIVE.match(path.name):
            continue
        for no, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            for found in ALIVE_CITATION.finditer(line):
                sites.append((path.name, no, found.group(1)))
    return sites


class DocCitationAliveGapTest(unittest.TestCase):
    """`doc_citation_sites` 의 갈래를 합성 트리로 밟는다 — 실물은 초록이면 자기를 못 잰다.

    **픽스처는 토큰을 조립해서 쓴다**(`CitationAliveGapTest` 와 같은 계약) — 한 리터럴에
    `design_<이름>.md` 를 담으면 이 파일 자신이 없는 문서를 가리키게 되고, 위의 코드 축이 문다.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.docs = pathlib.Path(self.tmp.name)

    def write(self, name, line):
        (self.docs / name).write_text("# 문서\n%s\n" % line, encoding="utf-8")

    def test_an_empty_tree_is_quiet(self):
        """순회가 빈손인 경우는 여기서 안 문다 — 그 자리는 실물의 하한이 맡는다."""
        self.assertEqual([], doc_citation_sites(self.docs))
        self.assertIsNone(citation_alive_gap(doc_citation_sites(self.docs), self.docs))

    def test_a_citation_to_an_existing_document_is_quiet(self):
        name = "design_%s.md" % "alive"
        self.write("index.md", "근거는 `%s` 다" % name)
        self.write(name, "# 설계")
        self.assertIsNone(citation_alive_gap(doc_citation_sites(self.docs), self.docs))

    def test_a_citation_to_a_missing_document_is_a_gap(self):
        name = "design_%s.md" % "gone"
        self.write("index.md", "근거는 `%s` 다" % name)
        gap = citation_alive_gap(doc_citation_sites(self.docs), self.docs)
        self.assertIsNotNone(gap, "없는 문서를 가리키는데 조용하다")
        self.assertIn("index.md:2", gap, "자리를 안 알려준다 — 사람이 못 찾는다")
        self.assertIn(name, gap, "이름을 안 알려준다")

    def test_archived_documents_are_not_scanned(self):
        """접힌 기록은 그때 그 파일이 있었다 — 고치면 과거를 고쳐 쓰는 것이다."""
        name = "plan_%s.md" % "gone"
        # 아카이브 이름도 **조립한다**(리뷰 A-5). 통째 리터럴로 쓰면 `tests` 가
        # `ALIVE_DIRS` 안이라 **코드 축이 이 줄을 실물 인용으로 읽고**, 077 이 개명되는
        # 날 픽스처 문자열이 결손으로 보고된다 — 지금 초록인 것은 우연이었다.
        for shape in ("history_%s.md", "plan_history_%s.md", "design_history_%s.md"):
            self.write(shape % "077", "근거는 `%s` 다" % name)
        self.assertEqual([], doc_citation_sites(self.docs),
                         "아카이브를 훑었다 — `ARCHIVE` 조건이 죽었다")

    def test_a_non_markdown_file_is_not_scanned(self):
        """docstring 이 「대상 확장자」를 주장하니 거는 자를 둔다 (리뷰 A-6).

        넓히는 변이(`glob("*")`)는 좁히는 변이와 달리 다른 테스트가 안 잡는다.
        """
        self.write("note.txt", "근거는 `%s` 다" % ("plan_%s.md" % "intxt"))
        self.assertEqual([], doc_citation_sites(self.docs),
                         "`.md` 가 아닌 파일을 훑었다 — 대상 확장자가 넓어졌다")

    def test_a_bare_name_outside_backticks_is_caught(self):
        """계획 110 이 백틱 조건을 없앴다 — 문서 쪽도 같은 정규식을 쓰므로 함께 문다."""
        name = "plan_%s.md" % "bare"
        self.write("index.md", "근거는 %s 다" % name)
        gap = citation_alive_gap(doc_citation_sites(self.docs), self.docs)
        self.assertIsNotNone(gap, "백틱 밖 이름을 놓쳤다")

    def test_the_placeholder_form_is_not_a_citation(self):
        """면제 기제를 안 만든 근거 — 자리표시자는 **표기**로 빠진다(설계 계약 4)."""
        self.write("index.md", "자리표시자 `plan_%s.md` 는 파일이 아니다" % "<슬러그>")
        self.assertEqual([], doc_citation_sites(self.docs),
                         "꺾쇠 자리표시자를 인용으로 읽었다 — 정책이 성립하지 않는다")


class DocCitationAliveTest(unittest.TestCase):
    def test_live_docs_cite_documents_that_exist(self):
        sites = doc_citation_sites(DOCS)
        self.assertGreaterEqual(
            len(sites), DOC_CITATION_FLOOR,
            "문서 인용을 %d 회밖에 못 셌다 (하한 %d). 둘 중 하나다 — ① 순회가 죽었다"
            "(0 에 가까우면 이쪽. 그대로 두면 0건 초록이 된다) ② `index.md` 가 대상에서"
            " 빠졌거나 쪼개졌다(대다수 인용이 그 파일에 있다. 축은 멀쩡하고 하한이 낡은"
            " 것이니 수를 다시 재서 고친다)" % (len(sites), DOC_CITATION_FLOOR))
        gap = citation_alive_gap(sites, DOCS)
        self.assertIsNone(gap, gap)


class PinRotTest(unittest.TestCase):
    """빈손 대조 핀이 **마지막 빈손 밤보다 묵었나**.

    핀(`status.md` 의 `## 빈손 대조 핀` 줄)의 값은 「**지난 빈손 밤** 이후 코드 트리가
    안 변했다」는 것이다. 그래서 핀은 빈손 밤이 끝날 때 옮겨야 하고, 안 옮기면 다음
    빈손 밤이 받는 대조가 쓸 수 없게 된다 — 실측으로 **39일·22계획** 묵어 58파일
    `+5,149/-143` 을 내고 있었다(2026-10-22 반복 747).

    **왜 「해시 ≠ `main`」으로 안 재나** — 계획이 도는 날에는 항상 다르고 그게 정상이라
    거짓 RED 가 상시다. 「핀 날짜가 K일 묵었나」·「변경 파일 수가 임계를 넘었나」도
    버렸다: 둘 다 핀을 아무 날에나 갈아끼우는 **공허한 손**을 부르고, 그러면 핀이 제
    용도를 잃은 채로 초록이 된다. 유도는 `docs/design_history_096.md`.
    """

    def test_the_pin_is_not_older_than_the_last_empty_night(self):
        gap = pin_rot_gap((DOCS / "status.md").read_text(encoding="utf-8"),
                          night_reports(DOCS))
        self.assertIsNone(gap, gap)

    def test_the_rot_that_actually_happened_is_red(self):
        """2026-09-30 사건 — 핀이 2026-09-13 인 채로 빈손 밤이 지나갔다."""
        gap = pin_rot_gap("## 빈손 대조 핀 — 기준 트리 `064fe56` (2026-09-13 반복 592 에 옮겼다)",
                          [("night_2026-09-30.md", "| **신호** | ⚪ **빈손** 근거 0건 |")])
        self.assertIsNotNone(gap, "묵은 핀을 놓쳤다")
        self.assertIn("2026-09-30", gap, "마지막 빈손 밤의 날짜를 안 인쇄한다")
        self.assertIn("2026-09-13", gap, "핀의 날짜를 안 인쇄한다")

    def test_no_empty_night_is_quiet(self):
        """빈손 밤이 아직 없던 저장소에서 거짓 RED 를 내지 않는다."""
        self.assertIsNone(pin_rot_gap(
            "## 빈손 대조 핀 — 기준 트리 `064fe56` (2026-09-13 반복 592 에 옮겼다)",
            [("night_2026-10-20.md", "| **신호** | 🟢 **GREEN** 계획 1개 완료 |")]))

    def test_the_same_day_is_not_rot(self):
        """경계는 초과가 아니다 — 그 밤이 옮긴 핀을 같은 밤이 물면 거짓 RED 다."""
        self.assertIsNone(pin_rot_gap(
            "## 빈손 대조 핀 — 기준 트리 `26f1393` (2026-10-22 반복 747 에 옮겼다)",
            [("night_2026-10-22.md", "| **신호** | ⚪ **빈손** 탐색 0건 |")]))

    def test_a_missing_pin_line_is_red_not_silence(self):
        """꼴이 드리프트하면 **그것이 실패다.**

        「재지 못했다」로 조용해지는 길을 두지 않는다 — 계획 120 이 그 자리에서
        죽은 측정기를 초록으로 봤다.
        """
        gap = pin_rot_gap("## 빈손 대조 핀 — 기준 트리는 지난 밤의 것",
                          [("night_2026-10-22.md", "| **신호** | ⚪ **빈손** |")])
        self.assertIsNotNone(gap, "핀 줄을 못 찾았는데 조용하다")
        self.assertIn("핀 줄", gap)

    def test_the_dateless_old_form_is_red(self):
        """2026-09-13~10-22 의 **실물** 꼴 — 날짜가 없다.

        `git show 3d83072:docs/status.md` 가 `## 빈손 대조 핀 — 기준 트리 \`064fe56\``
        한 줄을 낸다. 날짜가 없으면 묵음을 셀 수 없으니 **빨강이다** — 그 꼴을 조용히
        통과시키면 이 자가 제 역사의 대부분에서 죽은 채로 초록이었을 것이다.
        """
        gap = pin_rot_gap("## 빈손 대조 핀 — 기준 트리 `064fe56`",
                          [("night_2026-09-30.md", "| **신호** | ⚪ **빈손** 근거 0건 |")])
        self.assertIsNotNone(gap, "날짜 없는 옛 꼴을 조용히 통과시켰다")
        self.assertIn("핀 줄", gap)

    def test_no_reports_at_all_is_quiet(self):
        """보고서가 0건이면 조용하다 — 그러나 **살아 있는 축은 하한으로 문다.**

        0건 위에서 조용히 통과하는 것이 이 저장소 최다 재발이라, 순수 계층은
        조용해도 `NightReportSignalTest` 가 `assertTrue(reports)` 로 막는다.
        """
        self.assertIsNone(pin_rot_gap(
            "## 빈손 대조 핀 — 기준 트리 `26f1393` (2026-10-22 반복 747 에 옮겼다)", []))
        self.assertIsNone(signal_row_gap([]))

    def test_the_legend_line_is_not_a_signal(self):
        """범례가 거짓 양성을 만들지 않는다 — 표 줄만 센다.

        실측 근거: `night_2026-10-08.md` 가 「🔴 실패 · 🟡 판단 · 🟢 완료 · ⚪ 빈손」을
        본문에 들고 있다. 문서 전체에서 `⚪` 를 찾는 안이 여기서 죽는다.
        """
        self.assertIsNone(pin_rot_gap(
            "## 빈손 대조 핀 — 기준 트리 `26f1393` (2026-10-22 반복 747 에 옮겼다)",
            [("night_2026-10-25.md",
              "## 🟢 종합\n| **신호** | 🟢 완료 |\n"
              # 실물 `night_2026-10-08.md:4` 를 그대로 가져왔다 (`test.md` 3절 ⑧).
              "🔴 실패 · 🟡 판단·패치 · 🟢 완료 · ⚪ 빈손.")]))


class NightReportSignalTest(unittest.TestCase):
    """**가장 최신** 야간 보고서가 신호 줄을 들고 있나.

    `PinRotTest` 의 입력이 이 꼴이다 — 아무도 안 지키면 재는 자가 조용히 죽는다
    (`grep -rn 'reports' tests/` 가 0건이었다).

    **과거는 안 본다.** 40개 중 8개에 줄이 없고 그것이 전부 2026-10-08 이하다.
    고치는 것은 직교 편집이고, 못 세는 ⚪ 는 전부 핀 날짜보다 과거라 **판정에 영향이
    0 이다**(과소 계수가 거짓 초록을 못 만든다). 각 보고서는 **쓰인 날 최신**이므로
    이 축 하나로 앞으로의 보고서가 전부 지켜진다 — 날짜 상수를 박지 않는 이유다.
    """

    def test_the_latest_report_carries_a_signal_row(self):
        # 게이트 ⑱ ㉢ — `docs/reports/` 는 추적 밖이라 다른 체크아웃(자동 병합 워크트리)엔 없다.
        # 폴더가 «있는데» 0건인 것은 여전히 문다.
        if not (DOCS / "reports").is_dir():
            self.skipTest("docs/reports/ 없음 — 기계 로컬 가드")
        reports = night_reports(DOCS)
        self.assertTrue(reports, "야간 보고서를 못 찾았다 — 순회가 죽으면 0건 초록이 된다")
        gap = signal_row_gap(reports)
        self.assertIsNone(gap, gap)

    def test_the_latest_is_the_one_that_is_read(self):
        """축이 **최신**이라는 것 자체를 못박는다 (변이 ⑤ 가 여기서 죽는다)."""
        rows = [("night_2026-10-20.md", "| **신호** | 🟢 완료 |"),
                ("night_2026-10-22.md", "## ⚪ 종합 — 표 줄이 없다")]
        self.assertIsNotNone(signal_row_gap(rows), "최신의 결손을 놓쳤다")
        self.assertIn("night_2026-10-22.md", signal_row_gap(rows))

    def test_an_old_gap_is_left_alone(self):
        """과거 8개를 안 문다 — 고치면 직교 편집이고 판정에 영향이 0 이다."""
        self.assertIsNone(signal_row_gap(
            [("night_2026-10-08.md", "본문만 있다"),
             ("night_2026-10-22.md", "| **신호** | ⚪ **빈손** |")]))

    def test_a_report_without_the_row_has_no_signal(self):
        self.assertIsNone(report_signal("# 야간 보고\n## 🟢 종합 — 머리만 있다"))

    def test_the_signal_is_read_from_the_row(self):
        self.assertEqual("⚪", report_signal("| **신호** | ⚪ **빈손** 탐색 0건 |"))

    def test_the_signal_survives_ordinary_editing_of_the_cell(self):
        """**값을 감싸는 편집**이 재는 자를 죽이지 않는다.

        백지 패스가 재현한 자리다 — 첫 글자를 집는 축은 아래 셋에서 `*`·`` ` ``·`None`
        을 돌려줬고, 그러면 그 밤이 빈손으로 세어지지 않은 채 꼴 가드도 조용했다.
        """
        for cell in ("| **신호** | **⚪ 빈손** |",
                     "| **신호** | `⚪` 빈손 |",
                     "| **신호**  | ⚪ **빈손** |",
                     "|**신호**| ⚪ 빈손 |"):
            with self.subTest(cell=cell):
                self.assertEqual("⚪", report_signal(cell))

    def test_an_unknown_mark_is_not_a_signal(self):
        """알려진 넷 밖은 신호가 아니다 — 조용히 세지 않는 것보다 빨강이 낫다."""
        self.assertIsNone(report_signal("| **신호** | ❓ 모르는 표기 |"))

    def test_every_report_of_the_latest_day_is_read(self):
        """같은 날 두 벌이면 **둘 다** 본다 (백지 패스 지적).

        같은 날 두 벌 이상인 날이 넷이다 — 사전순 마지막만 보는 축은 앞것을 영구히
        검사하지 않고, 그 밤이 ⚪ 였으면 집계에서도 빠진다.
        """
        rows = [("night_2026-10-22.md", "본문만 있다"),
                ("night_2026-10-22_x.md", "| **신호** | 🟢 완료 |")]
        gap = signal_row_gap(rows)
        self.assertIsNotNone(gap, "같은 날 앞것의 결손을 놓쳤다")
        self.assertIn("night_2026-10-22.md", gap)

    def test_an_unpadded_latest_name_is_red(self):
        """0 패딩이 빠진 이름은 ⚪ 집계에서 조용히 빠지므로 빨강이다."""
        gap = signal_row_gap([("night_2026-9-5.md", "| **신호** | ⚪ 빈손 |")])
        self.assertIsNotNone(gap, "날짜를 못 읽는 이름을 통과시켰다")
        self.assertIn("night_2026-9-5.md", gap)


class ReportNameTest(unittest.TestCase):
    """**날짜를 못 읽는** 야간 보고서 이름이 하나라도 있나.

    `pin_rot_gap` 의 ⚪ 집계와 `signal_row_gap` 의 꼴 검사가 둘 다 `REPORT_NAME` 으로
    날짜를 읽는데, 그 정규식은 0 패딩을 **요구**한다. 그래서 패딩이 빠진 이름은
    집계에서 `if REPORT_NAME.match(name)` 에 **걸러지고**, 사전순 마지막이 아니면
    꼴 가드도 못 본다 — 핀 썩음 판정이 조용히 죽는다.

    재현(계획 125 탐색): 핀 `2026-09-13` + ⚪ `night_2026-10-5.md` +
    `night_2026-11-01.md` → **둘 다 `None`**, 이름만 `10-05` 로 고치면 즉시 빨강.

    **관용하지 않고 신고한다.** `10-5` 를 `10-05` 로 읽어 주는 안은 틀린 이름 위에서
    자가 초록으로 돌아 사람이 그 꼴을 계속 쓰게 한다(`digest.md` 후보 `[7]` 의 처방).
    """

    def test_every_live_report_name_carries_a_date(self):
        # 게이트 ⑱ ㉢ — `docs/reports/` 는 추적 밖이라 다른 체크아웃엔 없다.
        if not (DOCS / "reports").is_dir():
            self.skipTest("docs/reports/ 없음 — 기계 로컬 가드")
        reports = night_reports(DOCS)
        self.assertTrue(reports, "야간 보고서를 못 찾았다 — 순회가 죽으면 0건 초록이 된다")
        gap = report_name_gap(reports)
        self.assertIsNone(gap, gap)

    def test_an_unpadded_name_is_named(self):
        gap = report_name_gap([("night_2026-10-5.md", "| **신호** | ⚪ 빈손 |")])
        self.assertIsNotNone(gap, "패딩 빠진 이름을 통과시켰다")
        self.assertIn("night_2026-10-5.md", gap)

    def test_a_dateless_name_is_named(self):
        """날짜가 아예 없는 이름 — `night_reports` 의 glob 이 그것도 집어 온다."""
        gap = report_name_gap([("night_report.md", "| **신호** | 🟢 완료 |")])
        self.assertIsNotNone(gap, "날짜 없는 이름을 통과시켰다")
        self.assertIn("night_report.md", gap)

    def test_a_name_hidden_in_the_middle_is_named(self):
        """**사전순 중간**에 숨은 것 — `signal_row_gap` 이 구조적으로 못 보는 자리다.

        `night_2026-10-5` < `night_2026-11-01` 이라 최신-하나 축은 조용하다.
        그 침묵이 이 계획의 근거이므로 **두 자의 차이를 여기서 못박는다.**
        """
        rows = [("night_2026-10-5.md", "| **신호** | ⚪ 빈손 |"),
                ("night_2026-11-01.md", "| **신호** | 🟢 완료 |")]
        self.assertIsNone(signal_row_gap(rows), "전제가 바뀌었다 — 최신 축이 이미 문다")
        gap = report_name_gap(rows)
        self.assertIsNotNone(gap, "중간에 숨은 이름을 놓쳤다")
        self.assertIn("night_2026-10-5.md", gap)

    def test_all_of_them_are_named_not_just_the_first(self):
        """**전 자리를 모은다** — `citation_alive_gap` 선례(먼저 걸린 하나가 아니다).

        하나씩 돌려주면 고치는 쪽이 전수를 한 번 더 돌려야 다음 것이 보인다 —
        `digest.md` 후보 `[4]` 가 `archive_gap` 에서 등재한 그 비용이다.
        """
        gap = report_name_gap([("night_2026-10-5.md", "본문"),
                               ("night_report.md", "본문")])
        self.assertIn("night_2026-10-5.md", gap)
        self.assertIn("night_report.md", gap)

    def test_the_real_suffixed_forms_stay_quiet(self):
        """음성 대조 — 같은 날 두 벌인 실물 꼴은 **접두**만 맞으면 조용하다.

        **이름을 상상하지 않고 실물에서 떴다** (`test.md` 3절 ⑧). 같은 날 두 벌
        이상인 날이 넷이고 접미사 꼴은 전부 `_<슬러그>` 다 — `ls docs/reports/` 실측:
        `night_2026-09-09_iter-third-witness.md` · `night_2026-09-10_verdict-head.md` ·
        `night_2026-09-12_empty-sweep.md` · `night_2026-09-12_pin-coverage.md` ·
        `night_2026-09-14_order-probe.md`. 접미사를 무는 쪽으로 좁히면 이 다섯이
        거짓 RED 가 된다.
        """
        self.assertIsNone(report_name_gap(
            [("night_2026-09-09.md", "본문"),
             ("night_2026-09-09_iter-third-witness.md", "본문"),
             ("night_2026-09-12_pin-coverage.md", "본문")]))

    def test_a_date_that_runs_into_more_characters_is_named(self):
        """**날짜 뒤에 바로 붙은 글자** — 백지 패스가 실측한 자리다 ([R125-2]).

        구분자를 요구하기 전에는 `night_2026-10-055.md` 가 `match` 되고 `group(1)` 이
        `2026-10-05` 라, 새 가드는 **조용히 통과시키고** `pin_rot_gap` 은 그 밤을
        10-05 로 **잘못 읽었다**(재현했다). 날짜의 「값」이 아니라 「꼴」 문제라
        docstring 이 면제한 범위 밖이었다.
        """
        for name in ("night_2026-10-055.md", "night_2026-10-05extra.md"):
            with self.subTest(name=name):
                gap = report_name_gap([(name, "본문")])
                self.assertIsNotNone(gap, "날짜 뒤로 흘러넘친 이름을 통과시켰다")
                self.assertIn(name, gap)

    def test_no_reports_at_all_is_quiet(self):
        """0건이면 조용하다 — 하한은 위 살아 있는 축이 `assertTrue` 로 문다."""
        self.assertIsNone(report_name_gap([]))


class DupDefGapTest(unittest.TestCase):
    """`dup_def_gap` 의 갈래. 실물은 `DupDefTest` 가 부른다.

    실물은 지우고 나면 초록이라 갈래가 한 번씩만 지나간다. 특히 **오탐 축**(서로 다른
    클래스의 같은 이름)은 등재문이 적은 regex 처방이 실제로 틀리던 자리고, 그 꼴로
    `src/ tests/ e2e/ scripts/` 를 세면 `setUp`·`index`·`status`·`test_*` 가 **7건**
    잡힌다(계획 126 실측). 자가 스코프를 보는 한 조용해야 한다.
    """

    def test_a_module_level_duplicate_is_named_with_both_line_numbers(self):
        gap = dup_def_gap([("m.py", "def f():\n    pass\n\n\ndef f():\n    pass\n")])
        self.assertIsNotNone(gap, "가려진 모듈 레벨 정의를 통과시켰다")
        self.assertIn("`f`", gap)
        # **두 줄 번호를 둘 다 댄다** — 하나만 대면 고치는 쪽이 어느 것이 죽은 것인지
        # 모른다. 이 단언이 없으면 줄 번호를 빼는 변이가 살아남는다.
        self.assertIn(":1", gap)
        self.assertIn(":5", gap)

    def test_the_same_name_in_different_classes_is_quiet(self):
        """**오탐 축** — 등재문의 regex 처방이 틀리던 바로 그 자리다."""
        self.assertIsNone(dup_def_gap([("m.py",
            "class A:\n    def setUp(self):\n        pass\n\n\n"
            "class B:\n    def setUp(self):\n        pass\n")]))

    def test_a_duplicate_inside_one_class_is_named(self):
        """같은 클래스 안의 중복은 **진짜 결함**이다 — 모듈 레벨과 같은 병이다.

        `^def ` 수집 꼴은 이 축과 위 오탐 축을 **구별하지 못한다**. 둘을 나란히 두는
        것이 「스코프를 본다」의 값이다.
        """
        gap = dup_def_gap([("m.py",
            "class A:\n    def go(self):\n        pass\n\n    def go(self):\n        pass\n")])
        self.assertIsNotNone(gap, "클래스 안의 중복을 놓쳤다")
        self.assertIn("`go`", gap)

    def test_the_same_name_nested_in_different_functions_is_quiet(self):
        self.assertIsNone(dup_def_gap([("m.py",
            "def a():\n    def inner():\n        pass\n\n\n"
            "def b():\n    def inner():\n        pass\n")]))

    def test_a_duplicate_nested_in_one_function_is_named(self):
        gap = dup_def_gap([("m.py",
            "def a():\n    def inner():\n        pass\n    def inner():\n        pass\n")])
        self.assertIsNotNone(gap, "함수 안의 중복을 놓쳤다")
        self.assertIn("`inner`", gap)

    def test_a_conditional_second_definition_is_quiet(self):
        """**천장을 못박는다** — `try`/`except` 재정의는 의도된 꼴이라 안 문다.

        면제가 아니라 `_scope_dups` 가 `body` 를 직접 보는 데서 **공짜로** 나온다.
        여기 못을 안 박으면 나중에 `ast.walk` 로 바꾸는 변이가 이 꼴을 거짓 RED 로
        만들면서도 조용히 산다.
        """
        self.assertIsNone(dup_def_gap([("m.py",
            "try:\n    from _fast import f\nexcept ImportError:\n"
            "    def f():\n        pass\n")]))

    def test_all_of_them_are_named_not_just_the_first(self):
        """**전 자리를 모은다** — `report_name_gap` 선례(먼저 걸린 하나가 아니다)."""
        gap = dup_def_gap([("a.py", "def f():\n    pass\ndef f():\n    pass\n"),
                           ("b.py", "def g():\n    pass\ndef g():\n    pass\n")])
        self.assertIn("a.py", gap)
        self.assertIn("b.py", gap)

    def test_a_clean_source_is_quiet(self):
        self.assertIsNone(dup_def_gap([("m.py", "def f():\n    pass\n")]))

    def test_no_sources_at_all_is_quiet(self):
        """0건이면 조용하다 — 하한은 실물 축이 `assertTrue` 로 문다."""
        self.assertIsNone(dup_def_gap([]))

    def test_a_broken_file_is_not_swallowed(self):
        """문법이 깨진 파일은 **터진다** — 삼키면 「위반 0」에 조용히 섞인다."""
        with self.assertRaises(SyntaxError):
            dup_def_gap([("m.py", "def f(\n")])


class DupDefTest(unittest.TestCase):
    """살아 있는 `.py` 중에 가려진 함수 정의가 있나 — 계획 126 의 자.

    **판정은 `dup_def_gap` 이 한다** — 갈래를 실물 없이 밟는 것은 `DupDefGapTest` 다.
    """

    def test_no_live_source_has_a_shadowed_definition(self):
        paths = python_sources()
        # **하한** — `rglob` 이 죽어 0건을 훑고 「위반 0」을 외치는 것을 막는다.
        self.assertGreaterEqual(
            len(paths), SOURCE_FLOOR,
            "모집단이 %d개다 — 하한 %d 아래면 순회가 죽은 것이지 깨끗한 것이 아니다"
            % (len(paths), SOURCE_FLOOR))
        gap = dup_def_gap(
            (path.relative_to(ROOT), path.read_text(encoding="utf-8")) for path in paths)
        self.assertIsNone(gap, gap)

    def test_the_population_carries_every_directory_that_exists(self):
        """모집단이 네 디렉터리를 **전부** 담는다 — 하나를 빼는 변이를 막는다.

        **실물로는 못 재는 축이다** — `scripts/` 는 오늘 `.py` 가 0개라 빼도 수가 안
        변하고, `src/` 를 빼도 남은 셋이 하한을 넘겨 조용하다. 합성 트리로 순회를
        직접 밟는다 (`ArchiveBacklogTest` 의 모집단 축과 같은 분담).
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for name in SOURCE_DIRS:
                (root / name).mkdir()
                (root / name / ("%s_mod.py" % name)).write_text("x = 1\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "not_source.py").write_text("x = 1\n", encoding="utf-8")
            self.assertEqual([p.name for p in python_sources(root)],
                             sorted("%s_mod.py" % name for name in SOURCE_DIRS))

    def test_a_missing_directory_is_skipped_not_fatal(self):
        """얕은 체크아웃 하나가 전수를 통째로 흔들지 않는다."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "only.py").write_text("x = 1\n", encoding="utf-8")
            self.assertEqual([p.name for p in python_sources(root)], ["only.py"])


if __name__ == "__main__":
    unittest.main()
