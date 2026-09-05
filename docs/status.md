---
signal: GREEN
phase: 리뷰
step: 1/1
attempt: 0
iteration: 353
updated: 2026-09-06
ctx: 58
night_iterations: 170
night_red: 2
night_retries: 1
plan: index-step-sync 계획 60 (테스트 1/1 완료 — 판정을 `step_gap` 으로 빼 갈래를 다 밟았다 · 다음은 리뷰 phase)
---

## 현재 상태

**테스트 phase 를 돌았다 — 어제 세운 가드가 자기를 못 재고 있었다.** 갭 탐색(`rules/test.md`
3절)이 8점짜리 하나를 찾아 그 자리에서 닫았다. 판정을 `step_gap(status_text, index_text)`
순수 함수로 빼고 갈래를 합성 문자열로 밟는 `StepGapTest` 5건을 세웠다
(609 → **614건 OK · rc 0**). 제품 `src/` 는 **0줄**, 새 파일 0개다.

## 찾은 갭 — 8점, 이번 스텝에서 닫았다

**`StepSyncTest` 의 몸통 전체가 아무에게도 안 재어지고 있었다.** 실물 문서가 오늘
서로 맞아 있어서(초록 데이터) 판정을 어떻게 비틀어도 전수가 초록이다 — 변이 6종
**6/6 생존**(전수 609건 · 죽은 단언 0):
① null 갈래 기대값 `0/0` → `9/9` · ② null 갈래 통째 삭제 · ③ 대조를 자기비교로
(`r.group(1)` → `s.group(1)`) · ④ 「index 에 행이 없다」 가드 삭제 ·
⑤·⑥ 「status 에 `step:`/`plan:` 줄이 없다」 가드 삭제.
`StepPatternTest` 가 재던 것은 **정규식 셋**이지 그 위의 판정이 아니었다.
설계서가 적은 「조용히 지나가는 갈래는 0개다」를 **아무도 재지 않았다.**

`CitationPatternTest`·`ArchiveMatchTest` 독스트링이 같은 자리에서 이미 적어 둔
「린트형 데이터가 초록일 때 검사는 자신을 못 잰다」의 세 번째 사례다.

## 무엇을 했나 — 기존 관용구를 그대로 썼다

`done_section`·`indexed` 가 `ArchiveMatchTest` 를 위해 나온 것과 **같은 모양**이다:
판정을 순수 함수로 빼고 실물은 `StepSyncTest` 가, 갈래는 `StepGapTest` 가 부른다.
단언은 한 줄도 안 낮췄다(`rules/test.md` 6절) — `StepSyncTest` 는 같은 두 문서를 읽어
같은 것을 요구하고, 실패 메시지는 `assertIsNone(gap, gap)` 으로 그대로 나온다.

**고친 뒤 같은 변이 6종을 다시 먹였다 — 6/6 사망**, 각각 의도한 단언이 죽였다
(①② `test_null_plan_requires_the_zero_step` · ③ `test_step_mismatch_is_reported` ·
④ `test_missing_index_row_is_reported` · ⑤⑥ `test_missing_status_lines_are_reported`).
**하네스에 이빨이 있는지도 양성 대조로 봤다** — `STEP_ROW` 에서 슬러그를 빼면 7건이 죽는다.

## 남긴 것 — 6점, digest 로

**`IterationSyncTest` 도 같은 구멍이다**(축만 다르다). 비교를 자기비교로 비트는 변이가
전수 614건에서 **생존**한다(실측). 갈래가 하나뿐이라 썩을 표면이 스텝 축의 1/4 이고,
오늘 손대는 것은 직교 편집이라 `digest ## 다음 계획 후보 (테스트 phase 갭)` 에 `[6]` 으로
남겼다. 여는 조건은 「반복 축 검사를 손대는 날」이고 답은 `iter_gap` 세 줄이다.

## 다음

**리뷰 phase.** 볼 것은 ① 판정을 함수로 빼면서 계약이 조용히 바뀐 곳이 없나
(특히 `s`/`p` 검사 순서 — 옛 코드는 둘 다 본 뒤에 실패했고 새 코드는 `step:` 을 먼저 문다)
② `StepGapTest` 의 합성 `INDEX` 가 실물 표 모양과 어긋나지 않았나
③ 이번 반복이 `digest.md` 에서 지운 완료 항목(계획 52)이 정말 다른 곳에 남아 있나.

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main` 무접촉 · PR 0(만들지도 조회하지도 않았다). 착수 시 원격 브랜치는
  `49bd4e2` 로 HEAD 와 같았다.
- **러너 규율 위반 0회 — 누적 38 유지.** 전수는 맨몸으로 돌리고 판정 줄과 `rc` 를 눈으로
  봤다(`Ran 614 tests · OK · rc 0`). 변이 하네스의 출력도 파이프 없이 읽었다.
- 문서 한도 — `history_current.md` **293/300**(다음 반복이 회전한다) · `digest.md` 200/200.
  **`digest.md` 는 여유가 0줄이라** 새 후보 한 줄을 넣으며 가장 오래된 완료 항목
  (계획 52 `focus-ring-combinator`)을 지웠다 — 내용은 `index.md` 52번 행과
  `plan_history_038.md`·`design_history_038.md` 에 그대로 있고 명부는 안 건드렸다.
- 변이는 계속 **메모리에서** 걸고(소스를 문자열로 치환해 로드된 모듈에 다시 exec)
  `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다 — 저장소 파일과 `data/crawl.db` 무접촉.
