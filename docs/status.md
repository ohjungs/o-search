---
signal: DONE
mode: night
plan: null
phase: 계획
step: 4/4
attempt: 0
iteration: 21
night_iterations: 19
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 21)
ctx: 84% / 200k (정지 시점)
rules: null
---

# 현재 상태

**indexer 계획 DONE — e2e 통과, 아카이브 002 완료.** 이어서 컨텍스트 상한으로 정상 종료.
crawler-core(001) 에 이어 두 번째 계획이 닫혔다. 전체 71/71 통과, 야간 RED 0·재시도 0.

이제 크롤 DB 한 개로 `python3 -m websearch.indexer <db>` 색인 → `--query` 검색이
끝까지 동작한다. 한국어 2글자 질의와 영어 질의 모두 실측 확인.

## 진행 중인 스텝 — 이어받는 세션이 읽을 것

- 할 일: **다음 계획 착수 — `search-api`** (`docs/index.md` 사양 분할 3번).
  질의 → 랭킹 결과 API. 컨셉 성능 1(p95 300ms)의 측정이 여기서 시작된다
- 근거: `docs/index.md` 의존 순서상 indexer 다음이 search-api. `indexer.search()` 가
  이미 (url, title, snippet) bm25 순으로 돌려주므로 HTTP 껍데기 + 측정이 핵심이다
- 완료 기준: 계획 phase 이므로 `rules/plan.md` 로 `docs/plan_search-api.md` 를 쓴다.
  중복 확인은 `docs/index.md` + `docs/digest.md`
- 이미 한 것: 없음 (착수 전)

### 계획을 쓸 때 반드시 반영할 것 (digest 에 근거 있음)

- `search()` 의 질의 재작성은 신뢰 경계다. HTTP 파라미터가 붙는 순간 NUL·제어문자
  경로가 실제로 도달 가능해진다 — 이미 막아뒀지만 API 계층에서 다시 확인
- digest "판단 필요" 의 [8] 증분이 재크롤 갱신 미반영 — recrawl 계획 소관이나
  API 가 옛 본문을 서빙하게 되므로 순서를 앞당길지 판단
- digest "다음 계획 후보" 의 [85] meta noindex 무시 — 공개 API 로 노출되면 윤리 축
  위반이 밖에서 보인다. crawl-delay 건과 묶어 별도 계획으로 올릴 것

## 다음 행동

`/loop-harness night` 또는 `/loop-harness` 를 다시 부르면 이어진다.
DONE 처리는 끝났으므로 다음 세션은 계획 phase 부터 시작한다.

## 정지 사유

컨텍스트 상한 (야간 반복 19회 수행, 이번 세션 6회).
