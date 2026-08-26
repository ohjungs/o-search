---
signal: GREEN
mode: night
plan: crawl-throughput
phase: 설계
step: 0/3
attempt: 0
iteration: 64
night_iterations: 1
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-27 (반복 64)
ctx: 82% / 200k
rules: rules/design.md
---

# 현재 상태

**`crawl-throughput`(008) 계획 완료.** 브랜치 `loop/crawl-throughput`.
계획서 `docs/plan_crawl-throughput.md`. **다음은 설계 phase.**

## 문제 (사용자 실측)

크롤 처리량 **초당 0.5문서**. `concept.md:44` 기준은 **초당 5문서** — 10배 차이.
원인은 `src/websearch/crawl.py:26-51` 이 한 번에 한 페이지씩 순차로 받아
**네트워크 대기가 곧 총 소요시간**이라는 것. 같은 실측에서 1,700문서쯤
`store.upsert` 가 `sqlite3.OperationalError: database is locked` 로 크롤을 죽였다
(`indexer` 가 같은 DB 를 읽는 중).

## 스텝 (3개)

| # | 무엇 | 의존 | 건드릴 파일 |
|---|---|---|---|
| 1 | 처리량 e2e 하니스 `e2e/perf_crawl.py` — 지금 코드로 **RED** 를 본다 | 없음 | e2e 신규 1 |
| 2 | 크롤 루프 동시 fetch (스레드풀) | 1 | crawl·frontier + 테스트 2 |
| 3 | `store` 가 잠긴 DB 에 안 죽는다 | 없음 | store + 테스트 1 |

임계경로 1 → 2. 스텝 3은 독립이라 순서 자유(야간이라 순차로 돈다).

## 다음 스텝 — 설계

**설계 트리거 3개에 걸렸다** (`rules/design.md` 1절): 공개 인터페이스 변경
(`crawl.crawl()`·`Frontier.next()`) · 3개 이상 파일 · 대안이 갈림.
산출물 `docs/design_crawl-throughput.md` 가 답할 것:
① 동시성 수단 ② 프런티어·저장소 동시 접근 안전 ③ 워커 하나가 죽어도
크롤 전체가 안 죽는 실패 격리 ④ 되돌리기 수단.

**깨뜨릴 가정 하나**(`design.md` 3-2절): 동시성이 politeness 를 먹지 않는가 —
`Frontier.next()` 는 팝 시점에 `_last_fetch` 를 찍는데, 응답이 1초보다 오래 걸리면
**같은 도메인이 in-flight 인 채로 다시 팝될 수 있다.** 이게 참이면
"도메인당 in-flight 1개" 를 설계가 명시해야 한다.

- 이미 한 것: 계획서만. **소스 0줄** — 코드는 아직 아무것도 안 건드렸다

## 보류 (그대로)

- `recrawl` 정책 (`concept.md:31`) · `search-ui`(경량·디자인 축 측정 명령이 아직 `없음`)
- digest `[7]` `robots.allowed()` 비ASCII 예외 누수 — 이 계획 범위 밖
