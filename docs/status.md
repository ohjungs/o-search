---
signal: GREEN
phase: 테스트
step: 1/1
attempt: 0
iteration: 368
updated: 2026-09-06
ctx: 41
night_iterations: 185
night_red: 2
night_retries: 4
plan: anchor-net-cover 계획 63 (테스트 1/1 완료 · 다음은 리뷰)
---

## 현재 상태

**개발이 세운 다섯 줄을 남의 관찰이 아니라 이 반복의 하네스로 다시 쟀고, 여섯 변이가
전부 개발이 적은 대로 죽었다.** 새로 세운 테스트는 **0개** — 갭 탐색이 찾은 것 둘이
`rules/test.md` 4절의 8점 선 아래(`[5]`·`[4]`)라 `digest.md` 에 등재만 했다.
개발이 신고한 어긋남(완료 기준 6번)은 **계획서 4절에 정정으로 못박아 닫았다.**

## 변이 재측 — 하네스를 새로 짜서 다시 걸었다

| 변이 | 죽은 단언 | 어디서 |
|---|---|---|
| **M0** 무변이 대조군 | **0** | 오탐 0 |
| **M1a** `STEP_LINE` `^` 제거 | **1** | `StepPatternTest.test_status_lines_need_the_whole_line` |
| **M1b** `STEP_LINE` `$` 제거 | **1** | 같은 시험 |
| **M2** `PLAN_SLUG` `^` 제거 | **1** | 같은 시험 |
| **M3** `ITER_ROW` `^` 제거 | **1** | `IterationPatternTest.test_only_the_exact_row_matches` |
| **M4** `STEP_ROW` `^` 제거 | **1** | `StepPatternTest.test_row_is_picked_by_exact_slug` |
| **R1a·R1b** 계획 62 의 `ITER_LINE` `^`·`$` 제거 | **각 1** | `IterationPatternTest.test_status_line_needs_the_whole_line` |
| **P1~P4** 양성 대조(`^ZZZ`) | **6 · 6 · 5 · 4** | 배선 확인 |

전수 맨몸 `Ran 620 tests in 15.869s · OK · rc 0`. 하네스는 저장소 밖
(`scratchpad/mutate.py`)이고 `mock.patch.object` 로 메모리에서만 갈아 끼웠다 —
`git status --porcelain` 은 하네스를 돌리는 내내 빈손이었다.

## 개발이 신고한 어긋남을 닫았다

완료 기준 6번의 「건수가 620 → **늘어난 수**」는 **3절 처방과 어긋난 예측**이었다 —
처방이 기존 시험에 단언을 더하고 합성 표에 행을 끼우는 것이라 메서드 수가 안 는다.
`docs/plan_anchor-net-cover.md` 4절 6번 아래에 **정정 문단**을 붙였다: 기준의 뜻(전수
초록 + `README.md` 일치)은 그대로 요구하고 **건수 증가 요구만 무효**로 한다.
**단언을 낮춘 것이 아님을 재서 보였다** — `test_readme.UNIT_COUNT` 를 「못 뽑는
꼴」과 「다른 수를 뽑는 꼴」로 각각 갈면 `test_verification_counts_match_reality` 가
**각각 1건씩 죽는다**. 즉 「단위 620건 ↔ 실제 620건」은 살아 있는 단언이다.

## 갭 탐색 — 6개 카테고리, 8점 이상 0건

정규식 축은 계획 60~63 이 닫았으므로 **남은 자리는 「무엇을 검사 대상으로 삼는가」**
쪽이었다. 실측 둘 다 죽은 단언 0 이지만 점수가 선 아래라 이번에 세우지 않았다.

- **`[5]` `APPEND_TARGETS` 를 줄이는 변이가 안 걸린다** — `history_current.md` 를
  빼도(둘로 줄여도, 하나만 남겨도) **0**. 그 문서가 머리 검사에서 통째로 빠진다.
- **`[4]` `ARCHIVE` 를 넓히는 변이 셋(`$` 제거·`re.I`·`[0-9]+`→`[0-9]*`)도 0** —
  다만 물리려면 `history_001.md.bak.md` 같은 이름이 `docs/` 에 있어야 해 도달성이
  낮다. **기록 하나를 정정했다**: 계획 62·63 이 `^…$` 를 한 덩어리로 「`.match()`
  라 잉여」로 미뤘는데, **등가 변이는 `^` 뿐**이고 `$`·수량자·대소문자는 아니다.
  진짜 위험한 «접두어까지 넓히기»는 `DocCitationTest` 가 이미 1건으로 잡는다.

둘 다 `digest ## 다음 계획 후보 (테스트 phase 갭, 8점 미만)` 에 한 줄로 등재했고
**여는 조건은 「`APPEND_TARGETS` 나 `ARCHIVE` 를 손대는 날」** 이다.

## 하지 않은 것

- **새 테스트 0줄** — 8점 이상이 0건이다(`rules/test.md` 4절). 계수기를 위해 시험을
  쪼개지 않은 것과 같은 이유로, 점수 선 아래 갭에 단언을 세우지 않았다.
- **`tests/`·`src/`·`e2e/`·`README.md` 무접촉** — 이번 반복이 고친 것은 기록 문서
  넷(`digest.md`·`status.md`·`history_current.md`·`metrics.md`)과 계획서 하나다.
- **`digest.md` 200줄 유지** — 새 항목 한 줄을 넣으면서 닫힌 지 오래인 완료 항목
  하나(계획 40 `exit-code-contract`)를 지웠다. 원본은 `plan_history_026.md` 에 있다.

## 다음

**리뷰 phase.** 볼 것은 ① 다섯 줄이 실물 판정을 안 바꾸는가(`232`·`1/1` 무변) ②
잡음 행이 **대상 행 앞** 에 있어야만 변이를 잡는다는 순서 의존이 주석에만 적혀
있는가 ③ 계획서 4절의 정정이 「단언을 낮춘 것」으로 읽히지 않는가.

## 한도

- 병합은 사람 몫이다 — 계획 57~63 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR 0(만들지도 조회하지도 않았다).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 커밋 하나로 그대로 쌓았다.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 줬다.
- `history_current.md` 는 88줄에서 이번 항목을 더해 **116줄**(상한 300 · 다음 회전
  번호 `history_065.md`).
