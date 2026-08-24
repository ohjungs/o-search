---
signal: GREEN
mode: night
plan: crawl-delay
phase: 개발
step: 1/4
attempt: 0
iteration: 39
night_iterations: 8
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 39)
ctx: 82% / 200k
rules: null
---

# 현재 상태

**`crawl-delay` 설계 완료** → `docs/design_crawl-delay.md`.
다음 반복은 **개발 스텝 1/4** — `RobotsCache.delay(url)` 이다 (`docs/plan_crawl-delay.md` 스텝 1).
TDD: 실패하는 테스트를 `tests/test_robots.py` 에 먼저 쓴다.

## 설계가 정한 것 (개발이 지킬 계약)

- `RobotsCache.delay(url) -> float | None` — `None` 은 "지시 없음". robots 적재는 `allowed()` 와 같은 캐시 1회
- **stdlib 이 소수를 버린다**(`Crawl-delay: 3.5` → `None`, 실측). `crawl_delay()` 가 `None` 일 때만
  robots 본문에서 `crawl-delay:` 실수 값을 긁어 **가장 큰 값**을 쓴다 (느린 쪽으로만 틀린다)
- `Frontier.set_delay(domain, seconds)` — 내부 간격 `max(DOMAIN_INTERVAL, seconds or 0)`,
  **`MAX_DELAY = 30.0` 초과는 그 도메인을 버린다**(큐를 비우고 이후 `add()` 도 거부)
- 배선은 **크롤 루프가 밀어넣는다** — `robots.allowed(url)` 직후 `set_delay`

## 탐침이 알려준 것 (스텝 2 가 건드릴 정확한 지점)

`Frontier.next()` 와 `Frontier.seconds_until_ready()` 가 모듈 상수 `DOMAIN_INTERVAL` 을
**직접 읽는다** — 메서드만 추가하면 안 먹는다. 두 곳을 도메인별 조회로 바꿔야 한다.

## 진행 중인 스텝

없음 — 계획·설계만 끝났다. 소스는 한 줄도 안 건드렸다.
브랜치 `loop/crawl-delay` (`loop/search-api` 4f92e32 에서 갈라짐).

## 직전 계획

`search-api` **DONE** (반복 32~37). 124/124, e2e 4개. 아카이브 004.
**4개 계획 브랜치 전부 머지 안 됐다.**

## 정지 조건

이번 세션 반복 8건(32~39) 전부 GREEN. RED 0 · 재시도 0 · 보류 0 · 패치 0.
