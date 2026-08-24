---
signal: GREEN
mode: night
plan: quality-eval
phase: 설계
step: 0/4
attempt: 0
iteration: 47
night_iterations: 16
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 47)
ctx: 80% / 200k
rules: rules/design.md
---

# 현재 상태

**`quality-eval` 계획 작성 완료 → 설계 phase.**
`docs/plan_quality-eval.md` (스텝 4개), 브랜치 `loop/quality-eval` (`loop/crawl-delay` 6bb2785 에서 분기).
착수 전 기준선 146/146 통과 확인.

## 다음 스텝 — 설계 phase

`docs/design_quality-eval.md` 를 쓴다. **설계가 답해야 할 것은 셋이다** (계획서 `## 설계` 절):

1. **방해 문서(distractor) 설계** — 정답 문서만 질의어를 가지면 recall@10 은 자동 100% 가 되고
   측정이 거짓말한다. 같은 어휘를 공유하되 정답이 아닌 문서를 어떻게 넣을 것인가
2. **정답의 정의** — 질의당 정답 1건인가 집합인가. 포함률의 분모·분자가 여기서 갈린다
3. **fixture 위치·형식** — 코퍼스/질의 셋을 별도 데이터 파일로 둘 것인가 스크립트 안에 둘 것인가

설계 입력으로 이미 확인해 둔 사실은 계획서 `## 이미 참인 것` 절에 전부 있다
(`indexer.search` 는 limit 기본 10, `_fts_query` 가 어절마다 접두 `*`, `unicode61` 은 한국어를
공백 단위로만 자름, `e2e/perf_search.py:50` 이 크롤 없이 `pages` 를 직접 채우는 패턴).

- 이미 한 것: 계획서·브랜치·`index.md` 한 줄. 코드는 손대지 않았다

## 이번 반복에서 함께 한 문서 정리

`history_current.md` 가 37회/273줄로 상한(20회/300줄)을 넘어 **회전**했다 —
반복 1~37 을 `docs/history_001.md` 로 옮기고, `digest.md` 완료 절에 빠져 있던
`plan_crawler-core (001)` 한 줄을 채웠다. 현재 `history_current.md` 는 9회/76줄.

## 보류 (사람 승인 대기 — 무인 모드에서 착수 금지)

- `recrawl`(`concept.md:31` 30일 재방문) · `X-Robots-Tag` 헤더 — 둘 다 **스키마 변경**이다
- `robots.py:_fetch_robots` 의 `resp.read()` 무상한 — 자원 관련이라 무인 금지 (`digest.md`)
