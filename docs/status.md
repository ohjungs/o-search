---
signal: DONE
phase: e2e
step: 0/0
attempt: 0
iteration: 365
updated: 2026-09-06
ctx: 56
night_iterations: 182
night_red: 2
night_retries: 4
plan: null
---

## 현재 상태

**계획 62 `head-anchor-cover` 를 e2e 1/1 로 닫았다 — 통과 · 완료 기준 7/7 · 활성 계획 0.**
e2e 21종을 전부 맨몸으로 다시 돌려 **rc 0 · 21/21** 이고, 전수는 `Ran 620 tests in
15.767s` · `OK` · rc 0 이다. 결과는 `docs/e2e/head-anchor-cover/result.md`.

## e2e 결과

**새 e2e 파일 0개를 「해당 없음」으로 넘기지 않고 근거 셋으로 쟀다**(`rules/e2e.md` 3절) —
프로세스 밖 변화 0(`src/`·`e2e/`·`docs/specs/`·`data/` diff **빈손**) · `DOC_HEAD` 가
`tests/` 안이라 네 수단(웹 UI·HTTP API·CLI·라이브러리) 어디에도 걸 곳이 없다
(`src/` 에 `tests` 를 import 하는 줄 **0건**) · 새로 만들면 전수 명령과 겹쳐 「1회만」이
깨진다. 계획 60·61 이 밟은 자리와 같고 형식도 같다.

**대신 사용자 관점 검증을 실행했다.** 실물 `docs/` 를 `mktemp -d` 로 복사해 사람이 낼
법한 **머리 편집 넷**을 넣었더니 **4/4 가 빨개졌고** 가드가 문서 이름과 실제 첫 줄을 함께
찍었다 — H1 머리가 리스트 항목에 빨려 들어감(이 파일이 존재하게 만든 그 사고의 모양) ·
H1→H2 · 머리 앞 빈 줄 · `# ` 뒤 공백 누락. 대조군은 조용하다. **다섯 판 어디서도
`DocHeadPatternTest` 는 안 흔들린다** — 두 층을 가른 목적 그대로다.

**완료 기준 7/7 을 오늘 다시 쟀다.** M0 대조군 `Ran 620 · 실패 0 · 에러 0` ·
**M1**(앵커 제거) → `test_status_line_needs_the_whole_line` **하나만** 사망 ·
**M2**(`DOC_HEAD` → `^`) → `test_pattern_leaves_non_h1_heads` 가 6/6 subTest 사망 ·
**M3**(`^ZZZ`) → 실물 쪽 `DocHeadTest` 3/3 사망 ·
**M5**(`ITER_ROW` 넓히기) → 계획 61 이 세운 `test_only_the_exact_row_matches` 여전히 사망.
기준선은 8축 전부 회귀 0 이라 `docs/project.md` 를 한 줄도 안 갱신했다.

## e2e 가 잡은 것 — 세 프로세스가 놓친 주석 (severity: low)

**M3 의 실패 메시지가 실물 첫 줄을 그대로 찍어서 드러났다**: `index.md` 는 `# 계획 목록` ·
`history_current.md` 는 `# 최근 반복 기록` 인데, `DocHeadPatternTest.CAUGHT` 위 주석은
「**실물 세 문서의 첫 줄 그대로**」라 적고 리터럴 옆에 문서 이름을 달아 두었다 —
그 둘의 리터럴(`# 계획 색인`·`# 기록 (현재)`)은 **실물과 다르다.**

**동작 영향 0**(합성 리터럴이라 판정에 제목 문구가 안 쓰인다 — 편집 다섯 판에서 안 움직였다)
**이지만 문장이 거짓이다.** 리뷰 phase 가 후보 ③으로 이 자리를 보고도 「제목이 바뀌면
고쳐야 한다로 읽힐 여지」로만 읽었을 뿐 **이미 어긋나 있다**는 것은 못 봤다.
**주석만 고쳤다** — 「합성 리터럴이다 · 실물 제목이 바뀌어도 안 움직인다 · 실물 첫 줄은
`DocHeadTest` 몫이다」로 바꾸고 문서 이름 꼬리주석 셋을 지웠다. **리터럴은 안 건드렸다**
(실물을 좇게 만들면 계획 61 리뷰가 세운 「두 층을 가른다」가 거꾸로 무너진다).
계획의 「건드릴 파일」 안이고 판정·리터럴·건수가 무변이라 개발 phase 로 안 돌렸다 —
`rules/e2e.md` 8절은 **실패**했을 때 되돌리라고 적는데 21종·전수 어디도 안 빨개졌다.

## 검증

전수 **맨몸** `Ran 620 tests in 15.767s` · `OK` · **rc 0** (주석 수정 뒤 · 건수 무변).
e2e 21종 개별 실행 **전부 rc 0**. `ls e2e/*.py` **21개** ↔ `README.md` 「e2e 시나리오 21종」.
범위 무접촉 — `git diff --stat d763317 HEAD -- src/ e2e/ docs/specs/ data/` **빈손** ·
`data/crawl.db` sha256 `85c96744…5bda18` 무변.

## 다음

**활성 계획 0 — 다음 반복은 계획 phase 다.** `digest ## 다음 계획 후보 (테스트 phase 갭,
8점 미만)` 에 계획 62 테스트 phase 가 등재한 `[6]`「계획 62 가 `ITER_LINE` 에서 닫은 앵커
구멍의 형제가 정규식 넷에 그대로 있다 — 앵커를 지우는 변이 4/4 가 전수 620건에서 생존한다」가
남아 있고, 그 항목의 여는 조건은 계획 62 와 같은 「그 검사를 손대는 날」이다.

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60·61·62 의 커밋이 `loop/passage-cost-band` 에
  쌓여 있고 `origin/main`(`d1fe3e9`) 무접촉 · PR 0(만들지도 조회하지도 않았다).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 = 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- `docs/digest.md` 는 **200줄 정각**이다 — 완료 한 줄을 더하면서 이 계획이 닫은 후보
  한 줄을 지워 정각을 지켰다.
- 회전은 없다 — `history_current.md` 는 상한 300 아래고, 다음 회전 번호는 `history_064.md` 다.
