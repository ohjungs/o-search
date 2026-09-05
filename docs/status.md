---
signal: GREEN
phase: 테스트
step: 1/1
attempt: 0
iteration: 352
updated: 2026-09-06
ctx: 62
night_iterations: 169
night_red: 2
night_retries: 1
plan: index-step-sync 계획 60 (개발 1/1 완료 — 스텝 축 가드 · 다음은 테스트 phase)
---

## 현재 상태

**개발 phase 를 돌았다 — 스텝 축 가드가 섰다.** `tests/test_docs.py` 에
`StepSyncTest`·`StepPatternTest` 를 `IterationSyncTest`·`IterationPatternTest` 옆자리로
더했다(+4건 · **609건 OK · rc 0**). 제품 `src/` 는 **0줄**, 새 파일 0개다.
`digest ## 반복 실패` 의 4회 등재 항목이 남긴 「남은 후보는 검사 한 줄」을 채운 것이다.

## 무엇이 섰나 — 안 D 그대로

`status.md` 의 `plan:` 슬러그로 `index.md` 의 `| plan_<슬러그> |` 행을 집어 스텝 칸을
`step: N/M` 과 대조한다. 상태 칸(`진행`/`완료`)은 안 본다. `plan: null` 이면 대조 대신
`step: 0/0` 을 요구한다. 상수 셋(`STEP_LINE`·`PLAN_SLUG`·`STEP_ROW`)은 `ITER_ROW` 옆에
두고, 행 이름 뒤 ` | ` 를 요구해 **접두 일치를 막는다**(`plan_index-step-sync-2` 차단).

## TDD — 실패를 눈으로 봤다 (`dev.md` 0절)

검사를 먼저 쓰고 **양방향으로 비틀어** 둘 다 빨간 것을 봤다 — ① `index.md` 만 `1/1` 로
(`'1/1' != '0/1'`) ② 되돌리고 `status.md` 만 `1/1` 로(`'0/1' != '1/1'`). **한쪽만 재는
검사가 아니다.** 되돌리면 초록이었다.

**변이 5종 전멸**(`mock.patch.object` · 메모리 · 저장소 파일 무변):
M1 슬러그를 안 본다 → 3죽음 · M2 접두 일치로 넓힌다 → 1 · M3 `PLAN_SLUG` 이 줄 전체를
읽는다 → 2 · M4 `STEP_LINE` 이 `N/M` 을 안 요구한다 → 1 · **M5 상태 칸을 `진행` 으로
좁힌다 → 1**. M5 가 죽는 것이 안 D 와 안 A·B 를 가르는 자리다 — 합성 표의 대상 행은
상태가 `완료` 다.

## 이 계획이 자기 첫 시험대였다

착수 시점 관례가 갈려 있었다 — 계획 57·58 의 개발 커밋은 `status.step` 을 `1/1` 로 올리고
`index` 를 `0/1` 에 두어(=어긋남 11건의 정체) 계획 59 는 `0/1` 로 되돌렸다. **이 커밋은
둘을 함께 `1/1` 로 올린다** — 새 검사가 요구하는 방향이고, 그것이 원하는 동작이다.

## 다음

**테스트 phase.** 새 가드 둘의 갭을 `rules/test.md` 로 훑는다. 이미 아는 천장 둘 —
① 상태 칸 자신의 정합성(`진행` 을 `완료` 로 안 바꾼 행)은 안 D 가 못 본다
② 검사는 작업 트리 HEAD 만 본다(옛 구간에 먹이면 대량으로 빨개진다).
둘 다 설계서 「범위 밖」에 적혀 있다.

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main` 무접촉 · PR 0(만들지도 조회하지도 않았다). 착수 시 원격 브랜치는
  `6c8c598` 로 HEAD 와 같았다.
- **러너에 파이프를 붙였다 — 누적 38.** 전수를 `| tail -4` 로 잘라 `rc` 가 파이프의 0 으로
  가려졌다(README 건수 실패가 `FAILED` 인데 `rc=0`). **맨몸으로 다시 돌려** 판정 줄과
  `rc` 를 눈으로 봤다: `Ran 609 tests · OK · rc 0`.
- 문서 한도 — `history_current.md` 247/300 · `digest.md` 200/200.
  **`digest.md` 는 여유가 0줄이다.**
- 변이는 계속 **메모리에서**(`mock.patch.object`) 걸고 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를
  함께 준다 — 저장소 파일과 `data/crawl.db` 는 안 건드린다.
