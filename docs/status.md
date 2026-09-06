---
signal: GREEN
phase: 리뷰
step: 1/1
attempt: 0
iteration: 358
updated: 2026-09-06
ctx: 52
night_iterations: 175
night_red: 2
night_retries: 4
plan: iter-gap-cover 계획 61 (테스트 1/1 완료 — 갭 둘을 digest 로 넘겼다 · 다음은 리뷰 phase)
---

## 현재 상태

**계획 61 테스트 1/1 을 끝냈다.** 저장소 파일은 **한 줄도 안 고쳤다** — 이 반복이 한
일은 전수와 변이 재측, 그리고 문서 마감뿐이다(`src/`·`tests/`·`e2e/`·`README.md`·
`docs/specs/`·`data/crawl.db` diff 빈손). 전수 `Ran 618 tests` · `OK` · rc 0 ·
대조군 죽은 단언 **0**.

## 변이 재측 — M1~M5 사망, M6·M7 생존

| 변이 | 죽은 단언 | 판정 |
|---|---|---|
| 대조군 | 0 | 기준선 618 OK |
| M1 대조를 자기비교로 | 1 `test_iteration_mismatch_is_reported` | 의도한 하나만 |
| M2 `metrics` 가드 삭제 | 1 `test_missing_metrics_row_is_reported` | 의도한 하나만 |
| M3 `status` 가드 삭제 | 1 `test_missing_status_line_is_reported` | 의도한 하나만 |
| M4 판정 통째 삭제(양성 대조) | 3 | 계획서 기준 「셋 이상」 충족 |
| M5 `ITER_ROW` 넓힘 | 2 (`IterGapTest`+`IterationPatternTest`) | 죽는다 |
| M6 `ITER_LINE` 의 `^`·`$` 제거 | **0** | **갭** |
| M7 `DocHeadTest` 판정 넓힘 | **0** (두 번 재서 둘 다) | **갭** |

## 갭 둘 — 고치지 않고 넘겼다

둘 다 「판정이 실물 문서 위에서만 돈다」의 형제다. ① `night_iterations` 를 막는 것은
앵커가 아니라 **복수형 `s`** 였다 — 앵커가 진짜 막는 자리(줄 중간·꼬리 붙은
`iteration:`)를 밟는 단언이 0개다. ② `DocHeadTest` 는 실물 세 문서가 늘 H1 이라
판정을 `^` 로 넓혀도 아무도 안 죽는다. **8점 미만이라 이번 스텝에서 안 고치고**
(`rules/test.md` 3절) `digest` 의 테스트 phase 갭 절에 `[6]` 으로 남겼다.

## 다음

**리뷰 1/1.** 완료 기준 1~5 는 개발이 실측으로 닫았고, 6(`status`↔`index` 스텝 축)은
`index.md` 61번 행이 이미 `1/1` 이라 `StepSyncTest` 가 전수 안에서 초록으로 확인한다.

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60·61 의 커밋이 `loop/passage-cost-band` 에 쌓여
  있고 `origin/main` 무접촉 · PR 0(만들지도 조회하지도 않았다).
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- 변이는 **저장소 밖에서** 건다 — 스크래치패드 하네스가 `mock.patch` 로 갈아 끼웠고
  저장소 파일은 무접촉이다.
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- **앞 시도 둘이 600초 무진전으로 죽어 이 반복은 시도2 다.** 죽은 시도가 남긴 것은
  회전 diff 뿐이었고, 이 반복이 측정을 다시 재고 기록을 마감했다.
- 회전을 마쳤다 — `history_current.md` 는 80줄, 다음 회전 번호는 `history_064.md` 다.
