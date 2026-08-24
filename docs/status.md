---
signal: GREEN
mode: night
plan: crawl-delay
phase: 개발
step: 2/4
attempt: 0
iteration: 40
night_iterations: 9
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 40)
ctx: 82% / 200k
rules: null
---

# 현재 상태

**`crawl-delay` 개발 1/4 완료** — `RobotsCache.delay(url)` 이 산다. 130/130 통과.
다음 반복은 **개발 2/4** — `Frontier` 가 도메인별 간격을 갖는다
(`docs/plan_crawl-delay.md` 스텝 2, 계약은 `docs/design_crawl-delay.md`).

## 다음 스텝이 알아야 할 것

- **탐침으로 확인한 지점**: `Frontier.next()` 와 `Frontier.seconds_until_ready()` 가
  모듈 상수 `DOMAIN_INTERVAL` 을 **직접 읽는다**. `set_delay()` 만 추가하면 안 먹는다 —
  두 곳을 도메인별 조회로 바꿔야 한다 (`src/websearch/frontier.py:28`, `:47` 부근)
- 계약: `set_delay(domain, seconds|None)` → 내부 간격 `max(DOMAIN_INTERVAL, seconds or 0)`,
  **`MAX_DELAY = 30.0` 초과면 그 도메인 큐를 비우고 이후 `add()` 도 거부**
- `Frontier(now=...)` 시계 주입이 이미 있다 — 새 테스트도 실제로 잠들지 않는다
- 스텝 1 이 남긴 것: `RobotsCache.delay(url) -> float | None`,
  소수는 stdlib 이 버려서 `robots.py:_DELAY_LINE` 로 본문에서 직접 긁는다(가장 느린 값)

## 이번 스텝에서 배운 것 (다음 변이 검사 전에 읽을 것)

`max`↔`min` 처럼 **같은 길이**로 변이시켰다 되돌리면 파일 크기·mtime(초)이 그대로라
`__pycache__` 가 옛 .pyc 를 계속 쓴다 — 되돌린 뒤에도 실패가 남아 있는 것처럼 보인다.
`docs/project.md` 명령 절에 `PYTHONDONTWRITEBYTECODE=1` 로 적어 뒀다.

## 정지 조건

이번 세션 반복 9건(32~40) 전부 GREEN. RED 0 · 재시도 0 · 보류 0 · 패치 0.
브랜치 `loop/crawl-delay`. **4개 계획 브랜치는 여전히 머지 안 됐다.**
