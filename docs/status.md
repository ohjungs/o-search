---
signal: GREEN
mode: night
plan: crawl-politeness
phase: 설계
step: 1/6
attempt: 0
iteration: 90
night_iterations: 1
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 90 · 계획 phase 완료)
ctx: 52% / 200k
rules: 1411a37
---

# 현재 상태

**계획 013 `crawl-politeness` 를 열었다.** `docs/digest.md ## 판단 필요` 의 `[high]` 2건을
한 계획으로 묶었다 — 뿌리(예의 계약이 워커 경계를 못 넘는다)와 파일
(`src/websearch/crawl.py` 의 `_fetch_one`·`_store_result`)이 겹친다.

| 구멍 | 실측 | 목표 |
|---|---|---|
| A `Crawl-delay: 5` 도메인의 첫 요청이 예외 → 다음 간격 | **1.0초** (대조군 5.0) | ≥ 5.0초 |
| B 연결 거부 도메인 1 URL → TCP 연결 3회 간격 | **0.0002초** | 각각 ≥ 1.0초 |

계획 `docs/plan_crawl-politeness.md`. 브랜치 `loop/crawl-politeness` (기점 `cdbd842`).

**설계로 넘긴다** — 3개 파일 · 공개 인터페이스 변경 · 대안이 갈린다 · 동시화 계약 4
(메인 스레드는 네트워크를 안 한다)를 건드린다. 다음 반복이 `docs/design_crawl-politeness.md`
를 쓴다. 어떤 대안을 고르든 **선언된 간격보다 빠르게 때리지 않는다. 모르면 느린 쪽.
성능과 부딪히면 성능을 깎는다** (`docs/specs/concept.md` 갈림길 1순위 = 크롤 윤리).

## 다음 계획 (이번 계획이 DONE 되면)

`pagination-ui` — 검색 UI 에 페이지 이동을 붙인다. JSON API 는 이미 `page=` 를 받는다.
`e2e/design_check.py` 기준(JS 0B · 대비 4.5:1 · 360px)을 그대로 통과해야 한다.

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
