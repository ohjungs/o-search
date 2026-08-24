---
signal: GREEN
mode: night
plan: null
phase: 계획
step: 0/0
attempt: 0
iteration: 37
night_iterations: 6
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 37)
ctx: 82% / 200k
rules: null
---

# 현재 상태

**`search-api` DONE.** 5스텝 + 테스트·리뷰 관문 전부 통과. 124/124, e2e 4개 통과.
아카이브 완료 — `plan_history_004.md` · `design_history_004.md`.

## 다음 계획 — 이어받는 세션이 착수할 것

- **`crawl-delay` 존중** (계획 phase 부터)
- 근거: `docs/digest.md` 의 `[높음·설계 범위 밖 메모] robots crawl-delay 존중`.
  `docs/specs/concept.md` 갈림길 우선순위 1순위가 크롤 윤리다. robots.txt 의
  `Crawl-delay` 를 읽어 도메인 간격에 반영하는 **순수 로직**이라 스키마 변경 없이
  무인으로 닫을 수 있다 (사용자가 이미 정한 순서)
- 착수 안 함: `recrawl`(증분 색인이 갱신을 반영 안 함 — 스키마 변경이라 무인 보류),
  `X-Robots-Tag`(스키마 expand)
- 브랜치: `loop/crawl-delay` 를 새로 딴다. **`loop/search-api` 는 머지 안 된 상태다**

## `search-api` 가 남긴 것

- `GET /search?q=&page=` — JSON, 10건 단위, `has_next`, 검증은 `serve._parse()` 한 곳
- `indexer.search(..., offset=0)`, `ORDER BY bm25(docs), rowid` (동점 고정, 비용 0)
- **성능 축이 열렸다**: `e2e/perf_search.py` / 기준선 p95 6.71ms(3000문서) → `project.md`
- e2e 4번째 `e2e/search_api_e2e.py` (CLI 기동 경로)

## 정지 조건

이번 세션 반복 6건(32~37) 전부 GREEN. RED 0 · 재시도 0 · 보류 0 · 패치 0.
계획 하나를 열어둔 채 끝내지 않고 DONE 까지 닫았다.
