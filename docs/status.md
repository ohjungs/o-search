---
signal: GREEN
phase: 테스트
step: 1/1
attempt: 0
iteration: 362
updated: 2026-09-06
ctx: 52
night_iterations: 179
night_red: 2
night_retries: 4
plan: head-anchor-cover 계획 62 (개발 1/1 완료 · 다음은 테스트 1/1)
---

## 현재 상태

**계획 62 의 개발 1/1 을 닫았다 — 문서 가드 둘이 이제 자기 판정을 잰다.**
`tests/test_docs.py` 에 모듈 상수 `DOC_HEAD`(`ITER_LINE` 아래)와
`DocHeadPatternTest`(CAUGHT 3 · NOT_CAUGHT 6)를 세우고, `IterationPatternTest` 에
앵커를 실제로 재는 리터럴 두 줄을 더했다. 만진 파일은 `tests/test_docs.py` ·
`README.md`(단위 건수 줄) **둘뿐**이고 계획서 「건드릴 파일」과 정확히 같다.

## 무엇이 닫혔나

- ① **`ITER_LINE` 의 앵커를 붙드는 단언이 생겼다.** `assertIsNone(ITER_LINE.search(
  "x iteration: 1"))`(`^`)·`assertIsNone(ITER_LINE.search("iteration: 1x"))`(`$`).
  기존 `night_iterations: 90` 단언이 막던 것은 앵커가 아니라 **복수형 `s`** 라는
  진단을 그 자리 주석으로 남겼다 — 다음 편집이 오해를 반복하지 않게.
- ② **`r"^# \S"` 가 모듈 상수 `DOC_HEAD` 로 올라갔다.** `DocHeadTest` 는
  `assertRegex(first, DOC_HEAD, …)` 로 실물 세 문서를 재는 자리로 남고, 갈래는
  `DocHeadPatternTest` 가 합성 리터럴로 잰다(`CitationPatternTest` 관용구 그대로).
  두 층을 가른 목적이 `step_gap`·`iter_gap` 과 같다.

## TDD — RED 를 눈으로 먼저 봤다

`rules/dev.md` 0절. 상수 없이 새 클래스와 `assertRegex(first, DOC_HEAD, …)` 만 먼저
넣고 전수를 돌려 **`NameError: name 'DOC_HEAD' is not defined` ×12**(새 클래스 9 ·
`DocHeadTest` subTest 3)와 `test_readme` 의 `(618, 21) != (620, 21)` 을 본 뒤 구현했다.

## 변이 재측 — 완료 기준 1~4 (2026-09-06 · 반복 362)

저장소 파일 무접촉. 하네스는 저장소 밖 스크래치패드에서 `mock.patch.object` 로
모듈 속성만 갈아 끼운다.

| 변이 | 결과 |
|---|---|
| **M0** 무변이 대조군 | `Ran 620` — 죽은 단언 **0** |
| **M1** `ITER_LINE` 앵커 제거 | **사망 1** — `IterationPatternTest.test_status_line_needs_the_whole_line` |
| **M2** `DOC_HEAD` → `re.compile(r"^")` | **사망 6** — 전부 `DocHeadPatternTest.test_pattern_leaves_non_h1_heads` 의 subTest |
| **M3** 양성 대조 `^ZZZ` | **사망 6** — `DocHeadTest` 3(실물) + `DocHeadPatternTest.test_pattern_catches_document_heads` 3 |
| **M5** `ITER_ROW` 넓힘(계획 61) | **여전히 사망 2** — `IterationPatternTest.test_only_the_exact_row_matches` + `IterGapTest` |

**M2 와 M3 이 서로 다른 이름을 죽인다** — 판정을 넓히는 변이는 합성 갈래가,
판정을 죽이는 변이는 실물 검사가 잡는다. 두 층을 가른 값이 이것이다.

## 완료 기준 7개

1~4 위 표대로 충족 · **5** 전수 `Ran 620 tests in 15.792s` `OK` rc 0(맨몸)이고
`README.md` 도 「단위 620건」으로 같은 커밋에서 움직였다 · **6** `git diff --stat
d763317 HEAD -- src/ e2e/ docs/specs/ data/` **빈손**, `data/crawl.db` sha256
`85c96744…5bda18` 무변 · **7** `status.step` `1/1` 과 `index.md` 62번 행 `1/1` 이
이 커밋에서 함께 움직인다(`StepSyncTest` 의 세 번째 시험대).

## 다음

**테스트 1/1.** 새 `DOC_HEAD`·`DocHeadPatternTest` 와 늘어난 `ITER_LINE` 단언 위에서
갭을 탐색한다. 계획서 5절이 남긴 자리가 후보다 — `ITER_ROW`·`STEP_ROW`·`STEP_LINE`·
`PLAN_SLUG` 의 앵커는 **오늘 재지 않았다**. 같은 유형의 구멍이 거기 있는지는 이
계획의 변이 목록 밖이고, 있으면 `digest` 후보로 남긴다.

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60·61·62 의 커밋이 `loop/passage-cost-band` 에
  쌓여 있고 `origin/main`(`d1fe3e9`) 무접촉 · PR 0(만들지도 조회하지도 않았다).
- 반복 361 커밋(`e774608`)은 원격에 정상 반영돼 있었다. 이번 커밋도 같은 브랜치에
  그대로 쌓는다 — `--force`·`--amend`·`rebase` 없음.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- `docs/digest.md` 는 **200줄(상한 정각)** 이다 — 이번 반복도 한 줄도 안 더했다.
  다음에 더해야 하면 `rules/docs.md` 3절대로 **완료 항목부터** 지운다.
- 회전은 없다 — `history_current.md` 는 **177 → 이 항목 뒤 201줄**(상한 300), 다음
  회전 번호는 `history_064.md` 다.
