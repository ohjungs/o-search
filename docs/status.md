---
signal: GREEN
phase: e2e
step: 1/1
attempt: 0
iteration: 396
updated: 2026-09-06
ctx: 46
night_iterations: 192
night_red: 2
night_retries: 4
plan: spec-citation-anchor — 계획 68 (리뷰 phase 스텝 1/1 완료 · 다음은 e2e phase)
---

## 현재 상태

**계획 68 `spec-citation-anchor` 리뷰 1/1 을 GREEN 으로 닫았다 — 백지 패스와 대조
패스 둘 다 막는 것 0건이다.** 전수 **`Ran 628` · `OK` · rc 0** · 브랜치
`loop/passage-cost-band` · 이번 스텝 코드 **0줄**.

## 이번 스텝이 판정한 것

**리뷰가 본 diff** — 브랜치 전체(`274c0eb`·`112b69d`·`880253b`). 실질은
`tests/test_docs.py` `SpecCitationTest`(새 단언 `test_every_citation_carries_an_anchor`
와 `_anchors(line, pos)` 헬퍼) · 여섯 소스 파일의 인용 12자리 정정 · `README.md`
건수 1줄이고 나머지는 문서다. `src/` 0줄 · `docs/specs/` 무변 · `data/crawl.db` 무변 ·
새 의존성 0 · 재색인 0 · 스키마 0 · PR #7 무접촉.

**핵심 판정 — `_anchors` 공유가 옳다.** 대조 축은 「옮겨 적은 것이 **있는** 인용」만
재고, 의무 축은 「**모든** 인용이 뭔가 갖는가」를 잰다. 축은 다르지만 **추출기가 하나**라
추출기가 죽으면 의무 축이 먼저 운다 — 정적으로 확인했다: `PHRASE` 가 죽으면 문구 전용
**12자리**, `CONST`/`NUM` 이 죽으면 값 전용 **4자리**가 앵커 0 이 되어 새 단언이 문다.
갈라 놓았으면 의무 축이 자기 추출기로 "앵커 있음" 을 선언하는 동안 대조 축이 조용히
0건이 되는 구멍이 열린다. 수집 자체가 0건이 되는 거짓 초록은 `_citations` 안의
`MIN_HITS 14` 가 이미 막고 있다(가드가 **공유 수집기 안**에 있는 것이 맞다).

**실측(정적 계산, 변이 0판)** — 인용 **18건 전부 앵커를 갖는다**(앵커 없음 0).
대조 건수는 **19**(문구 14 · 값 5)로 계획 전 7 에서 올랐다.

## 남긴 것 (전부 정보성 · 막지 않음)

- **`MIN_CHECKS 6` 은 이제 사실상 잉여다.** 실측 19 대비 하한이 6 이라 13건이 조용히
  사라져도 안 운다. 다만 「전부 사라짐」은 새 의무 단언이 먼저 물고, 손으로 관리할 값을
  늘리지 않으려고 계획 5절이 **명시적으로 올리지 않기로** 정했다. 지금 손대면 직교
  편집이라 **안 고쳤다** — 없앨지/올릴지는 다음 계획 몫이다.
- **밀림 생존 넷은 범위 인용의 구조적 성질이다.** 재실측 결과 생존은
  `test_serve.py:914`·`design_check.py:2`·`design_check.py:444`(전부 `50-54`, `-1`·`-2`)와
  `quality_eval.py:3`(`22-23`, `-1`) — **정확히 범위 인용 넷**이고 나머지 14 는 ±1·±2 에서
  전부 죽는다. 처방은 `digest.md` 「다음 계획 후보」 `[5]` 에 이미 있다.
- **공백 한 칸짜리 문구(`" "`)** 는 `PHRASE` 와 `assertIn` 을 둘 다 통과한다. 실물 0건이고
  막으려면 최소 길이를 손으로 관리해야 해서 적어만 둔다.
- `design_check.py:444` 의 `print` 라벨이 큰따옴표를 갖게 됐지만 그 문자열을 긁는 파서는
  없다(참조처는 `docs/project.md`·`docs/e2e/search-ui/result.md` 산문뿐).

## 검증

전수 **`Ran 628 tests` · `OK` · rc 0**(맨몸 1회) · `README.md:104` 의 `628` 과 일치 ·
`metrics.md` 「반복 396」 = 이 파일 `iteration: 396`(`IterationSyncTest`) ·
`history_current.md` 144줄(상한 300, 회전 불필요).

## 다음

**e2e phase.** 이번 계획의 코드 diff 는 테스트와 주석 문자열뿐이라 e2e 의 몫은
회귀 확인이다 — `design_check.py`·`perf_crawl.py`·`quality_eval.py` 의 바뀐 문자열이
실행 경로에서 그대로 도는지 본다.
