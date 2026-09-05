---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
iteration: 351
updated: 2026-09-06
ctx: 55
night_iterations: 168
night_red: 2
night_retries: 1
plan: index-step-sync 계획 60 (설계 완료 — 안 D 채택 · 다음은 개발 1/1)
---

## 현재 상태

**설계 phase 를 돌았다 — 계획 60 의 검사가 `index.md` 의 어느 행을 집을지가 정해졌다.**
산출물은 `docs/design_index-step-sync.md` 하나이고, 제품 `src/`·`tests/` 는 **0줄** 만졌다.
이 반복이 먼저 처리한 것은 문서 한도 두 건이다(아래 「한도 처리」).

## 설계 결정 — 안 D (슬러그로 집는다)

`status.md` 의 **`plan:` 슬러그**로 `index.md` 의 `| plan_<슬러그> |` 행을 집어 그 행의
스텝 칸을 `step: N/M` 과 대조한다. 상태 칸(`진행`/`완료`)은 안 본다. `plan: null` 이면
대조 대신 **`step: 0/0`** 을 요구한다 — **조용히 지나가는 갈래가 0개**다.

**눈금(최근 30커밋 · 진짜 어긋남 11건) 실측** — A(진행 행 정확히 1개) 11잡음/**오탐 3** ·
B(있을 때만 대조) 11잡음/**조용한 통과 3** · C(`git log`) 계획서 2절이 이미 약화 판정 ·
**D 12잡음 / 오탐 0 / 조용한 통과 0**. D 가 하나 더 잡는 `9c6f763` 은 오탐이 아니라
**진짜 결함**이다 — `status` 가 계획 57 을 열어 놓았는데 `index.md` 에 그 행이 아예 없었다.
슬러그로 집으면 A·B 가 씨름하던 **「진행 행 0개」라는 상태 자체가 사라진다.**

**가정을 깨봤다**(`design.md` 3-2절) — 「`plan:` 첫 토큰 == `index` 행 이름」은 오늘 형식을
쓰는 **최근 344커밋에서 342건 중 341건 참**이고, 유일한 예외가 위의 `9c6f763` 이다.
슬러그가 없던 2건은 둘 다 `plan: null`+`step: 0/0`(하네스 템플릿의 초기 상태)이라 계약의
`null` 갈래가 덮는다. **계획서 3절과 완료 기준 4 의 문구도 이 결정에 맞춰 고쳤다.**

## 한도 처리 (append 전에 끝냈다)

- **회전**: `history_current.md` 299줄 → 계획 58 `passage-cost-band` 의 여섯 반복
  (339~344 · 113줄)을 **`docs/history_061.md`** 로 옮기고 `digest.md` 「아카이브 명부」에
  등재했다(`ArchiveIndexTest` 초록). 남은 `history_current.md` 는 186줄.
- **압축**: `digest.md` 202줄 → 가장 오래된 완료 항목 둘(계획 50 `runner-quiet` ·
  계획 51 `hidden-passage`)을 지워 **정확히 200줄**. 원본은 `plan_history_036/037.md` 와
  `index.md` 에 그대로 있다.

## 다음

**개발 1/1.** `tests/test_docs.py` 에 `StepSyncTest`·`StepPatternTest` 를 세운다 — 계약은
설계서 「계약」 절이 정본이다(상수 셋을 `ITER_ROW`·`ITER_LINE` 옆에 · 매치가 `None` 이면
비교 전에 실패 · 행 이름은 **정확히** 일치 · 합성 표에 접두가 같은 더 긴 슬러그 행을 둔다).
TDD 순서는 계획서 3절 그대로다. **이 계획 자신이 첫 시험대다** — 개발 커밋에서 `index.md`
계획 60 행을 `1/1` 로 함께 올리지 않으면 새 검사가 그 커밋에서 죽는다(그것이 원하는 동작).

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main` 무접촉 · PR 0(만들지도 조회하지도 않았다).
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 0회(누적 37 유지).
- 문서 한도는 이번 반복이 둘 다 내렸다 — `history_current.md` 186/300 · `digest.md` 200/200.
  **`digest.md` 는 여유가 0줄이라** 다음에 완료 항목을 더하는 반복이 또 지워야 한다.
- 변이는 계속 **메모리에서**(`mock.patch.object`) 걸고 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를
  함께 준다 — 저장소 파일과 `data/crawl.db` 는 안 건드린다.
