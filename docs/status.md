---
signal: GREEN
phase: 리뷰
step: 1/1
attempt: 0
iteration: 363
updated: 2026-09-06
ctx: 46
night_iterations: 180
night_red: 2
night_retries: 4
plan: head-anchor-cover 계획 62 (테스트 1/1 완료 · 다음은 리뷰 1/1)
---

## 현재 상태

**계획 62 의 테스트 1/1 을 닫았다 — 완료 기준 재측 4/4 그대로고, 갭 하나를
찾아 `digest` 에 [6] 으로 등재했다.** 테스트 phase 는 새 테스트를 쓰는 자리가
아니라 빠뜨린 것을 찾고 전체를 돌리는 자리다(`rules/test.md` 1·3·6절).
저장소 코드는 **한 바이트도 안 고쳤다** — 변이는 전부 저장소 밖 스크래치패드
하네스가 `mock.patch.object` 로 모듈 속성만 갈아 끼운 것이다.

## 완료 기준 재측 — 다른 프로세스에서 다시 걸었다

| 변이 | 결과 |
|---|---|
| **M0** 무변이 대조군 | `Ran 620` — 죽은 단언 **0** |
| **M1** `ITER_LINE` 앵커 제거 | **사망 1** — `IterationPatternTest.test_status_line_needs_the_whole_line` |
| **M2** `DOC_HEAD` → `^` | **사망 1** — `DocHeadPatternTest.test_pattern_leaves_non_h1_heads` |
| **M3** 양성 대조 `^ZZZ` | **사망 2** — `DocHeadPatternTest.test_pattern_catches_document_heads` + `DocHeadTest` |
| **M5** `ITER_ROW` 넓힘(계획 61) | **여전히 사망 2** — `IterationPatternTest` + `IterGapTest` |
| **M6·M7** `DOC_HEAD` 의 `\S` 제거(`^# `·`^#`) | **각각 사망 1** — `NOT_CAUGHT` 의 `"#제목"`·`"# "` 이 그 글자를 붙든다 |

M2·M3 이 서로 다른 이름을 죽여 두 층의 귀속이 다시 확인됐다.

## 갭 탐색 — 후보 하나, 점수 [6]

**계획 62 가 `ITER_LINE` 에서 닫은 구멍의 형제가 정규식 넷에 그대로 있다.**
`STEP_LINE`(`^`·`$`) · `PLAN_SLUG`(`^`) · `ITER_ROW`(`^`) · `STEP_ROW`(`^`) 를
지우는 변이가 **4/4 전수 620건에서 생존**했다(`ARCHIVE` 도 생존하나 `.match()` 라
`^` 가 잉여). 배선 의심을 먼저 껐다 — 같은 상수를 `^ZZZ` 로 죽이면 각각
**6·6·4·1건**이 죽는다. `StepPatternTest` 의 `STEP_LINE.search("step: 1")` 이 막던
것도 앵커가 아니라 **`N/M` 모양**이라 `night_iterations: 90` 과 같은 착시였다.

**8 미만이라 이 스텝에서 닫지 않는다**(`rules/test.md` 4절). 앵커는 오늘 넷 다
참이고 구멍은 「앞으로 넓히는 편집이 조용히 산다」는 잠복이며, 계획서 5절이
**미리 「있으면 digest 후보로 남긴다」로 선언한 범위 밖**이다.
**여는 조건은 「그 정규식 넷 중 하나를 손대는 날」** — 계획 61 → 62 의 계승과 같다.

## 검증

전수 **맨몸** `Ran 620 tests in 15.889s` · `OK` · **rc 0**.
범위 무접촉 — `git diff --stat d763317 HEAD -- src/ e2e/ docs/specs/ data/` **빈손** ·
`data/crawl.db` sha256 `85c96744…5bda18` 무변.

## 다음

**리뷰 1/1.** 볼 것은 계획 62 의 diff(`tests/test_docs.py` · `README.md`) 하나다 —
`NOT_CAUGHT` 여섯 줄이 판정을 바꾸지 않는지(계획서 7절의 위험), `DOC_HEAD` 를
상수로 올린 것이 `DocHeadTest` 의 실물 판정을 약화시키지 않았는지를 본다.

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60·61·62 의 커밋이 `loop/passage-cost-band` 에
  쌓여 있고 `origin/main`(`d1fe3e9`) 무접촉 · PR 0(만들지도 조회하지도 않았다).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 = 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- `docs/digest.md` 는 200줄 정각이라, 후보 한 줄을 더하면서 `rules/docs.md` 3절대로
  **가장 오래된 완료 항목**(계획 55 `db-state-invariant`)을 지워 200줄을 지켰다 —
  원본은 `plan_history_041.md` 와 `## 완료` 첫 줄의 아카이브 명부에 그대로 있다.
- 회전은 없다 — `history_current.md` 는 **228줄**(상한 300), 다음 회전 번호는
  `history_064.md` 다.
