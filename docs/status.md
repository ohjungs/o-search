---
signal: GREEN
mode: night
plan: crawl-delay
phase: 개발
step: 4/4
attempt: 0
iteration: 42
night_iterations: 11
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 42)
ctx: 82% / 200k
rules: null
---

# 현재 상태

**`crawl-delay` 개발 3/4 완료 — 배선 끝.** 138/138 통과.
`Crawl-delay: 5` 를 선언한 도메인은 크롤 루프에서 실제로 5초 간격으로 요청된다(가짜 시계로 확인).

다음은 **개발 4/4 — e2e** (`docs/plan_crawl-delay.md` 스텝 4):
`e2e/crawl_delay_e2e.py` 를 만들고 `docs/project.md` 명령 목록에 추가한다.

## 다음 스텝이 할 일

- 로컬 HTTP 서버가 `/robots.txt` 로 `User-agent: *` + `Crawl-delay: 2` 를 내고
  링크로 이어진 페이지 3~4개를 낸다. **서버가 요청 도착 시각을 기록**한다
- `crawl.crawl(...)` 을 **실제 시계로** 돌리고(짧게 — 2초 × 2~3회)
  같은 도메인 연속 요청 간격이 전부 2초 이상임을 단언한다.
  1초 하한만 지켜졌다면 실패해야 한다
- 기존 e2e 4개(`e2e/*.py`)와 같은 모양으로 쓴다 — `e2e/crawl_e2e.py` 가 로컬 서버 예시다

## 스텝 1~3 이 남긴 것

- `RobotsCache.delay(url) -> float | None` (소수는 `robots.py:_DELAY_LINE` 폴백)
- `Frontier.set_delay(domain, seconds|None)` — 하한 1초, `MAX_DELAY = 30.0` 초과는 도메인 폐기
- `crawl.crawl()` 이 `robots.allowed()` 직후 `frontier.set_delay(netloc, robots.delay(url))`.
  **첫 요청은 어떤 간격도 어기지 않는다** — 폐기 도메인도 첫 페이지 하나는 받고 거기서 멈춘다
- 변이 검사: 스텝 2 에서 4건, 스텝 3 에서 1건(배선 제거) 전부 잡힌다

## 함정 (이번 세션에서 밟았다)

1. **`git checkout <파일>` 로 변이를 되돌리지 마라** — 커밋 전이면 구현이 날아간다. 사본 `cp` 로 되돌린다
2. 같은 길이 변이(`max`↔`min`)는 `__pycache__` 가 옛 .pyc 를 재사용한다 → `PYTHONDONTWRITEBYTECODE=1`

## 정지 조건

이번 세션 반복 11건(32~42) 전부 GREEN. RED 0 · 재시도 0 · 보류 0 · 패치 0.
브랜치 `loop/crawl-delay`. **5개 계획 브랜치 전부 머지 안 됐다.**
